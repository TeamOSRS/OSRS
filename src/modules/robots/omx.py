import os
import json
import numpy as np
from typing import Dict, List, Any

from src.modules.robots.base_robot import BaseRobot

class OMXRobot(BaseRobot):
    """
    Robot plugin representing the Open Manipulator X robot arm.
    """
    def __init__(self):
        super().__init__(name="Open Manipulator X", version="Open Manipulator X")
        self._init_default_limits()
        self.load_config()

    def _init_default_limits(self):
        self.limits = {
            11: {"name": "Joint 1 - Yaw",      "min": 0,    "max": 4095, "default": 2048},
            12: {"name": "Joint 2 - Shoulder", "min": 1024, "max": 3072, "default": 2048},
            13: {"name": "Joint 3 - Elbow",    "min": 1024, "max": 3072, "default": 2048},
            14: {"name": "Joint 4 - Wrist",    "min": 1024, "max": 3072, "default": 2048},
            15: {"name": "Joint 5 - Gripper",  "min": 1024, "max": 3072, "default": 2048},
        }

    def load_config(self):
        filename = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "osrs_config.json")
        if not os.path.exists(filename):
            return
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
            profile_name = "Open Manipulator X"
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
            "asset_path": "assets/open_manipulator_x.urdf",
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
            
            hand_center_x = np.mean(pts[:, 0])
            hand_center_y = np.mean(pts[:, 1])
            
            yaw_val = np.clip(hand_center_x, 0.0, 1.0)
            targets[11] = self._interpolate(yaw_val, self.limits[11])
            
            pitch_val = np.clip(1.0 - hand_center_y, 0.0, 1.0)
            targets[12] = self._interpolate(pitch_val, self.limits[12])
            
            curls = self.extract_curls(lms)
            if curls is not None:
                idx_curl, mid_curl, rng_curl, thb_curl, pinch_dist = curls
                targets[13] = self._interpolate(1.0 - idx_curl, self.limits[13])
                targets[14] = self._interpolate(1.0 - mid_curl, self.limits[14])
                gripper_val = np.clip((pinch_dist - 0.15) / 0.55, 0.0, 1.0)
                targets[15] = self._interpolate(gripper_val, self.limits[15])
        return targets

    def _interpolate(self, val: float, limit_dict: dict) -> int:
        res = limit_dict["min"] + val * (limit_dict["max"] - limit_dict["min"])
        return int(np.clip(res, 0, 4095))

    def extract_curls(self, landmarks):
        if hasattr(landmarks, "landmark"):
            points = np.array([[lm.x, lm.y, lm.z] for lm in landmarks.landmark])
        else:
            points = np.array([[lm.x, lm.y, lm.z] for lm in landmarks])

        # Index Curl
        idx_mcp, idx_pip, idx_dip, idx_tip = points[5], points[6], points[7], points[8]
        idx_len = np.linalg.norm(idx_pip - idx_mcp) + np.linalg.norm(idx_dip - idx_pip) + np.linalg.norm(idx_tip - idx_dip)
        idx_dist = np.linalg.norm(idx_tip - idx_mcp)
        idx_ratio = np.clip(idx_dist / max(idx_len, 0.01), 0.3, 1.0)
        idx_curl = 1.0 - ((idx_ratio - 0.3) / 0.7)

        # Middle Curl
        mid_mcp, mid_pip, mid_dip, mid_tip = points[9], points[10], points[11], points[12]
        mid_len = np.linalg.norm(mid_pip - mid_mcp) + np.linalg.norm(mid_dip - mid_pip) + np.linalg.norm(mid_tip - mid_dip)
        mid_dist = np.linalg.norm(mid_tip - mid_mcp)
        mid_ratio = np.clip(mid_dist / max(mid_len, 0.01), 0.3, 1.0)
        mid_curl = 1.0 - ((mid_ratio - 0.3) / 0.7)

        # Ring Curl
        rng_mcp, rng_pip, rng_dip, rng_tip = points[13], points[14], points[15], points[16]
        rng_len = np.linalg.norm(rng_pip - rng_mcp) + np.linalg.norm(rng_dip - rng_pip) + np.linalg.norm(rng_tip - rng_dip)
        rng_dist = np.linalg.norm(rng_tip - rng_mcp)
        rng_ratio = np.clip(rng_dist / max(rng_len, 0.01), 0.3, 1.0)
        rng_curl = 1.0 - ((rng_ratio - 0.3) / 0.7)

        # Thumb Curl
        thb_mcp, thb_pip, thb_dip, thb_tip = points[2], points[3], points[4], points[4]
        thb_len = np.linalg.norm(thb_pip - thb_mcp) + np.linalg.norm(thb_tip - thb_pip)
        thb_dist = np.linalg.norm(thb_tip - thb_mcp)
        thb_ratio = np.clip(thb_dist / max(thb_len, 0.01), 0.4, 1.0)
        thb_curl = 1.0 - ((thb_ratio - 0.4) / 0.6)

        pinch_dist = np.linalg.norm(points[4] - points[8]) / max(idx_len, 0.01)
        return idx_curl, mid_curl, rng_curl, thb_curl, pinch_dist
