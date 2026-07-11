import os
import json
import numpy as np
from typing import Dict, List, Any

from src.modules.robots.base_robot import BaseRobot

class RoverRobot(BaseRobot):
    """
    Robot plugin representing the Rover Bot platform (differential drive chassis).
    """
    def __init__(self):
        super().__init__(name="Rover Bot", version="Rover Bot")
        self._init_default_limits()
        self.load_config()

    def _init_default_limits(self):
        self.limits = {
            41: {"name": "L Front Drive",  "min": 1024, "max": 3072, "default": 2048},
            42: {"name": "L Mid Drive",    "min": 1024, "max": 3072, "default": 2048},
            43: {"name": "L Rear Drive",   "min": 1024, "max": 3072, "default": 2048},
            44: {"name": "R Front Drive",  "min": 1024, "max": 3072, "default": 2048},
            45: {"name": "R Mid Drive",    "min": 1024, "max": 3072, "default": 2048},
            46: {"name": "R Rear Drive",   "min": 1024, "max": 3072, "default": 2048},
        }

    def load_config(self):
        filename = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "osrs_config.json")
        if not os.path.exists(filename):
            return
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
            profile_name = "Rover Bot"
            if profile_name in data:
                profile_limits = {}
                for k, v in data[profile_name].items():
                    profile_limits[int(k)] = v
                self.limits = profile_limits
        except Exception as e:
            pass

    def get_digital_twin_model(self) -> Dict[str, Any]:
        return {
            "asset_type": "URDF",
            "asset_path": "assets/rover.urdf",
            "visual_offsets": {"x": 0.0, "y": 0.0, "z": 0.0}
        }

    def process_pose(self, landmarks: Any) -> Dict[int, int]:
        targets = {mid: info["default"] for mid, info in self.limits.items()}
        if landmarks is None:
            return targets
            
        hand_list = landmarks if isinstance(landmarks, list) else [{"landmarks": landmarks, "handedness": "Right"}]
        if len(hand_list) > 0:
            lms = hand_list[0]["landmarks"]
            if hasattr(lms, "landmark"):
                pts = np.array([[lm.x, lm.y, lm.z] for lm in lms.landmark])
            else:
                pts = np.array([[lm.x, lm.y, lm.z] for lm in lms])
            
            hand_center_x = np.mean(pts[:, 0]) # 0.0 (left) to 1.0 (right)
            hand_center_y = np.mean(pts[:, 1]) # 0.0 (top) to 1.0 (bottom)
            
            throttle = np.clip(1.0 - hand_center_y, 0.0, 1.0)
            steering = np.clip(hand_center_x, 0.0, 1.0)
            
            left_speed = np.clip(throttle + (steering - 0.5), 0.0, 1.0)
            right_speed = np.clip(throttle - (steering - 0.5), 0.0, 1.0)
            
            for mid in [41, 42, 43]:
                targets[mid] = self._interpolate(left_speed, self.limits[mid])
            for mid in [44, 45, 46]:
                targets[mid] = self._interpolate(right_speed, self.limits[mid])
        return targets

    def _interpolate(self, val: float, limit_dict: dict) -> int:
        res = limit_dict["min"] + val * (limit_dict["max"] - limit_dict["min"])
        return int(np.clip(res, 0, 4095))
