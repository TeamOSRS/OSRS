import os
import json
import logging
from typing import Dict, List, Any

# Modular robot plugins
from src.modules.robots.leap_hand import LeapHandRobot
from src.modules.robots.humanoid import HumanoidRobot
from src.modules.robots.omx import OMXRobot
from src.modules.robots.rover import RoverRobot
from src.modules.robots.base_robot import BaseRobot

class PoseMapper:
    """
    Backwards-compatible wrapper delegating core operations to modular robot plugins.
    """
    def __init__(self, hand_version="V1"):
        self.hand_version = hand_version
        self._init_robot()

    def _init_robot(self):
        if self.hand_version in ["V1", "V2"]:
            self.robot = LeapHandRobot(version=self.hand_version)
        elif self.hand_version == "Humanoid V1":
            self.robot = HumanoidRobot()
        elif self.hand_version == "Open Manipulator X":
            self.robot = OMXRobot()
        elif self.hand_version == "Rover Bot":
            self.robot = RoverRobot()
        else:
            self.robot = BaseRobot(self.hand_version, self.hand_version)

    def map_landmarks_to_ticks(self, landmarks) -> Dict[int, int]:
        return self.robot.process_pose(landmarks)

    def get_motor_limits(self) -> Dict[int, Dict[str, Any]]:
        return self.robot.get_joint_layout()

    def set_motor_limit(self, motor_id: int, limit_type: str, value: int):
        self.robot.limits[int(motor_id)][limit_type] = int(value)
        self.save_config()

    def save_config(self):
        # Delegate config saving back to robot
        if hasattr(self.robot, "save_config"):
            self.robot.save_config()
        else:
            # Fallback direct save logic
            filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), "osrs_config.json")
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    data = json.load(f)
                data[self.hand_version] = {str(k): v for k, v in self.robot.limits.items()}
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4)
            except Exception:
                pass

    def classify_gesture(self, landmarks) -> Optional[str]:
        # Gestures classification is LeapHand-specific
        if isinstance(self.robot, LeapHandRobot):
            # Extract curls
            curls = self.robot.extract_curls(landmarks)
            if curls is None:
                return None
            idx_curl, mid_curl, rng_curl, thb_curl, pinch_dist = curls
            if pinch_dist < 0.28 and mid_curl > 0.75 and rng_curl > 0.75:
                return "Pinch"
            if thb_curl < 0.45 and idx_curl > 0.75 and mid_curl > 0.75 and rng_curl > 0.75:
                return "Thumbs Up"
            if idx_curl < 0.4 and mid_curl > 0.75 and rng_curl > 0.75 and thb_curl > 0.65:
                return "Making One"
            if idx_curl < 0.4 and mid_curl < 0.4 and rng_curl > 0.75 and thb_curl > 0.65:
                return "Scissors"
            if idx_curl > 0.75 and mid_curl > 0.75 and rng_curl > 0.75 and thb_curl > 0.65:
                return "Closed Fist"
            if idx_curl < 0.35 and mid_curl < 0.35 and rng_curl < 0.35 and thb_curl < 0.45:
                return "Open Hand"
            if (0.35 <= idx_curl <= 0.8) and (0.35 <= mid_curl <= 0.8) and (0.35 <= rng_curl <= 0.8):
                return "Tiger Claw"
        return None

    def get_preset_ticks(self, gesture_name) -> Dict[int, int]:
        if isinstance(self.robot, LeapHandRobot):
            presets = {
                "Open Hand":   (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.5, 0.5, 0.5, 0.0),
                "Closed Fist": (1.0, 1.0, 1.0, 0.0, 1.0, 1.0, 0.0, 0.5, 0.0, 0.8),
                "Scissors":    (0.0, 0.0, 1.0, 0.0, 1.0, 1.0, 1.0, 0.5, 0.0, 0.8),
                "Making One":  (0.0, 1.0, 1.0, 0.0, 1.0, 1.0, 0.5, 0.5, 0.0, 0.8),
                "Thumbs Up":   (1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.5, 0.0, 0.0),
                "Tiger Claw":  (0.65, 0.65, 0.65, 0.55, 0.55, 0.55, 1.0, 0.5, 1.0, 0.2),
                "Pinch":       (0.5, 1.0, 1.0, 0.4, 0.4, 0.4, 0.2, 0.5, 0.0, 0.4),
            }
            if gesture_name not in presets:
                gesture_name = "Open Hand"
            vals = presets[gesture_name]
            targets = {}
            if self.hand_version == "V1":
                targets[0] = self.robot._interpolate(vals[6], self.robot.limits[0])
                targets[1] = self.robot._interpolate(vals[0], self.robot.limits[1])
                targets[2] = self.robot._interpolate(vals[0], self.robot.limits[2])
                targets[9] = self.robot._interpolate(vals[0], self.robot.limits[9])
                targets[4] = self.robot._interpolate(vals[7], self.robot.limits[4])
                targets[5] = self.robot._interpolate(vals[1], self.robot.limits[5])
                targets[6] = self.robot._interpolate(vals[1], self.robot.limits[6])
                targets[7] = self.robot._interpolate(vals[1], self.robot.limits[7])
                targets[8] = self.robot._interpolate(vals[8], self.robot.limits[8])
                targets[3] = self.robot._interpolate(vals[2], self.robot.limits[3])
                targets[10] = self.robot._interpolate(vals[2], self.robot.limits[10])
                targets[11] = self.robot._interpolate(vals[2], self.robot.limits[11])
                targets[12] = self.robot._interpolate(1.0 - vals[9], self.robot.limits[12])
                targets[13] = self.robot._interpolate(vals[3], self.robot.limits[13])
                targets[14] = self.robot._interpolate(vals[4], self.robot.limits[14])
                targets[15] = self.robot._interpolate(vals[5], self.robot.limits[15])
            else:
                targets[0] = self.robot._interpolate(vals[6], self.robot.limits[0])
                targets[1] = self.robot._interpolate(vals[0], self.robot.limits[1])
                targets[2] = self.robot._interpolate(vals[7], self.robot.limits[2])
                targets[3] = self.robot._interpolate(vals[1], self.robot.limits[3])
                targets[4] = self.robot._interpolate(vals[8], self.robot.limits[4])
                targets[5] = self.robot._interpolate(vals[2], self.robot.limits[5])
                targets[6] = self.robot._interpolate(1.0 - vals[9], self.robot.limits[6])
                targets[7] = self.robot._interpolate(vals[4], self.robot.limits[7])
            return targets
        return {mid: info["default"] for mid, info in self.robot.get_joint_layout().items()}
        
from typing import Optional
