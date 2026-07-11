import threading
import time
import random
import math
from typing import Dict, List, Any, Optional
import numpy as np

# Absolute import from local tree
from dynamixel_driver import DynamixelDriver
from src.core.logging import logger
from src.modules.robots.base_robot import BaseRobot

class RobotManager:
    """
    Manages the active robot instance, handles serial bus connections, 
    drives the 50Hz control thread, and coordinates calibration and presets.
    """
    def __init__(self, event_bus):
        self.event_bus = event_bus
        self.active_robot: Optional[BaseRobot] = None
        self.driver: Optional[DynamixelDriver] = None
        self.dxl_lock = threading.Lock()
        
        # Subscribe to replay frames to drive robot joints
        self.event_bus.subscribe("replay_frame", self._on_replay_frame)
        
        # Connection status
        self.connected = False
        self.active_port = "COM14"
        self.baudrate = 4000000
        self.mock_mode = False
        
        # Operational variables
        self.estop_active = False
        self.tracking_enabled = False
        self.camera_active = False
        self.plugin_manager = None
        
        # Balancer Pose Sequence tracking
        self.is_balancer_seq_playing = False
        self.balancer_seq_name = ""
        self.balancer_seq_step = 0
        self.balancer_seq_total = 0
        
        # Safety limits
        self.current_limit = 250
        self.speed_limit = 150
        
        # Positions
        self.manual_positions: Dict[int, int] = {}
        self.target_positions: Dict[int, int] = {}
        self.smoothed_positions: Dict[int, int] = {}
        self.latest_telemetry: Dict[int, Dict[str, Any]] = {}
        
        # Emote tracking
        self.is_emote_running = False
        self.active_emote_frames: List[Dict[int, int]] = []
        self.emote_frame_index = 0
        self.emote_delay_ms = 50
        self.emote_auto_torqued_ids: List[int] = []
        
        # Calibration state
        self.calib_running = False
        self.calib_progress = 0.0
        self.calib_status_msg = "Idle"
        self.calib_paused = False
        self.calib_aborted = False
        self.calib_retry = False
        self.calib_fault_reason = ""
        self.calib_trajectory: List[Dict[int, int]] = []
        self.calib_active_ids: List[int] = []
        self.calib_start_pose: Dict[int, int] = {}
        self.calib_end_pose: Dict[int, int] = {}
        
        # Diagnostics
        self.mock_errors: Dict[int, int] = {}
        self.last_reboot_time: Dict[int, float] = {}
        self.system_health = 100
        self.cpu_usage = 4.2
        self.ram_usage = 1.8
        self.latency = 0.0
        self.fps = 0
        
        # Caching variables for decimated reads
        self.read_cycle_count = 0
        self._cached_currents = {}
        self._cached_errors = {}
        
        # Threads
        self.dxl_thread: Optional[threading.Thread] = None
        self.dxl_thread_running = False
        
        # Symmetrical Mirror Sync
        self.mirror_sync_active = False


    def set_robot(self, robot: BaseRobot):
        """Switches the active robot profile and updates defaults."""
        self.active_robot = robot
        self.update_motor_defaults()
        if self.driver is not None:
            with self.dxl_lock:
                self.driver.motor_ids = list(robot.get_joint_layout().keys())
        logger.log(f"Profile version switched to {robot.name} {robot.version}")
        self.event_bus.publish("robot_changed", robot)

    def update_motor_defaults(self):
        """Sets target positions to the defaults defined in the active robot profile."""
        if not self.active_robot:
            return
        limits = self.active_robot.get_joint_layout()
        self.manual_positions.clear()
        for mid, info in limits.items():
            self.manual_positions[mid] = info["default"]

    def connect(self, port: str, baudrate: int, mock_mode: bool, current_limit: int = 250, speed_limit: int = 150) -> Dict[str, Any]:
        """Initializes connection to the Dynamixel bus driver."""
        if self.connected:
            return {"status": "error", "message": "Bus connection already active."}
            
        if not self.active_robot:
            return {"status": "error", "message": "No robot selected."}

        limits = self.active_robot.get_joint_layout()
        motor_ids = list(limits.keys())
        
        logger.log(f"Initializing bus protocols on port {port} ({baudrate} bps)...")
        
        self.driver = DynamixelDriver(
            port=port,
            baudrate=baudrate,
            motor_ids=motor_ids,
            mock_mode=mock_mode
        )
        
        if self.driver.connect():
            self.connected = True
            self.active_port = port
            self.baudrate = baudrate
            self.mock_mode = mock_mode
            self.current_limit = current_limit
            self.speed_limit = speed_limit
            
            if not mock_mode:
                logger.log("Scanning Dynamixel serial bus...")
                active_ids = self.driver.scan()
                
                # Auto-baudrate recovery check
                missing_ids = [mid for mid in motor_ids if mid not in active_ids]
                if missing_ids:
                    logger.log(f"Actuators {missing_ids} are missing at {baudrate} bps. Initiating baud rate recovery auto-scan...", "WARNING")
                    self._recover_baudrates(port, missing_ids, baudrate)
                    # Scan again after recovery
                    active_ids = self.driver.scan()
                    
                if not active_ids:
                    logger.log("Hardware scan returned zero active actuators. Safe abort.", "ERROR")
                    self.driver.disconnect()
                    self.driver = None
                    self.connected = False
                    return {"status": "error", "message": "Scan failed: No active motors detected."}
                
                # Auto-detect profile from scanned active motor IDs
                if hasattr(self, "plugin_manager") and self.plugin_manager:
                    active_set = set(active_ids)
                    detected_profile = None
                    if active_set.issubset(set(range(16))) and len(active_set) > 8:
                        detected_profile = "V1"
                    elif active_set.issubset(set(range(8))) and len(active_set) > 4:
                        detected_profile = "V2"
                    elif active_set.issubset({11, 12, 13, 14, 15}) and len(active_set) >= 4:
                        detected_profile = "Open Manipulator X"
                    elif active_set.issubset({21, 12, 13, 24, 25, 26, 27, 28, 11, 22, 23, 14, 15, 16, 17, 18, 31, 32}) and len(active_set) > 5:
                        detected_profile = "Humanoid V1"
                        
                    if detected_profile and detected_profile in self.plugin_manager.robots:
                        new_robot = self.plugin_manager.robots[detected_profile]
                        self.set_robot(new_robot)
                        logger.log(f"Auto-detected hardware configuration. Auto-switched profile to: {detected_profile}")
                        
                self.driver.motor_ids = active_ids
                logger.log(f"Actuator scanning complete. Found {len(active_ids)} active nodes: {active_ids}")
            
            with self.dxl_lock:
                # Set operating mode dynamically based on profile
                mode = 4 if (self.active_robot and self.active_robot.name == "Humanoid Bot") else 5
                self.driver.set_operating_mode(self.driver.motor_ids, mode=mode)
                if not mock_mode:
                    self.driver.set_torque_limits(self.driver.motor_ids, limit_ma=current_limit)
                    self.driver.set_current_limits(self.driver.motor_ids, limit_ma=current_limit)
                    self.driver.set_pid_gains(self.driver.motor_ids, kp=200, ki=0, kd=80)
                    self.driver.set_profile_velocity(self.driver.motor_ids, velocity=speed_limit)
            
            self.dxl_thread_running = True
            self.dxl_thread = threading.Thread(target=self._dxl_worker_loop, daemon=True)
            self.dxl_thread.start()
            logger.log(f"OSRS live connection active. Profile: {self.active_robot.name}")
            return {"status": "success", "active_motors": self.driver.motor_ids}
        else:
            self.driver = None
            self.connected = False
            logger.log("Communication line connection failed.", "ERROR")
            return {"status": "error", "message": "Connection failed: Port unavailable or invalid configuration."}

    def disconnect(self):
        """Safely stops DXL worker threads and disconnects physical lines."""
        if not self.connected:
            return {"status": "already disconnected"}
            
        logger.log("De-initializing bus protocol. Closing threads...")
        self.dxl_thread_running = False
        if self.dxl_thread:
            self.dxl_thread.join(timeout=1.0)
            self.dxl_thread = None
            
        if self.driver:
            self.driver.disconnect()
            self.driver = None
            
        self.connected = False
        logger.log("Bus protocol connection closed safely.")
        return {"status": "success"}

    def trigger_estop(self, active: bool):
        self.estop_active = active
        if active:
            logger.log("EMERGENCY ESTOP ENGAGED - ALL WRITE PACKETS SHUT DOWN", "ERROR")
            if self.driver and self.driver.is_connected:
                try:
                    with self.dxl_lock:
                        self.driver.enable_torque(self.driver.motor_ids, False)
                        for mid in self.driver.motor_ids:
                            self.driver.torque_state[mid] = False
                except Exception as e:
                    logger.log(f"Failed to safely cut torque: {e}", "ERROR")
        else:
            logger.log("Emergency E-Stop released. Operator control restored.", "WARNING")

    def toggle_torque(self, motor_id: str, enable: bool) -> bool:
        if not self.driver or not self.driver.is_connected:
            return False
            
        if motor_id == "global":
            targets = self.driver.motor_ids
            logger.log(f"Set torque globally to {enable} for all joints.")
        elif motor_id == "left":
            targets = [21, 12, 13, 24, 25, 26, 27, 28]
            logger.log(f"Set torque to {enable} for Left Arm motors: {targets}")
        elif motor_id == "right":
            targets = [11, 22, 23, 14, 15, 16, 17, 18]
            logger.log(f"Set torque to {enable} for Right Arm motors: {targets}")
        else:
            try:
                targets = [int(motor_id)]
                logger.log(f"Set torque to {enable} for Motor ID {motor_id}.")
            except ValueError:
                return False
                
        with self.dxl_lock:
            targets = [t for t in targets if t in self.driver.motor_ids]
            if not targets:
                return True
            success = self.driver.enable_torque(targets, enable)
            if success:
                for mid in targets:
                    self.driver.torque_state[mid] = enable
            return success

    def trigger_reboot(self, motor_id: int):
        threading.Thread(target=self._reboot_individual_motor_sequence, args=(motor_id,), daemon=True).start()

    def _reboot_individual_motor_sequence(self, motor_id: int):
        logger.log(f"Initiating individual reboot sequence for Motor ID {motor_id}...")
        success = False
        was_torque_on = False
        
        if self.driver is not None and self.driver.is_connected:
            was_torque_on = self.driver.torque_state.get(motor_id, False)
            with self.dxl_lock:
                success = self.driver.reboot([motor_id])
            if self.driver.mock_mode:
                if motor_id in self.mock_errors:
                    self.mock_errors[motor_id] = 0
                success = True
        else:
            if motor_id in self.mock_errors:
                self.mock_errors[motor_id] = 0
            success = True
            
        if success:
            logger.log(f"Reboot packet successfully processed for Motor {motor_id}.")
            if was_torque_on:
                logger.log(f"Scheduling torque auto-recovery for Motor {motor_id} in 600ms...")
                time.sleep(0.600)
                if self.driver is not None and self.driver.is_connected:
                    logger.log(f"Restoring torque status for Motor {motor_id}...")
                    with self.dxl_lock:
                        rec_success = self.driver.enable_torque([motor_id], True)
                    if rec_success:
                        logger.log(f"Torque successfully restored for Motor {motor_id}.")
                    else:
                        logger.log(f"Torque auto-recovery failed for Motor {motor_id}.", "ERROR")
        else:
            logger.log(f"Reboot command failed for Motor {motor_id}.", "ERROR")

    def _dxl_worker_loop(self):
        logger.log("Dynamixel worker thread starting...")
        while self.dxl_thread_running:
            start_time = time.time()
            
            # Simulated stats updates
            self.cpu_usage = round(random.uniform(3.5, 7.5) if not self.estop_active else 1.2, 1)
            self.ram_usage = round(random.uniform(1.7, 1.9), 2)
            
            if self.driver is None or not self.driver.is_connected:
                time.sleep(0.03)
                self.latency = 0.0
                continue
                
            motor_ids = self.driver.motor_ids
            targets = self.manual_positions.copy() if not self.tracking_enabled else self.target_positions.copy()
            
            pres_pos = {}
            pres_cur = {}
            pres_err = {}
            
            self.read_cycle_count += 1
            t_start = time.time()
            try:
                with self.dxl_lock:
                    torque_active = any(self.driver.torque_state.values())
                    pres_pos = self.driver.read_positions(motor_ids)
                    
                    # Decimate currents read to ~10Hz (every 5 cycles)
                    if self.read_cycle_count % 5 == 0 or not self._cached_currents:
                        self._cached_currents = self.driver.read_currents(motor_ids)
                    pres_cur = self._cached_currents
                    
                    # Decimate hardware errors read to ~1Hz (every 50 cycles)
                    if self.read_cycle_count % 50 == 0 or not self._cached_errors:
                        if self.driver.mock_mode:
                            self._cached_errors = {mid: self.mock_errors.get(mid, 0) for mid in motor_ids}
                        else:
                            self._cached_errors = self.driver.read_hardware_errors_sync(motor_ids)
                    pres_err = self._cached_errors
                        
                    if not torque_active:
                        self.smoothed_positions.clear()
                        
                    # Write targets
                    if targets and torque_active and not self.estop_active:
                        write_dict = {}
                        balancer_active = False
                        if self.plugin_manager:
                            balancer = self.plugin_manager.research_modules.get("ball_balancer")
                            if balancer and getattr(balancer, "is_active", False):
                                balancer_active = True
                        alpha = 1.0 if (self.is_emote_running or self.is_balancer_seq_playing or balancer_active) else 0.25
                        limits = self.active_robot.get_joint_layout() if self.active_robot else {}
                        
                        for mid in motor_ids:
                            if mid in targets:
                                target_val = targets[mid]
                                current_val = self.smoothed_positions.get(mid)
                                if current_val is None:
                                    current_val = pres_pos.get(mid, target_val)
                                    if not isinstance(current_val, (int, float)):
                                        current_val = target_val
                                        
                                should_wrap = (0 <= target_val <= 4095)
                                if mid in limits:
                                    if not (0 <= limits[mid]["min"] <= 4095) or not (0 <= limits[mid]["max"] <= 4095):
                                        should_wrap = False
                                        
                                if should_wrap:
                                    diff = (target_val - current_val + 2048) % 4096 - 2048
                                    new_val = int((current_val + alpha * diff) % 4096)
                                else:
                                    diff = target_val - current_val
                                    new_val = int(current_val + alpha * diff)
                                    
                                self.smoothed_positions[mid] = new_val
                                write_dict[mid] = new_val
                                
                        if write_dict:
                            self.driver.write_positions(write_dict)
                            
                # Telemetry sync if torque off
                if not torque_active and pres_pos:
                    limits = self.active_robot.get_joint_layout() if self.active_robot else {}
                    for mid in motor_ids:
                        pos = pres_pos.get(mid)
                        if isinstance(pos, (int, float)):
                            pos_int = int(pos)
                            if mid in limits:
                                pos_int = int(np.clip(pos_int, limits[mid]["min"], limits[mid]["max"]))
                            self.manual_positions[mid] = pos_int
                            self.target_positions[mid] = pos_int
                            
                # Assemble telemetry payload
                new_telemetry = {}
                for mid in motor_ids:
                    new_telemetry[mid] = {
                        "goal": targets.get(mid, 2048),
                        "present": pres_pos.get(mid, "--"),
                        "current": pres_cur.get(mid, "--"),
                        "error": pres_err.get(mid, 0),
                        "torque": self.driver.torque_state.get(mid, False) if self.driver else False
                    }
                self.latest_telemetry = new_telemetry
            except Exception as e:
                logger.log(f"Error in Dynamixel worker loop cycle: {e}", "WARNING")
                time.sleep(0.01)

            self.latency = round((time.time() - t_start) * 1000, 2)
            
            # Call any callback or publish updates
            self.event_bus.publish("telemetry_updated", self.latest_telemetry)
            
            elapsed = time.time() - start_time
            time.sleep(max(0.005, 0.020 - elapsed))
            
        logger.log("Dynamixel worker thread shut down.")

    def _on_replay_frame(self, frame_data: Dict[str, Any]):
        """
        Receives replayed trajectory frames and updates robot motor target/manual positions.
        Supports both direct motor ID ticks and simulation joint names in radians.
        """
        joints = frame_data.get("joints", {})
        if not self.active_robot:
            return
            
        limits = self.active_robot.get_joint_layout()
        
        # Build a mapping from joint name to motor ID
        name_to_id = {}
        for mid, info in limits.items():
            name_to_id[info["name"]] = mid

        # Standard MuJoCo name mapping dictionary to Dynamixel motor IDs
        mujoco_joint_map = {
            "r_sho_pitch": 11, "r_sho_roll": 22, "r_sho_yaw": 23, "r_el_pitch": 14,
            "r_forearm_yaw": 15, "r_wrist_pitch": 16, "r_wrist_yaw": 17, "r_finger_l_joint": 18, "r_finger_r_joint": 18,
            "l_sho_pitch": 21, "l_sho_roll": 12, "l_sho_yaw": 13, "l_el_pitch": 24,
            "l_forearm_yaw": 25, "l_wrist_pitch": 26, "l_wrist_yaw": 27, "l_finger_l_joint": 28, "l_finger_r_joint": 28,
            "head_yaw": 31, "head_tilt": 32
        }

        with self.dxl_lock:
            for key, val in joints.items():
                try:
                    # Resolve motor ID
                    mid = None
                    if key.isdigit():
                        mid = int(key)
                    elif key in name_to_id:
                        mid = name_to_id[key]
                    elif key in mujoco_joint_map:
                        mid = mujoco_joint_map[key]

                    if mid is not None and isinstance(val, (int, float)):
                        # Check if the value is in radians or ticks
                        if -20.0 <= val <= 20.0:
                            # Convert radians to encoder ticks: default + (rad / pi) * 2048
                            if mid in limits:
                                default_val = limits[mid].get("default", 2048)
                                tick = int(default_val + (val / math.pi) * 2048)
                                self.manual_positions[mid] = tick
                                self.target_positions[mid] = tick
                        else:
                            # Direct tick value
                            self.manual_positions[mid] = int(val)
                            self.target_positions[mid] = int(val)
                except Exception:
                    pass

    def _recover_baudrates(self, port: str, missing_ids: List[int], target_baudrate: int):
        """
        Scans missing Dynamixel actuator IDs on common lower baudrates and automatically 
        re-programs their EEPROM register (address 8) to the target_baudrate, reboots them, 
        and restores the connection.
        """
        try:
            import dynamixel_sdk as dxl
        except ImportError:
            logger.log("Cannot recover baudrates: dynamixel_sdk is not installed.", "ERROR")
            return
            
        # Determine target baudrate code (Address 8 value)
        baud_val = None
        if target_baudrate == 4000000:
            baud_val = 6
        elif target_baudrate == 3000000:
            baud_val = 5
        elif target_baudrate == 2000000:
            baud_val = 4
        elif target_baudrate == 1000000:
            baud_val = 3
        elif target_baudrate == 115200:
            baud_val = 2
        elif target_baudrate == 57600:
            baud_val = 1
            
        if baud_val is None:
            logger.log(f"Cannot recover baudrates: Target baudrate {target_baudrate} is not standard.", "ERROR")
            return
            
        # Temporarily disconnect the main driver so we can open the port at other baudrates
        if self.driver:
            self.driver.disconnect()
            
        # List of common baudrates to scan (excluding target)
        common_bauds = [1000000, 2000000, 57600, 115200]
        if target_baudrate in common_bauds:
            common_bauds.remove(target_baudrate)
            
        remaining_ids = missing_ids.copy()
        
        for temp_baud in common_bauds:
            logger.log(f"Scanning missing actuators {remaining_ids} at {temp_baud} bps...")
            temp_port = dxl.PortHandler(port)
            temp_packet = dxl.PacketHandler(2.0)
            
            if not temp_port.openPort():
                continue
            if not temp_port.setBaudRate(temp_baud):
                temp_port.closePort()
                continue
                
            found_ids = []
            for mid in remaining_ids:
                model, res, err = temp_packet.ping(temp_port, mid)
                if res == 0:
                    found_ids.append(mid)
                    
            if found_ids:
                logger.log(f"[+] Found missing actuators {found_ids} at {temp_baud} bps. Re-configuring to {target_baudrate} bps...")
                for mid in found_ids:
                    # 1. Disable torque first (Address 64) to allow EEPROM write
                    res1, err1 = temp_packet.write1ByteTxRx(temp_port, mid, 64, 0)
                    time.sleep(0.05)
                    # 2. Write new baud rate value (Address 8)
                    res2, err2 = temp_packet.write1ByteTxRx(temp_port, mid, 8, baud_val)
                    time.sleep(0.1)  # CRITICAL: wait for EEPROM write completion!
                    # 3. Reboot the motor so the change takes effect
                    res3, err3 = temp_packet.reboot(temp_port, mid)
                    logger.log(f"Reconfigured motor {mid}: torque disable (res={res1}, err={err1}), baudrate set (res={res2}, err={err2}), reboot (res={res3}, err={err3})")
                    
                temp_port.closePort()
                
                # Remove found IDs from the scan list
                for mid in found_ids:
                    if mid in remaining_ids:
                        remaining_ids.remove(mid)
                        
                logger.log("Waiting for re-configured actuators to reboot (2.5s)...")
                time.sleep(2.5)
            else:
                temp_port.closePort()
                
            if not remaining_ids:
                break
                
        # Reconnect main driver
        if self.driver:
            self.driver.connect()

    def get_mirrored_position(self, mid: int, val: int) -> int:
        """Calculates the mirrored coordinate for a joint using dynamic calibration offsets."""
        if not self.active_robot or self.active_robot.name != "Humanoid Bot":
            return val
            
        calib_left = getattr(self.active_robot, "calib_left", {})
        calib_right = getattr(self.active_robot, "calib_right", {})
        limits = self.active_robot.get_joint_layout()
        
        # Build reference centers
        ref_centers = {}
        for k, info in limits.items():
            ref_centers[k] = info["default"]
        ref_centers.update(calib_left)
        ref_centers.update(calib_right)
        
        mirror_partners = {
            21: 11, 11: 21,
            12: 22, 22: 12,
            13: 23, 23: 13,
            24: 14, 14: 24,
            25: 15, 15: 25,
            26: 16, 16: 26,
            27: 17, 17: 27,
            28: 18, 18: 28
        }
        
        partner = mirror_partners.get(mid)
        if not partner or partner not in ref_centers or mid not in ref_centers:
            return val
            
        center_self = ref_centers[mid]
        center_partner = ref_centers[partner]
        
        delta = val - center_self
        
        # Symmetrical mirroring rules (opposite or matching directional kinematics)
        opposite_joints = {24, 14, 25, 15, 26, 16, 28, 18, 13, 23}
        if mid in opposite_joints:
            mirrored_val = center_partner - delta
        else:
            mirrored_val = center_partner + delta
            
        # Clamp to limits of partner joint
        if partner in limits:
            p_min = limits[partner]["min"]
            p_max = limits[partner]["max"]
            mirrored_val = max(p_min, min(p_max, mirrored_val))
            
        return int(mirrored_val)

    def set_manual_position(self, motor_id: int, value: int, mirror_propagate: bool = True):
        """Sets a joint target coordinate, optionally propagating symmetrical mirror updates."""
        self.manual_positions[motor_id] = value
        self.target_positions[motor_id] = value
        
        if self.mirror_sync_active and mirror_propagate:
            mirror_partners = {
                21: 11, 11: 21,
                12: 22, 22: 12,
                13: 23, 23: 13,
                24: 14, 14: 24,
                25: 15, 15: 25,
                26: 16, 16: 26,
                27: 17, 17: 27,
                28: 18, 18: 28
            }
            partner_id = mirror_partners.get(motor_id)
            if partner_id:
                mirrored_val = self.get_mirrored_position(motor_id, value)
                self.set_manual_position(partner_id, mirrored_val, mirror_propagate=False)


