import os
import json
import logging
import numpy as np
from typing import Dict, List, Any

from src.modules.robots.base_robot import BaseRobot

class LeapHandRobot(BaseRobot):
    """
    Robot plugin representing the LEAP Hand (V1 with 16 motors, or V2 with 8 motors).
    """
    def __init__(self, version: str = "V1"):
        super().__init__(name="LEAP Hand", version=version)
        self._init_default_limits()
        self.load_config()

    def _init_default_limits(self):
        if self.version == "V1":
            self.limits = {
                0:  {"name": "Index Abduct", "min": 2048, "max": 2500, "default": 2048},
                1:  {"name": "Index MCP",    "min": 2048, "max": 3000, "default": 2048},
                2:  {"name": "Index PIP",    "min": 2048, "max": 3200, "default": 2048},
                3:  {"name": "Ring MCP",     "min": 2048, "max": 3000, "default": 2048},
                4:  {"name": "Middle Abduct","min": 2048, "max": 2500, "default": 2048},
                5:  {"name": "Middle MCP",   "min": 2048, "max": 3000, "default": 2048},
                6:  {"name": "Middle PIP",   "min": 2048, "max": 3200, "default": 2048},
                7:  {"name": "Middle DIP",   "min": 2048, "max": 3200, "default": 2048},
                8:  {"name": "Ring Abduct",  "min": 2048, "max": 2500, "default": 2048},
                9:  {"name": "Index DIP",    "min": 2048, "max": 3200, "default": 2048},
                10: {"name": "Ring PIP",     "min": 2048, "max": 3200, "default": 2048},
                11: {"name": "Ring DIP",     "min": 2048, "max": 3200, "default": 2048},
                12: {"name": "Thumb Abduct", "min": 2048, "max": 3200, "default": 2048},
                13: {"name": "Thumb MCP",    "min": 2048, "max": 3000, "default": 2048},
                14: {"name": "Thumb PIP",    "min": 2048, "max": 3200, "default": 2048},
                15: {"name": "Thumb DIP",    "min": 2048, "max": 3200, "default": 2048},
            }
        else:
            self.limits = {
                0:  {"name": "Index Abduct",  "min": 2048, "max": 2500, "default": 2048},
                1:  {"name": "Index Curl",    "min": 2048, "max": 3200, "default": 2048},
                2:  {"name": "Middle Abduct", "min": 2048, "max": 2500, "default": 2048},
                3:  {"name": "Middle Curl",   "min": 2048, "max": 3200, "default": 2048},
                4:  {"name": "Ring Abduct",   "min": 2048, "max": 2500, "default": 2048},
                5:  {"name": "Ring Curl",     "min": 2048, "max": 3200, "default": 2048},
                6:  {"name": "Thumb Abduct",  "min": 2048, "max": 3200, "default": 2048},
                7:  {"name": "Thumb Curl",    "min": 2048, "max": 3200, "default": 2048},
            }

    def load_config(self):
        filename = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "osrs_config.json")
        if not os.path.exists(filename):
            return
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
            profile_name = self.version
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
            "asset_path": "assets/leap_hand.urdf",
            "visual_offsets": {"x": 0.0, "y": 0.0, "z": 0.0}
        }

    def process_pose(self, landmarks: Any) -> Dict[int, int]:
        if landmarks is None:
            return {mid: info["default"] for mid, info in self.get_joint_layout().items()}
            
        single_hand = landmarks[0]["landmarks"] if (isinstance(landmarks, list) and len(landmarks) > 0) else landmarks
        if hasattr(single_hand, "landmark"):
            points = np.array([[lm.x, lm.y, lm.z] for lm in single_hand.landmark])
        else:
            points = np.array([[lm.x, lm.y, lm.z] for lm in single_hand])

        # Index Curl
        idx_mcp, idx_pip, idx_dip, idx_tip = points[5], points[6], points[7], points[8]
        idx_len = np.linalg.norm(idx_pip - idx_mcp) + np.linalg.norm(idx_dip - idx_pip) + np.linalg.norm(idx_tip - idx_dip)
        idx_dist = np.linalg.norm(idx_tip - idx_mcp)
        idx_ratio = np.clip(idx_dist / max(idx_len, 0.001), 0.3, 1.0)
        idx_curl = 1.0 - ((idx_ratio - 0.3) / 0.7)

        # Middle Curl
        mid_mcp, mid_pip, mid_dip, mid_tip = points[9], points[10], points[11], points[12]
        mid_len = np.linalg.norm(mid_pip - mid_mcp) + np.linalg.norm(mid_dip - mid_pip) + np.linalg.norm(mid_tip - mid_dip)
        mid_dist = np.linalg.norm(mid_tip - mid_mcp)
        mid_ratio = np.clip(mid_dist / max(mid_len, 0.001), 0.3, 1.0)
        mid_curl = 1.0 - ((mid_ratio - 0.3) / 0.7)

        # Ring Curl
        rng_mcp, rng_pip, rng_dip, rng_tip = points[13], points[14], points[15], points[16]
        rng_len = np.linalg.norm(rng_pip - rng_mcp) + np.linalg.norm(rng_dip - rng_pip) + np.linalg.norm(rng_tip - rng_dip)
        rng_dist = np.linalg.norm(rng_tip - rng_mcp)
        rng_ratio = np.clip(rng_dist / max(rng_len, 0.001), 0.3, 1.0)
        rng_curl = 1.0 - ((rng_ratio - 0.3) / 0.7)

        # Thumb Curl
        thb_mcp, thb_pip, thb_dip, thb_tip = points[2], points[3], points[4], points[4]
        thb_len = np.linalg.norm(thb_pip - thb_mcp) + np.linalg.norm(thb_tip - thb_pip)
        thb_dist = np.linalg.norm(thb_tip - thb_mcp)
        thb_ratio = np.clip(thb_dist / max(thb_len, 0.001), 0.4, 1.0)
        thb_curl = 1.0 - ((thb_ratio - 0.4) / 0.6)

        thb_mcp_len = np.linalg.norm(points[2] - points[1]) + np.linalg.norm(points[3] - points[2])
        thb_mcp_dist = np.linalg.norm(points[3] - points[1])
        thb_mcp_ratio = np.clip(thb_mcp_dist / max(thb_mcp_len, 0.001), 0.7, 1.0)
        thb_mcp_curl = 1.0 - ((thb_mcp_ratio - 0.7) / 0.3)

        thb_ip_len = np.linalg.norm(points[3] - points[2]) + np.linalg.norm(points[4] - points[3])
        thb_ip_dist = np.linalg.norm(points[4] - points[2])
        thb_ip_ratio = np.clip(thb_ip_dist / max(thb_ip_len, 0.001), 0.6, 1.0)
        thb_pip_dip_curl = 1.0 - ((thb_ip_ratio - 0.6) / 0.4)

        # Index Abduction
        idx_vec = idx_mcp - points[0]
        mid_vec = mid_mcp - points[0]
        denom_idx_mid = np.linalg.norm(idx_vec) * np.linalg.norm(mid_vec)
        angle_idx_mid = np.arccos(np.clip(np.dot(idx_vec, mid_vec) / (denom_idx_mid + 1e-6), -1.0, 1.0))
        idx_abd = np.clip((angle_idx_mid - 0.05) / 0.20, 0.0, 1.0)

        mid_abd = 0.5
        
        # Ring Abduction
        rng_vec = rng_mcp - points[0]
        denom_rng_mid = np.linalg.norm(rng_vec) * np.linalg.norm(mid_vec)
        angle_rng_mid = np.arccos(np.clip(np.dot(rng_vec, mid_vec) / (denom_rng_mid + 1e-6), -1.0, 1.0))
        rng_abd = np.clip((angle_rng_mid - 0.05) / 0.20, 0.0, 1.0)

        pinky_mcp = points[17] if len(points) > 17 else points[13]
        v_lateral = pinky_mcp - points[5]
        palm_width = np.linalg.norm(v_lateral)
        if palm_width > 0.001:
            v_lateral_dir = v_lateral / palm_width
            v_thumb = points[4] - points[5]
            norm_proj = np.dot(v_thumb, v_lateral_dir) / palm_width
            thb_abd = np.clip((norm_proj - (-1.2)) / 1.8, 0.0, 1.0)
        else:
            thb_abd = 0.5

        targets = {}
        if self.version == "V1":
            targets[0] = self._interpolate(idx_abd, self.limits[0])
            targets[1] = self._interpolate(idx_curl, self.limits[1])
            targets[2] = self._interpolate(idx_curl, self.limits[2])
            targets[9] = self._interpolate(idx_curl, self.limits[9])
            
            targets[4] = self._interpolate(mid_abd, self.limits[4])
            targets[5] = self._interpolate(mid_curl, self.limits[5])
            targets[6] = self._interpolate(mid_curl, self.limits[6])
            targets[7] = self._interpolate(mid_curl, self.limits[7])
            
            targets[8] = self._interpolate(rng_abd, self.limits[8])
            targets[3] = self._interpolate(rng_curl, self.limits[3])
            targets[10] = self._interpolate(rng_curl, self.limits[10])
            targets[11] = self._interpolate(rng_curl, self.limits[11])
            
            targets[12] = self._interpolate(1.0 - thb_abd, self.limits[12])
            targets[13] = self._interpolate(thb_mcp_curl, self.limits[13])
            targets[14] = self._interpolate(thb_pip_dip_curl, self.limits[14])
            targets[15] = self._interpolate(thb_pip_dip_curl, self.limits[15])
        else:
            targets[0] = self._interpolate(idx_abd, self.limits[0])
            targets[1] = self._interpolate(idx_curl, self.limits[1])
            targets[2] = self._interpolate(mid_abd, self.limits[2])
            targets[3] = self._interpolate(mid_curl, self.limits[3])
            targets[4] = self._interpolate(rng_abd, self.limits[4])
            targets[5] = self._interpolate(rng_curl, self.limits[5])
            targets[6] = self._interpolate(1.0 - thb_abd, self.limits[6])
            targets[7] = self._interpolate(thb_pip_dip_curl, self.limits[7])
            
        return targets

    def _interpolate(self, val: float, limit_dict: dict) -> int:
        res = limit_dict["min"] + val * (limit_dict["max"] - limit_dict["min"])
        return int(np.clip(res, 0, 4095))
