import time
import math
import random
import os
import json
from typing import Dict, Any, Optional

from src.core.logging import logger
from src.modules.research.base_research_task import BaseResearchTask

class BallStateProvider:
    """
    Abstract state estimator provider for the Ball Balancer research module.
    """
    def get_ball_state(self) -> Dict[str, float]:
        """
        Returns:
            { "x": float, "y": float, "vx": float, "vy": float, "confidence": float }
        """
        raise NotImplementedError("State providers must implement get_ball_state")

class VisionBallTracker(BallStateProvider):
    """
    State provider using visual feedback (webcam or MuJoCo simulator state).
    """
    def __init__(self):
        self.x = 0.05  # Start offset matching simulation_ref
        self.y = 0.0
        self.last_time = time.time()
        self.vx = 0.0
        self.vy = 0.0

    def set_measured_position(self, x: float, y: float):
        """Allows feed injection from camera landmarker or simulator."""
        now = time.time()
        dt = max(0.005, now - self.last_time)  # Cap minimum dt to 5ms to avoid zero division/spikes
        
        # Calculate raw velocity
        raw_vx = (x - self.x) / dt
        raw_vy = (y - self.y) / dt
        
        # Exponential moving average filter to smooth out high-frequency sensor noise
        # alpha=0.30 gives ~3x faster velocity response than the old 0.15
        alpha = 0.30
        self.vx = alpha * raw_vx + (1 - alpha) * self.vx
        self.vy = alpha * raw_vy + (1 - alpha) * self.vy
        
        self.x = x
        self.y = y
        self.last_time = now

    def get_ball_state(self) -> Dict[str, float]:
        return {
            "x": self.x,
            "y": self.y,
            "vx": self.vx,
            "vy": self.vy,
            "confidence": 0.95
        }

class ForceBallEstimator(BallStateProvider):
    """
    State provider using load-cell force measurements.
    """
    def __init__(self, force_sensor, balancer):
        self.force_sensor = force_sensor
        self.balancer = balancer
        self.y = 0.0
        self.vy = 0.0
        self.last_time = time.time()

    def get_ball_state(self) -> Dict[str, float]:
        w_L = self.force_sensor.weight_L
        w_R = self.force_sensor.weight_R
        ball_present = False
        ratio = 0.0
        
        if self.balancer.loadcell_mode == 2:
            total_w = w_L + w_R
            ball_present = total_w > 15.0
            if ball_present:
                ratio = (w_R - w_L) / total_w
        else:  # 1 load cell mode
            if self.balancer.loadcell_arm == "left":
                ball_present = w_L > 5.0
                if ball_present:
                    ratio = 1.0 - 2.0 * (w_L / max(10.0, self.balancer.ball_weight_ref))
            else:
                ball_present = w_R > 5.0
                if ball_present:
                    ratio = 2.0 * (w_R / max(10.0, self.balancer.ball_weight_ref)) - 1.0
        
        if ball_present:
            c0 = self.balancer.loadcell_c0
            c1 = self.balancer.loadcell_c1
            c2 = self.balancer.loadcell_c2
            c3 = self.balancer.loadcell_c3
            raw_y = c3 * (ratio ** 3) + c2 * (ratio ** 2) + c1 * ratio + c0
            raw_y = max(-0.22, min(0.22, raw_y))
            confidence = 0.90
        else:
            raw_y = 0.0
            confidence = 0.10
            
        now = time.time()
        dt = max(0.005, now - self.last_time)
        self.last_time = now
        
        # Exponential moving average filter
        alpha = 0.25
        new_y = alpha * raw_y + (1 - alpha) * self.y
        raw_vy = (new_y - self.y) / dt
        self.vy = alpha * raw_vy + (1 - alpha) * self.vy
        self.y = new_y
        
        return {
            "x": 0.0,
            "y": self.y,
            "vx": 0.0,
            "vy": self.vy,
            "confidence": confidence
        }

class FusionBallEstimator(BallStateProvider):
    """
    State provider fusing Vision, Force, and torque feedback.
    """
    def __init__(self, vision_provider: VisionBallTracker, force_provider: ForceBallEstimator):
        self.vision = vision_provider
        self.force = force_provider

    def get_ball_state(self) -> Dict[str, float]:
        v_state = self.vision.get_ball_state()
        f_state = self.force.get_ball_state()
        # Fuses based on confidence weights
        w_v = v_state["confidence"]
        w_f = f_state["confidence"]
        sum_w = w_v + w_f
        
        fused_y = (v_state["y"] * w_v + f_state["y"] * w_f) / sum_w
        fused_vy = (v_state["vy"] * w_v + f_state["vy"] * w_f) / sum_w
        
        return {
            "x": v_state["x"],
            "y": fused_y,
            "vx": v_state["vx"],
            "vy": fused_vy,
            "confidence": min(1.0, sum_w)
        }

class BallBalancer(BaseResearchTask):
    """
    Ball Balancer research coordinator containing PID controller 
    and handles updates for the cooperative dual-arm plate balancing.
    """
    def __init__(self, event_bus):
        super().__init__(name="Ball Balancer")
        self.event_bus = event_bus
        self.kp = 1.3   # Moderate proportional response
        self.kd = 0.50  # Damping to suppress overshoot
        self.ki = 0.10
        self.max_delta_z = 0.035
        self.speed_multiplier = 1.0
        self.max_tilt_positive = 150.0
        self.max_tilt_negative = 178.0
        
        self.target_y = 0.0
        self.integral = 0.0
        self.adaptive_tilt = 0.0
        self.last_target_tilt = None
        self.last_commanded_dir = 0
        self.last_time = time.time()
        self.smoothed_tilt = None        # Output-side EMA for smooth joint motion
        
        # Stuck-ball detection
        self.stuck_timer = 0.0
        self.stuck_vel_threshold = 0.008
        self.stuck_err_threshold = 0.04
        self.stuck_time_limit    = 2.0    # seconds of no movement before recovery
        self.stuck_cooldown      = 0.0    # post-reset cooldown timer
        self.stuck_cooldown_dur  = 3.0    # seconds to wait before detecting stuck again
        
        # Instantiate estimators
        self.vision_provider = VisionBallTracker()
        
        # Stubs for force estimation
        from src.modules.perception.force_sensing import ForceSensing
        self.force_sensor = ForceSensing()
        self.force_provider = ForceBallEstimator(self.force_sensor, self)
        
        # Fusion estimator
        self.fusion_provider = FusionBallEstimator(self.vision_provider, self.force_provider)
        
        # Selected provider (defaults to vision)
        self.active_provider: BallStateProvider = self.vision_provider
        self.is_active = False
        self.active_scenario = "NOMINAL"

        # Calibration cache configuration
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        self.calib_file_path = os.path.join(root_dir, "chiman_calibration.json")
        self.last_calib_mtime = 0
        self.cached_calib_l5y = -82

        # Load Cell cubic polynomial calibration coefficients
        self.loadcell_c0 = 0.0
        self.loadcell_c1 = 0.22
        self.loadcell_c2 = 0.0
        self.loadcell_c3 = 0.0

        # Load Cell configuration mode and arm placements
        self.loadcell_mode = 2  # 1 = single load cell, 2 = dual load cells
        self.loadcell_arm = "left"  # "left" or "right"
        self.ball_weight_ref = 100.0  # grams
        self.avg_mapping_error = 0.1  # running average discrepancy in meters
        self.invert_output = False
        self.ball_type = "green_ping_pong"  # "green_ping_pong" or "metal_chrome"

        # Model Exploration / Active Excitation Mode parameters
        self.exploration_mode = False
        self.balanced_time = 0.0
        self.exploration_targets = [0.0, 0.08, 0.0, -0.08]
        self.exploration_target_idx = 0

        # Online Learning / System Identification parameters
        self.auto_tune_enabled = False
        self.est_a = 0.5   # Estimated control authority (acceleration per unit of tilt)
        self.est_b = -0.1  # Estimated rolling resistance/friction (damping)
        self.last_applied_tilt = 0.0
        self.last_velocity = 0.0
        self.learning_history = []
        self.last_save_time = time.time()
        self.learning_data_path = os.path.join(root_dir, "balancer_learning_data.json")
        self._load_learning_data()

    def _load_learning_data(self):
        try:
            if os.path.exists(self.learning_data_path):
                with open(self.learning_data_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.est_a = data.get("est_a", 0.5)
                self.est_b = data.get("est_b", -0.1)
                self.loadcell_c0 = data.get("loadcell_c0", 0.0)
                self.loadcell_c1 = data.get("loadcell_c1", 0.22)
                self.loadcell_c2 = data.get("loadcell_c2", 0.0)
                self.loadcell_c3 = data.get("loadcell_c3", 0.0)
                self.loadcell_mode = data.get("loadcell_mode", 2)
                self.loadcell_arm = data.get("loadcell_arm", "left")
                self.ball_weight_ref = data.get("ball_weight_ref", 100.0)
                self.invert_output = data.get("invert_output", False)
                self.ball_type = data.get("ball_type", "green_ping_pong")
                self.learning_history = data.get("history", [])[-100:]
                logger.log(f"Ball Balancer: Loaded learning parameters est_a={self.est_a:.4f}, est_b={self.est_b:.4f}, mode={self.loadcell_mode}, arm={self.loadcell_arm}, invert={self.invert_output}, ball_type={self.ball_type}")
        except Exception as e:
            logger.log(f"Ball Balancer: Failed to load learning data: {e}", "WARNING")

    def _save_learning_data(self):
        try:
            pruned_history = self.learning_history[-1000:]
            data = {
                "est_a": self.est_a,
                "est_b": self.est_b,
                "loadcell_c0": self.loadcell_c0,
                "loadcell_c1": self.loadcell_c1,
                "loadcell_c2": self.loadcell_c2,
                "loadcell_c3": self.loadcell_c3,
                "loadcell_mode": self.loadcell_mode,
                "loadcell_arm": self.loadcell_arm,
                "ball_weight_ref": self.ball_weight_ref,
                "invert_output": self.invert_output,
                "ball_type": self.ball_type,
                "history": pruned_history
            }
            with open(self.learning_data_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.log(f"Ball Balancer: Failed to save learning data: {e}", "WARNING")

    def set_provider(self, provider_type: str):
        if provider_type == "vision":
            self.active_provider = self.vision_provider
        elif provider_type == "force":
            self.active_provider = self.force_provider
        elif provider_type == "fusion":
            self.active_provider = self.fusion_provider
        logger.log(f"Ball Balancer state provider changed to: {provider_type}")

    def update_gains(self, kp: float, kd: float, ki: float):
        self.kp = kp
        self.kd = kd
        self.ki = ki
        logger.log(f"Ball Balancer PID gains tuned to: Kp={kp}, Kd={kd}, Ki={ki}")

    def set_speed(self, speed: float):
        """Set the balancing speed multiplier (0.1 = very slow, 1.0 = default, 2.0 = very fast)."""
        self.speed_multiplier = max(0.1, min(2.0, float(speed)))
        logger.log(f"Ball Balancer speed multiplier set to: {self.speed_multiplier:.2f}x")

    def set_tilt_limits(self, max_positive: float, max_negative: float):
        """Set the maximum allowed tilt offset (servo units) above/below calibration center."""
        self.max_tilt_positive = max(10.0, float(max_positive))
        self.max_tilt_negative = max(10.0, float(max_negative))
        logger.log(f"Ball Balancer tilt limits set to: +{self.max_tilt_positive} / -{self.max_tilt_negative} units")

    def reset_loadcell_model(self):
        self.loadcell_c0 = 0.0
        self.loadcell_c1 = 0.22
        self.loadcell_c2 = 0.0
        self.loadcell_c3 = 0.0
        self._save_learning_data()
        logger.log("Ball Balancer: Load cell polynomial calibration model reset to default linear state.")

    def update_controller(self, dt: float) -> float:
        """
        Predictive PD controller for ball balancing.
        Reacts to the ball's predicted future position (current + velocity * lookahead)
        rather than current position, eliminating reaction lag and oscillation.
        """
        # Update simulated weight values if hardware serial port is disconnected
        vis_state = self.vision_provider.get_ball_state()
        self.force_sensor.update_mock_weights(vis_state["y"])

        state = self.active_provider.get_ball_state()

        # Safety fallback if tracking is lost
        if state.get("confidence", 0.0) < 0.2:
            self.integral = 0.0
            self.adaptive_tilt = 0.0
            self.stuck_timer = 0.0
            self.stuck_cooldown = 0.0
            self.last_target_tilt = None
            self.last_commanded_dir = 0
            self.event_bus.publish("balancer_frame", {
                "ball_y": state["y"], "ball_vy": state["vy"],
                "target_y": self.target_y, "delta_z": float(self.cached_calib_l5y),
                "confidence": state["confidence"], "ball_error": 0.0
            })
            return float(self.cached_calib_l5y)

        error    = state["y"]   # metres [-0.22, 0.22]
        velocity = state["vy"]  # m/s

        # ── ACTIVE MODEL EXPLORATION (EXCITATION TARGET SHIFTING) ─────────────
        if self.exploration_mode:
            current_error = abs(error - self.target_y)
            if current_error < 0.02 and abs(velocity) < 0.05:
                self.balanced_time += dt
            else:
                if current_error > 0.04:
                    self.balanced_time = max(0.0, self.balanced_time - dt * 2.0)
            
            if self.balanced_time >= 1.5:
                self.exploration_target_idx = (self.exploration_target_idx + 1) % len(self.exploration_targets)
                self.target_y = self.exploration_targets[self.exploration_target_idx]
                self.balanced_time = 0.0
                logger.log(f"Ball Balancer Exploration: Balanced! Shifting target to {self.target_y * 1005:.1f} mm")
        else:
            self.target_y = 0.0
            self.balanced_time = 0.0

        # ── COORDINATE SYSTEM LEARNING (VISION TO LOAD CELL MAP) ──────────────
        # Map: y_vision = c3 * r^3 + c2 * r^2 + c1 * r + c0
        # Calibrate weights dynamically when camera tracking is reliable
        w_L = self.force_sensor.weight_L
        w_R = self.force_sensor.weight_R
        total_w = w_L + w_R
        
        reliable = False
        ratio = 0.0
        if self.loadcell_mode == 2:
            reliable = total_w > 15.0
            if reliable:
                ratio = (w_R - w_L) / total_w
        else:  # 1 load cell mode
            if self.loadcell_arm == "left":
                reliable = w_L > 5.0
                if reliable:
                    ratio = 1.0 - 2.0 * (w_L / max(10.0, self.ball_weight_ref))
            else:
                reliable = w_R > 5.0
                if reliable:
                    ratio = 2.0 * (w_R / max(10.0, self.ball_weight_ref)) - 1.0

        if vis_state.get("confidence", 0.0) >= 0.8 and reliable:
            y_vision = vis_state["y"]
            y_lc_pred = self.loadcell_c3 * (ratio ** 3) + self.loadcell_c2 * (ratio ** 2) + self.loadcell_c1 * ratio + self.loadcell_c0
            err_lc = y_vision - y_lc_pred
            
            # Update running mapping convergence error
            self.avg_mapping_error = 0.98 * self.avg_mapping_error + 0.02 * abs(err_lc)
            
            # Gradient descent coordinate mapping updates
            lr_lc = 0.02
            self.loadcell_c0 += lr_lc * err_lc
            self.loadcell_c1 += lr_lc * err_lc * ratio
            self.loadcell_c2 += (lr_lc * 0.5) * err_lc * (ratio ** 2)   # lower rate for quadratic
            self.loadcell_c3 += (lr_lc * 0.25) * err_lc * (ratio ** 3)  # lower rate for cubic
            
            # Clamp settings to physical constraints
            self.loadcell_c0 = max(-0.15, min(0.15, self.loadcell_c0))
            self.loadcell_c1 = max(0.05, min(0.60, self.loadcell_c1))
            self.loadcell_c2 = max(-0.25, min(0.25, self.loadcell_c2))
            self.loadcell_c3 = max(-0.25, min(0.25, self.loadcell_c3))

        # ── SYSTEM IDENTIFICATION (ONLINE LEARNING) ──────────────────────────
        # 1. Estimate raw acceleration
        acc = 0.0
        if dt > 0.001:
            acc = (velocity - self.last_velocity) / dt

        # Normalize last applied relative tilt to keep system identification parameters scaled around 1.0
        u_prev = self.last_applied_tilt / 100.0
        
        # 2. Predict acceleration with model: acc_pred = a * u + b * v
        pred_acc = self.est_a * u_prev + self.est_b * self.last_velocity
        
        # 3. Compute prediction error
        pred_err = acc - pred_acc
        
        # 4. Gradient descent step (LMS)
        # Update parameters only when tracking is reliable and there is active motion
        if state.get("confidence", 0.0) >= 0.8 and (abs(velocity) > 0.002 or abs(u_prev) > 0.02):
            lr_a = 0.015
            lr_b = 0.015
            self.est_a += lr_a * pred_err * u_prev
            self.est_b += lr_b * pred_err * self.last_velocity
            
            # Constraint clamps: control authority must be positive; friction must be dissipative (negative/neutral)
            self.est_a = max(0.1, min(3.0, self.est_a))
            self.est_b = max(-1.0, min(0.2, self.est_b))

        # Save the current state for the next calculation interval
        self.last_velocity = velocity

        # Reload calibration center only when file changes
        try:
            if os.path.exists(self.calib_file_path):
                mtime = os.path.getmtime(self.calib_file_path)
                if mtime != self.last_calib_mtime:
                    with open(self.calib_file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if "calib_left" in data and "25" in data["calib_left"]:
                        self.cached_calib_l5y = int(data["calib_left"]["25"])
                    elif "left" in data and "25" in data["left"]:
                        self.cached_calib_l5y = int(data["left"]["25"])
                    self.last_calib_mtime = mtime
        except Exception:
            pass

        tilt_center = float(self.cached_calib_l5y)

        # ── 0. SCENARIO-AWARE GAINS ADAPTATION ─────────────────────────────────
        # Classify the ball's motion profile into active scenarios
        if abs(error) > 0.02 and abs(velocity) < 0.005 and self.stuck_timer > 0.5:
            self.active_scenario = "STUCK_RECOVERY"
            lookahead = 0.10
        elif abs(error) < 0.02 and abs(velocity) < 0.03:
            self.active_scenario = "FINE_TUNING"
            lookahead = 0.08
        elif abs(error) > 0.08 and error * velocity >= 0:
            self.active_scenario = "EMERGENCY_RETRIEVE"
            lookahead = 0.12
        elif error * velocity < -0.005 and abs(velocity) > 0.05:
            self.active_scenario = "PREEMPTIVE_BRAKING"
            lookahead = 0.16  # tilt-back early to slow the ball down
        else:
            self.active_scenario = "NOMINAL"
            lookahead = 0.10

        # ── 1. COMPUTE PID GAINS (SELF-TUNED OR NOMINAL MANUAL) ────────────────
        if self.auto_tune_enabled:
            # Set target frequency omega_n based on active scenario
            if self.active_scenario == "FINE_TUNING":
                omega_n = 2.5 * self.speed_multiplier
            elif self.active_scenario == "EMERGENCY_RETRIEVE":
                omega_n = 4.5 * self.speed_multiplier
            elif self.active_scenario == "PREEMPTIVE_BRAKING":
                omega_n = 3.0 * self.speed_multiplier
            else:
                omega_n = 3.2 * self.speed_multiplier
            
            # Analytic critical damping gains
            self.kp = (omega_n * omega_n) / self.est_a
            self.kd = (2.0 * omega_n + self.est_b) / self.est_a
            
            # Clamp to safe bounds to prevent wild behavior
            self.kp = max(0.4, min(2.8, self.kp))
            self.kd = max(0.15, min(1.2, self.kd))
            
            # Convert gains to match standard controller scale
            kp_eff = (100.0 * self.kp) / (650.0 * self.speed_multiplier)
            kd_eff = (100.0 * self.kd) / (650.0 * self.speed_multiplier)
            ki_eff = self.ki
        else:
            # Manual Mode: Scale gains according to scenario
            if self.active_scenario == "STUCK_RECOVERY":
                kp_eff = self.kp
                kd_eff = self.kd
                ki_eff = self.ki * 1.5
            elif self.active_scenario == "FINE_TUNING":
                kp_eff = self.kp * 0.8
                kd_eff = self.kd * 1.5
                ki_eff = self.ki * 1.5
            elif self.active_scenario == "EMERGENCY_RETRIEVE":
                kp_eff = self.kp * 1.6
                kd_eff = self.kd * 1.4
                ki_eff = self.ki
            elif self.active_scenario == "PREEMPTIVE_BRAKING":
                kp_eff = self.kp * 0.7
                kd_eff = self.kd * 1.3
                ki_eff = self.ki
            else:
                kp_eff = self.kp
                kd_eff = self.kd
                ki_eff = self.ki

        # ── 2. PREDICTIVE ERROR ──────────────────────────────────────────────
        predicted_error = error + velocity * lookahead

        # ── 3. PD ON PREDICTED STATE ─────────────────────────────────────────
        p_term = predicted_error * kp_eff
        d_term = velocity        * kd_eff

        # Tiny integral only to cancel slow physical slope drift
        self.integral += error * dt
        self.integral  = max(-0.15, min(0.15, self.integral))
        i_term = self.integral * ki_eff

        # Scale 650 — sufficient authority without violent jerking
        correction = -(p_term + d_term + i_term) * 650.0 * self.speed_multiplier

        # ── 4. GENTLE ADAPTIVE BIAS ──────────────────────────────────────────
        # Background correction for physical plate incline. Rate 200× is
        # deliberately slow so it doesn't fight the PD term or cause overshoot.
        is_centered = abs(error) < 0.008

        if is_centered:
            # Maintain active integral and adaptive bias to hold the plate level
            self.stuck_timer    = 0.0
            self.stuck_cooldown = 0.0
        else:
            if self.stuck_cooldown > 0.0:
                self.stuck_cooldown = max(0.0, self.stuck_cooldown - dt)

            moving_toward_center = (error > 0 and velocity < -0.005) or (error < 0 and velocity > 0.005)
            if not moving_toward_center:
                self.adaptive_tilt -= 200.0 * error * dt

            self.adaptive_tilt = max(-self.max_tilt_negative * 0.5,
                                     min(self.max_tilt_positive * 0.5, self.adaptive_tilt))

            if self.stuck_cooldown <= 0.0:
                if abs(error) > self.stuck_err_threshold and abs(velocity) < self.stuck_vel_threshold:
                    self.stuck_timer += dt
                else:
                    self.stuck_timer = 0.0

                if self.stuck_timer >= self.stuck_time_limit:
                    logger.log(
                        f"Ball Balancer: Stuck ball (err={error:.3f}m, vel={velocity:.4f}m/s) "
                        "– resetting bias.", "WARNING"
                    )
                    self.adaptive_tilt  = 0.0
                    self.integral       = 0.0
                    self.stuck_timer    = 0.0
                    self.stuck_cooldown = self.stuck_cooldown_dur

        if self.invert_output:
            target_tilt = tilt_center - (correction + self.adaptive_tilt)
        else:
            target_tilt = tilt_center + correction + self.adaptive_tilt

        # ── 5. BACKLASH COMPENSATION ─────────────────────────────────────────
        backlash_comp = 0.0
        if self.last_target_tilt is not None:
            diff = target_tilt - self.last_target_tilt
            if diff > 0.5:
                if self.last_commanded_dir == -1:
                    backlash_comp = 15.0
                self.last_commanded_dir = 1
            elif diff < -0.5:
                if self.last_commanded_dir == 1:
                    backlash_comp = -15.0
                self.last_commanded_dir = -1

        self.last_target_tilt = target_tilt
        target_tilt += backlash_comp

        # ── 6. PHYSICAL CLAMP ────────────────────────────────────────────────
        target_tilt = max(tilt_center - self.max_tilt_negative,
                          min(tilt_center + self.max_tilt_positive, target_tilt))

        # Update last applied tilt for next iteration's system identification
        self.last_applied_tilt = float(target_tilt - tilt_center)

        # ── DATA LOGGING & DISK PERSISTENCE (5Hz / 5s) ────────────────────────
        if not hasattr(self, "_log_frame_counter"):
            self._log_frame_counter = 0
        self._log_frame_counter += 1
        
        if self._log_frame_counter >= 6:
            self._log_frame_counter = 0
            now = time.time()
            log_entry = {
                "timestamp": now,
                "error": float(error),
                "velocity": float(velocity),
                "tilt": float(self.last_applied_tilt),
                "acc": float(acc),
                "kp": float(self.kp),
                "kd": float(self.kd),
                "est_a": float(self.est_a),
                "est_b": float(self.est_b)
            }
            self.learning_history.append(log_entry)
            if len(self.learning_history) > 100:
                self.learning_history.pop(0)
                
            if now - self.last_save_time >= 5.0:
                self.last_save_time = now
                self._save_learning_data()

        self.event_bus.publish("balancer_frame", {
            "ball_y": state["y"],
            "ball_vy": state["vy"],
            "target_y": self.target_y,
            "delta_z": float(target_tilt),
            "confidence": state["confidence"],
            "ball_error": float(state["y"] / 0.22),
            "active_scenario": self.active_scenario,
            "est_a": self.est_a,
            "est_b": self.est_b,
            "auto_tune_enabled": self.auto_tune_enabled,
            "loadcell_c0": self.loadcell_c0,
            "loadcell_c1": self.loadcell_c1,
            "loadcell_c2": self.loadcell_c2,
            "loadcell_c3": self.loadcell_c3,
            "loadcell_mode": self.loadcell_mode,
            "loadcell_arm": self.loadcell_arm,
            "ball_weight_ref": self.ball_weight_ref,
            "avg_mapping_error": self.avg_mapping_error,
            "invert_output": self.invert_output,
            "ball_type": self.ball_type,
            "exploration_mode": self.exploration_mode,
            "exploration_progress": float(self.balanced_time / 1.5) if self.exploration_mode else 0.0
        })

        return float(target_tilt)


    def step(self, dt: float) -> Optional[Dict[str, Any]]:
        """
        Executes a single step of the balancer task.
        Returns target plate offset to be applied to the active robot.
        """
        if not self.is_active:
            self.integral = 0.0
            self.adaptive_tilt = 0.0
            self.last_target_tilt = None
            self.last_commanded_dir = 0
            self.smoothed_tilt = None
            self.stuck_timer = 0.0
            self.stuck_cooldown = 0.0
            return None
        delta_z = self.update_controller(dt)
        return {"offsets": {"plate_balance": delta_z}}

