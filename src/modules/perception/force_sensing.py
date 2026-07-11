import os
import math
import random
import time
import json
import numpy as np
from typing import Dict, Any, Optional

from src.core.logging import logger

class KalmanFilter1D:
    """
    1D Kalman Filter for smoothing and tracking payload estimates.
    """
    def __init__(self, Q: float = 3.0, R: float = 250.0, initial_state: float = 0.0):
        self.Q = Q  # Process noise covariance (allows tracking changes)
        self.R = R  # Measurement noise covariance (suppresses sensor noise)
        self.x = initial_state  # Estimated state
        self.P = 10.0  # Estimation error covariance

    def update(self, z: float) -> float:
        # Predict
        self.P = self.P + self.Q
        
        # Update
        K = self.P / (self.P + self.R)
        self.x = self.x + K * (z - self.x)
        self.P = (1.0 - K) * self.P
        return self.x

class ForceSensing:
    """
    Perception plugin representing physical force-sensing/load cell inputs.
    Exposes force values for the plate balancing task.
    Also computes joint torques and end-effector payload weight estimations using
    Dynamixel currents and MuJoCo gravity compensation.
    """
    def __init__(self):
        self.load_cell_value = 0.0
        self.model = None
        self.data = None
        self.model_loaded = False
        
        # Weight state variables (raw and calibrated)
        self.raw_L = 0.0
        self.raw_R = 0.0
        self.weight_L = 0.0
        self.weight_R = 0.0
        
        # Calibration coefficients
        self.tare_L = 0.0
        self.tare_R = 0.0
        self.cal_factor_L = 1.0
        self.cal_factor_R = 1.0
        self.port = "COM11"
        self.connected = False
        self.loadcell_mode = 2
        self.loadcell_arm = "left"
        
        # Background serial reading thread
        import threading
        self.serial_thread = None
        self.running = False
        self.stop_event = threading.Event()
        
        # Velocity estimation state
        self.prev_positions = {}
        self.prev_time = time.time()
        
        # Kalman filter trackers for both end-effectors (initially 240g for mock consistency)
        self.left_kf = KalmanFilter1D(Q=3.0, R=250.0, initial_state=240.0)
        self.right_kf = KalmanFilter1D(Q=3.0, R=250.0, initial_state=240.0)
        
        # Load calibration settings
        self._load_calibration()
        
        # Load model for kinematics calculations
        self._load_mujoco_model()

    def _load_calibration(self):
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        self.calib_file_path = os.path.join(root_dir, "load_cell_calibration.json")
        if os.path.exists(self.calib_file_path):
            try:
                with open(self.calib_file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.tare_L = data.get("tare_L", 0.0)
                self.tare_R = data.get("tare_R", 0.0)
                self.cal_factor_L = data.get("cal_factor_L", 1.0)
                self.cal_factor_R = data.get("cal_factor_R", 1.0)
                self.port = data.get("port", "COM11")
                logger.log(f"ForceSensing: Loaded load cell calibration: tare_L={self.tare_L}, tare_R={self.tare_R}, cal_L={self.cal_factor_L}, cal_R={self.cal_factor_R}, port={self.port}")
            except Exception as e:
                logger.log(f"ForceSensing: Failed to load calibration config: {e}", "WARNING")

    def save_calibration(self):
        try:
            data = {
                "tare_L": self.tare_L,
                "tare_R": self.tare_R,
                "cal_factor_L": self.cal_factor_L,
                "cal_factor_R": self.cal_factor_R,
                "port": self.port
            }
            with open(self.calib_file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            logger.log(f"ForceSensing: Calibration persistently saved to {self.calib_file_path}")
        except Exception as e:
            logger.log(f"ForceSensing: Failed to save calibration config: {e}", "WARNING")

    def tare_scales(self):
        self.tare_L = self.raw_L
        self.tare_R = self.raw_R
        self.save_calibration()
        logger.log(f"ForceSensing: Tared scales at raw_L={self.tare_L:.2f}, raw_R={self.tare_R:.2f}")

    def calibrate_scale(self, side: str, known_weight: float) -> bool:
        if known_weight <= 0.0:
            return False
        if side.lower() == "left":
            diff = self.raw_L - self.tare_L
            self.cal_factor_L = diff / known_weight
            if abs(self.cal_factor_L) < 1e-4:
                self.cal_factor_L = 1.0
        elif side.lower() == "right":
            diff = self.raw_R - self.tare_R
            self.cal_factor_R = diff / known_weight
            if abs(self.cal_factor_R) < 1e-4:
                self.cal_factor_R = 1.0
        else:
            return False
        self.save_calibration()
        logger.log(f"ForceSensing: Calibrated {side} scale with known weight {known_weight}g (factor={self.cal_factor_L if side=='left' else self.cal_factor_R})")
        return True

    def update_port(self, port: str):
        self.port = port
        self.save_calibration()

    def start_reading(self):
        self.stop_reading()
        self.stop_event.clear()
        self.running = True
        import threading
        self.serial_thread = threading.Thread(target=self._serial_worker, daemon=True)
        self.serial_thread.start()

    def stop_reading(self):
        self.running = False
        self.connected = False
        self.stop_event.set()
        if self.serial_thread and self.serial_thread.is_alive():
            self.serial_thread.join(timeout=1.0)
            self.serial_thread = None

    def _serial_worker(self):
        import serial
        import re
        baud_rates = [57600, 115200, 9600, 38400]
        baud_idx = 0
        timeout_count = 0
        consecutive_invalid = 0
        last_logged_err = None
        
        while self.running and not self.stop_event.is_set():
            current_baud = baud_rates[baud_idx]
            try:
                with serial.Serial(self.port, current_baud, timeout=1.0) as ser:
                    self.connected = True
                    last_logged_err = None
                    ser.reset_input_buffer()
                    
                    while self.running and not self.stop_event.is_set():
                        line = ser.readline()
                        if not line:
                            timeout_count += 1
                            if timeout_count >= 3:
                                if self.connected:
                                    logger.log(f"ForceSensing: Serial timeout on {self.port} at {current_baud} baud. Switching baud rate...", "WARNING")
                                    self.connected = False
                                baud_idx = (baud_idx + 1) % len(baud_rates)
                                break # Exit inner loop to reconnect with next baud rate
                            continue
                        
                        timeout_count = 0
                        try:
                            decoded = line.decode('utf-8', errors='ignore').strip()
                            if not decoded:
                                continue
                            
                            # Extract all numbers using regular expression to bypass labels/units
                            numbers = re.findall(r"[-+]?\d*\.\d+|\d+", decoded)
                            if len(numbers) > 0:
                                # Successfully parsed numbers! Lock onto this baud rate
                                if not self.connected:
                                    logger.log(f"ForceSensing: Serial connection active on {self.port} at {current_baud} baud.")
                                    self.connected = True
                                consecutive_invalid = 0
                                
                                # Log raw line every 100 iterations for GUI console debugging
                                self.line_count = getattr(self, 'line_count', 0) + 1
                                if self.line_count % 100 == 0:
                                    logger.log(f"ForceSensing: Raw serial line: '{decoded}'")
                                
                                if len(numbers) >= 2:
                                    self.raw_L = float(numbers[0])
                                    self.raw_R = float(numbers[1])
                                elif len(numbers) == 1:
                                    val = float(numbers[0])
                                    if self.loadcell_arm == "right":
                                        self.raw_R = val
                                        self.raw_L = 0.0
                                    else:
                                        self.raw_L = val
                                        self.raw_R = 0.0
                                        
                                # Compute calibrated weight values
                                denom_L = self.cal_factor_L if self.cal_factor_L != 0.0 else 1.0
                                denom_R = self.cal_factor_R if self.cal_factor_R != 0.0 else 1.0
                                self.weight_L = (self.raw_L - self.tare_L) / denom_L
                                self.weight_R = (self.raw_R - self.tare_R) / denom_R
                            else:
                                # Received line but no numbers (garbage text from incorrect baud rate)
                                consecutive_invalid += 1
                                if consecutive_invalid >= 15:
                                    logger.log(f"ForceSensing: Received 15 consecutive non-numeric frames on {self.port} at {current_baud} baud (likely wrong baud rate). Switching...", "WARNING")
                                    consecutive_invalid = 0
                                    self.connected = False
                                    baud_idx = (baud_idx + 1) % len(baud_rates)
                                    break # Exit inner loop to reconnect with next baud rate
                            
                        except ValueError as ve:
                            self.err_count = getattr(self, 'err_count', 0) + 1
                            if self.err_count % 50 == 0:
                                logger.log(f"ForceSensing: Serial data value conversion error: '{decoded}'", "WARNING")
                        except Exception:
                            pass
            except Exception as e:
                self.connected = False
                err_msg = str(e)
                if err_msg != last_logged_err:
                    logger.log(f"ForceSensing: Connection failed on port {self.port} at {current_baud} baud: {err_msg}. Retrying...", "WARNING")
                    last_logged_err = err_msg
                # Sleep using event wait (instantly interruptible on exit)
                self.stop_event.wait(3.0)

    def update_mock_weights(self, ball_y: float):
        """Simulates raw sensor counts and weights when the physical serial connection is offline."""
        if not self.connected:
            # Distribute 150g weight of the ball based on position:
            # ball_y in [-0.22, 0.22] meters
            fraction = (ball_y + 0.22) / 0.44
            fraction = max(0.0, min(1.0, fraction))
            sim_weight_R = fraction * 150.0
            sim_weight_L = (1.0 - fraction) * 150.0
            
            # Add small noise
            noise_L = random.uniform(-0.1, 0.1)
            noise_R = random.uniform(-0.1, 0.1)
            
            self.weight_L = sim_weight_L + noise_L
            self.weight_R = sim_weight_R + noise_R
            
            # Back-calculate raw ADC counts based on simulated weight, tare, and factors
            self.raw_L = self.weight_L * self.cal_factor_L + self.tare_L
            self.raw_R = self.weight_R * self.cal_factor_R + self.tare_R

    def _load_mujoco_model(self):
        xml_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "simulation_ref", "my_bot.xml")
        if os.path.exists(xml_path):
            try:
                import mujoco
                self.model = mujoco.MjModel.from_xml_path(xml_path)
                self.data = mujoco.MjData(self.model)
                self.model_loaded = True
            except Exception:
                pass

    def read_load_cell(self) -> float:
        """Simulates/reads values from load cell in Newtons (N)."""
        # Sum both weights and convert grams to Newtons
        total_mass_g = self.weight_L + self.weight_R
        total_force_n = (total_mass_g / 1000.0) * 9.81
        self.load_cell_value = total_force_n
        return self.load_cell_value

    def update_estimation(self, telemetry_data: Dict[int, Dict[str, Any]], active_robot: Any, mock_mode: bool = False) -> Dict[str, Any]:
        """Disabled weight logic fallback."""
        return {
            "left_eef_weight_g": 0.0,
            "right_eef_weight_g": 0.0,
            "left_eef_weight_kg": 0.0,
            "right_eef_weight_kg": 0.0,
            "joint_torques": {}
        }

    def get_telemetry(self) -> Dict[str, Any]:
        return {
            "load_cell_n": self.read_load_cell(),
            "sensor_health": 100.0,
            "weight_L": self.weight_L,
            "weight_R": self.weight_R,
            "raw_L": self.raw_L,
            "raw_R": self.raw_R,
            "tare_L": self.tare_L,
            "tare_R": self.tare_R,
            "cal_factor_L": self.cal_factor_L,
            "cal_factor_R": self.cal_factor_R,
            "port": self.port,
            "connected": self.connected
        }
