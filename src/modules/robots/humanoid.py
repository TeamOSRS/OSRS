import os
import json
import numpy as np
from typing import Dict, List, Any

from src.modules.robots.base_robot import BaseRobot

class HumanoidRobot(BaseRobot):
    """
    Robot plugin representing the Humanoid Robot (OP3 bimanual humanoid arm/head).
    """
    def __init__(self):
        super().__init__(name="Humanoid Bot", version="Humanoid V1")
        self._init_default_limits()
        self.load_config()
        self.calib_left = {
            21: -3561, 12: -162, 13: 4344,
            24: 4026, 25: -82, 26: -1019, 27: 2065, 28: -2676
        }
        self.calib_right = {
            11: -1674, 22: 2138, 23: -1275,
            14: 2195, 15: -3, 16: 5117, 17: 2079, 18: 983
        }
        self.load_chiman_calibration()

    def update_limits_from_calibration(self):
        # Reset to base default limits first to avoid cumulative drift
        self._init_default_limits()
        self.load_config()
        
        # Shift Left Arm limits
        for mid, val in self.calib_left.items():
            if mid in self.limits:
                old_default = self.limits[mid].get("default", 2048)
                diff = val - old_default
                self.limits[mid]["default"] = val
                self.limits[mid]["min"] += diff
                self.limits[mid]["max"] += diff

        # Shift Right Arm limits
        for mid, val in self.calib_right.items():
            if mid in self.limits:
                old_default = self.limits[mid].get("default", 2048)
                diff = val - old_default
                self.limits[mid]["default"] = val
                self.limits[mid]["min"] += diff
                self.limits[mid]["max"] += diff

    def load_chiman_calibration(self):
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        filepath = os.path.join(root_dir, "chiman_calibration.json")
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if "calib_left" in data:
                    self.calib_left.update({int(k): int(v) for k, v in data["calib_left"].items()})
                elif "left" in data:
                    self.calib_left.update({int(k): int(v) for k, v in data["left"].items()})
                if "calib_right" in data:
                    self.calib_right.update({int(k): int(v) for k, v in data["calib_right"].items()})
                elif "right" in data:
                    self.calib_right.update({int(k): int(v) for k, v in data["right"].items()})
            except Exception:
                pass
        self.update_limits_from_calibration()

    def save_chiman_calibration(self) -> bool:
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        filepath = os.path.join(root_dir, "chiman_calibration.json")
        try:
            data = {
                "calib_left": {str(k): int(v) for k, v in self.calib_left.items()},
                "calib_right": {str(k): int(v) for k, v in self.calib_right.items()}
            }
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            self.update_limits_from_calibration()
            return True
        except Exception:
            return False

    def _init_default_limits(self):
        self.limits = {
            21: {"name": "L1P", "min": -7657, "max": 535, "default": -3561},
            12: {"name": "L2R", "min": -4258, "max": 3934, "default": -162},
            13: {"name": "L3Y", "min": 248, "max": 8440, "default": 4344},
            24: {"name": "L4F", "min": -3284, "max": 4908, "default": 812},
            25: {"name": "L5Y", "min": -3153, "max": 5039, "default": 943},
            26: {"name": "L6R", "min": -4075, "max": 4117, "default": 21},
            27: {"name": "L7P", "min": -4036, "max": 4156, "default": 60},
            28: {"name": "L8G", "min": -6772, "max": 1420, "default": -2676},
            
            11: {"name": "R1P", "min": -5770, "max": 2422, "default": -1674},
            22: {"name": "R2R", "min": -1958, "max": 6234, "default": 2138},
            23: {"name": "R3Y", "min": -5371, "max": 2821, "default": -1275},
            14: {"name": "R4F", "min": -58, "max": 8134, "default": 4038},
            15: {"name": "R5Y", "min": -5091, "max": 3101, "default": -995},
            16: {"name": "R6R", "min": -19, "max": 8173, "default": 4077},
            17: {"name": "R7P", "min": -4022, "max": 4170, "default": 74},
            18: {"name": "R8G", "min": -3113, "max": 5079, "default": 983},
            
            31: {"name": "Head Yaw (L/R)", "min": -4096, "max": 4096, "default": 0},
            32: {"name": "Head Pitch (U/D)", "min": -4096, "max": 4096, "default": 0},
        }

    def load_config(self):
        filename = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "osrs_config.json")
        if not os.path.exists(filename):
            return
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
            profile_name = "Humanoid V1"
            if profile_name in data:
                profile_limits = {}
                for k, v in data[profile_name].items():
                    profile_limits[int(k)] = v
                self.limits = profile_limits
        except Exception as e:
            pass

    def get_control_model(self) -> Dict[str, Any]:
        return {
            "coordinate_system": "MuJoCo",
            "kinematics": "DualArm7DOF_IK",
            "joint_ranges": {mid: [info["min"], info["max"]] for mid, info in self.limits.items()},
            "xml_scene": "simulation_ref/my_bot_plate_scene.xml",
            "pid_gains": {"kp": 120.0, "ki": 6.0, "kd": 5.0}
        }

    def get_digital_twin_model(self) -> Dict[str, Any]:
        return {
            "asset_type": "MJCF",
            "asset_path": "simulation_ref/my_bot.xml",
            "visual_offsets": {"x": 0.0, "y": 0.0, "z": 0.0}
        }

    def process_pose(self, landmarks: Any) -> Dict[int, int]:
        targets = {mid: info["default"] for mid, info in self.limits.items()}
        hand_list = landmarks if isinstance(landmarks, list) else [{"landmarks": landmarks, "handedness": "Right"}]

        # Head yaw/pitch from primary hand position
        head_yaw_id = 31
        head_pitch_id = 32
        
        if len(hand_list) > 0:
            prim_lms = hand_list[0]["landmarks"]
            if hasattr(prim_lms, "landmark"):
                pts = np.array([[lm.x, lm.y, lm.z] for lm in prim_lms.landmark])
            else:
                pts = np.array([[lm.x, lm.y, lm.z] for lm in prim_lms])
            
            hand_center_x = np.mean(pts[:, 0])
            hand_center_y = np.mean(pts[:, 1])
            
            targets[head_yaw_id] = self._interpolate(hand_center_x, self.limits[head_yaw_id])
            targets[head_pitch_id] = self._interpolate(1.0 - hand_center_y, self.limits[head_pitch_id])

        # Joints alias mapper helper
        alias_map = {
            "Shoulder Pitch": 1,
            "Shoulder Roll": 2,
            "Shoulder Yaw": 3,
            "Elbow Flex": 4,
            "Forearm Yaw": 5,
            "Wrist Roll": 6,
            "Wrist Pitch": 7,
            "Hand Grip": 8
        }
        
        def find_id_by_alias(prefix: str, alias_name: str) -> Optional[int]:
            short_code = f"{prefix}{alias_map[alias_name]}"
            for mid, info in self.limits.items():
                if info["name"].startswith(short_code):
                    return mid
            return None

        for hand_dict in hand_list:
            lms = hand_dict["landmarks"]
            side = hand_dict["handedness"]
            prefix = "L" if side == "Left" else "R"

            # Curls
            if hasattr(lms, "landmark"):
                pts = np.array([[lm.x, lm.y, lm.z] for lm in lms.landmark])
            else:
                pts = np.array([[lm.x, lm.y, lm.z] for lm in lms])

            # Index Curl
            idx_mcp, idx_pip, idx_dip, idx_tip = pts[5], pts[6], pts[7], pts[8]
            idx_len = np.linalg.norm(idx_pip - idx_mcp) + np.linalg.norm(idx_dip - idx_pip) + np.linalg.norm(idx_tip - idx_dip)
            idx_dist = np.linalg.norm(idx_tip - idx_mcp)
            idx_ratio = np.clip(idx_dist / max(idx_len, 0.001), 0.3, 1.0)
            idx_curl = 1.0 - ((idx_ratio - 0.3) / 0.7)

            # Middle Curl
            mid_mcp, mid_pip, mid_dip, mid_tip = pts[9], pts[10], pts[11], pts[12]
            mid_len = np.linalg.norm(mid_pip - mid_mcp) + np.linalg.norm(mid_dip - mid_pip) + np.linalg.norm(mid_tip - mid_dip)
            mid_dist = np.linalg.norm(mid_tip - mid_mcp)
            mid_ratio = np.clip(mid_dist / max(mid_len, 0.001), 0.3, 1.0)
            mid_curl = 1.0 - ((mid_ratio - 0.3) / 0.7)

            # Ring Curl
            rng_mcp, rng_pip, rng_dip, rng_tip = pts[13], pts[14], pts[15], pts[16]
            rng_len = np.linalg.norm(rng_pip - rng_mcp) + np.linalg.norm(rng_dip - rng_pip) + np.linalg.norm(rng_tip - rng_dip)
            rng_dist = np.linalg.norm(rng_tip - rng_mcp)
            rng_ratio = np.clip(rng_dist / max(rng_len, 0.001), 0.3, 1.0)
            rng_curl = 1.0 - ((rng_ratio - 0.3) / 0.7)

            # Thumb Curl
            thb_mcp, thb_pip, thb_dip, thb_tip = pts[2], pts[3], pts[4], pts[4]
            thb_len = np.linalg.norm(thb_pip - thb_mcp) + np.linalg.norm(thb_tip - thb_pip)
            thb_dist = np.linalg.norm(thb_tip - thb_mcp)
            thb_ratio = np.clip(thb_dist / max(thb_len, 0.001), 0.4, 1.0)
            thb_curl = 1.0 - ((thb_ratio - 0.4) / 0.6)

            # Abduction
            idx_vec = idx_mcp - pts[0]
            mid_vec = mid_mcp - pts[0]
            denom_idx_mid = np.linalg.norm(idx_vec) * np.linalg.norm(mid_vec)
            angle_idx_mid = np.arccos(np.clip(np.dot(idx_vec, mid_vec) / (denom_idx_mid + 1e-6), -1.0, 1.0))
            idx_abd = np.clip((angle_idx_mid - 0.05) / 0.20, 0.0, 1.0)

            rng_vec = rng_mcp - pts[0]
            denom_rng_mid = np.linalg.norm(rng_vec) * np.linalg.norm(mid_vec)
            angle_rng_mid = np.arccos(np.clip(np.dot(rng_vec, mid_vec) / (denom_rng_mid + 1e-6), -1.0, 1.0))
            rng_abd = np.clip((angle_rng_mid - 0.05) / 0.20, 0.0, 1.0)

            # Map to target IDs
            id_sp = find_id_by_alias(prefix, "Shoulder Pitch")
            id_sr = find_id_by_alias(prefix, "Shoulder Roll")
            id_sy = find_id_by_alias(prefix, "Shoulder Yaw")
            id_ef = find_id_by_alias(prefix, "Elbow Flex")
            id_fy = find_id_by_alias(prefix, "Forearm Yaw")
            id_wr = find_id_by_alias(prefix, "Wrist Roll")
            id_wp = find_id_by_alias(prefix, "Wrist Pitch")
            id_hg = find_id_by_alias(prefix, "Hand Grip")

            if id_sp is not None:
                targets[id_sp] = self._interpolate(idx_curl, self.limits[id_sp])
            if id_sr is not None:
                targets[id_sr] = self._interpolate(mid_curl, self.limits[id_sr])
            if id_sy is not None:
                targets[id_sy] = self._interpolate(idx_abd, self.limits[id_sy])
            if id_ef is not None:
                targets[id_ef] = self._interpolate(rng_curl, self.limits[id_ef])
            if id_fy is not None:
                targets[id_fy] = self._interpolate(rng_abd, self.limits[id_fy])
            if id_wr is not None:
                targets[id_wr] = self._interpolate(0.5, self.limits[id_wr])
            if id_wp is not None:
                targets[id_wp] = self._interpolate(0.5, self.limits[id_wp])
            if id_hg is not None:
                targets[id_hg] = self._interpolate(thb_curl, self.limits[id_hg])

        return targets

    def _interpolate(self, val: float, limit_dict: dict) -> int:
        res = limit_dict["min"] + val * (limit_dict["max"] - limit_dict["min"])
        return int(np.clip(res, limit_dict["min"], limit_dict["max"]))

    def get_emotes(self) -> Dict[str, List[Dict[str, Any]]]:
        # Emote mappings (modifications are 0-centered offsets or absolute joint tick adjustments)
        return {
            "HI Left": [
                { "delay": 15, "modifications": {"L1P": -3392, "L2R": -3392, "L4F": 3008, "L8G": -4096} },
                { "delay": 5, "modifications": {"L6R": -2592} },
                { "delay": 5, "modifications": {"R6R": 1408} },
                { "delay": 5, "modifications": {"L6R": -2592} },
                { "delay": 5, "modifications": {"R6R": 1408} },
                { "delay": 5, "modifications": {"L6R": -2592} },
                { "delay": 5, "modifications": {"R6R": 1408} },
                { "delay": 15, "modifications": {} }
            ],
            "HI Right": [
                { "delay": 15, "modifications": {"R1P": -3392, "R2R": 3392, "R4F": -3008, "R8G": -4096} },
                { "delay": 5, "modifications": {"R6R": 2592} },
                { "delay": 5, "modifications": {"R6R": -1408} },
                { "delay": 5, "modifications": {"R6R": 2592} },
                { "delay": 5, "modifications": {"R6R": -1408} },
                { "delay": 5, "modifications": {"R6R": 2592} },
                { "delay": 5, "modifications": {"R6R": -1408} },
                { "delay": 15, "modifications": {} }
            ],
            "Namaste": [
                { "delay": 25, "modifications": {
                    "L1P": -992, "R1P": -992,
                    "L2R": -1392, "R2R": 1392,
                    "L3Y": -1792, "R3Y": 1792,
                    "L4F": 3008, "R4F": -3008,
                    "L7P": 0, "R7P": 0,
                    "L8G": -4096, "R8G": -4096
                }},
                { "delay": 15, "modifications": {} },
                { "delay": 25, "modifications": {} }
            ],
            "Clap": [
                { "delay": 15, "modifications": {"L1P": -992, "R1P": -992, "L4F": 1808, "R4F": -1808, "L2R": -2192, "R2R": 2192, "L8G": -4096, "R8G": -4096} },
                { "delay": 4, "modifications": {"L2R": -792, "R2R": 792} },
                { "delay": 4, "modifications": {"L2R": -2192, "R2R": 2192} },
                { "delay": 4, "modifications": {"L2R": -792, "R2R": 792} },
                { "delay": 4, "modifications": {"L2R": -2192, "R2R": 2192} },
                { "delay": 4, "modifications": {"L2R": -792, "R2R": 792} },
                { "delay": 4, "modifications": {"L2R": -2192, "R2R": 2192} },
                { "delay": 15, "modifications": {} }
            ]
        }

    def solve_arm_ik(self, site_name: str, target_pos: np.ndarray, target_quat: np.ndarray, arm_joints: List[str], model: Any, data: Any, current_targets: Dict[str, float], damping=0.03, step_scale=0.5, k_posture=0.001) -> Dict[str, float]:
        """
        Calculates numerical DLS Inverse Kinematics for a 7-DOF arm from simulation_ref.
        """
        try:
            import mujoco
        except ImportError:
            return current_targets

        site_id = model.site(site_name).id
        
        # 1. Load targets into virtual kinematics buffer
        for name in arm_joints:
            qpos_adr = model.joint(name).qposadr[0]
            data.qpos[qpos_adr] = current_targets.get(name, 0.0)
            
        # 2. Update forward position kinematics
        mujoco.mj_fwdPosition(model, data)
        
        # 3. Calculate translation and rotation error
        current_pos = data.site_xpos[site_id].copy()
        current_rot_mat = data.site_xmat[site_id].copy().reshape(3, 3)
        current_quat = np.zeros(4)
        mujoco.mju_mat2Quat(current_quat, current_rot_mat.flatten())
        
        pos_err = target_pos - current_pos
        
        # Quaternion division/error
        w1, x1, y1, z1 = target_quat
        w2, x2, y2, z2 = current_quat
        q_err = np.array([
            w1*w2 - x1*-x2 - y1*-y2 - z1*-z2,
            w1*-x2 + x1*w2 + y1*-z2 - z1*-y2,
            w1*-y2 - x1*-z2 + y1*w2 + z1*-x2,
            w1*-z2 + x1*-y2 - y1*-x2 + z1*w2
        ])
        rot_err = 2.0 * q_err[1:4] * np.sign(q_err[0])
        dx = np.concatenate([pos_err, rot_err])
        
        # 4. Read Jacobian
        jacp = np.zeros((3, model.nv))
        jacr = np.zeros((3, model.nv))
        mujoco.mj_jacSite(model, data, jacp, jacr, site_id)
        J = np.vstack([jacp, jacr])
        
        dof_indices = [model.joint(name).dofadr[0] for name in arm_joints]
        J_arm = J[:, dof_indices]
        
        # 5. Solve via Damped Least Squares
        A = J_arm @ J_arm.T + (damping ** 2) * np.eye(6)
        try:
            dq = J_arm.T @ np.linalg.solve(A, dx)
        except np.linalg.LinAlgError:
            dq = J_arm.T @ dx * 0.1
            
        # 6. Apply target adjustments
        updated_targets = current_targets.copy()
        for i, name in enumerate(arm_joints):
            # Regularize towards home pose
            pull = (0.0 - current_targets.get(name, 0.0)) * k_posture
            updated_targets[name] = current_targets.get(name, 0.0) + dq[i] * step_scale + pull
            joint_range = model.joint(name).range
            updated_targets[name] = float(np.clip(updated_targets[name], joint_range[0], joint_range[1]))
            
        return updated_targets

    def apply_control_offset(self, offset_name: str, value: Any, manual_positions: Dict[int, int]):
        if offset_name == "plate_balance":
            # The value returned is the target_tilt position for ID 25
            tilt_val = int(value)
            
            # Compute the delta offset in ticks from Left Forearm Yaw calibration center
            calib_l5y = self.calib_left.get(25, -82)
            delta_ticks = tilt_val - calib_l5y
            
            # 1. Coordinate Wrist Forearm Yaws (L5Y ID 25, R5Y ID 15) to keep hands parallel to plate tilt
            if 25 in manual_positions:
                manual_positions[25] = int(calib_l5y - delta_ticks)
            if 15 in manual_positions:
                calib_r5y = self.calib_right.get(15, -3)
                manual_positions[15] = int(calib_r5y + delta_ticks)
                
            # 2. Coordinate Elbow Forearm Pitch/Flex (L4F ID 24, R4F ID 14) in vertical push-pull drive motion
            if 24 in manual_positions:
                calib_l4f = self.calib_left.get(24, 4026)
                manual_positions[24] = int(calib_l4f - delta_ticks)
            if 14 in manual_positions:
                calib_r4f = self.calib_right.get(14, 2195)
                manual_positions[14] = int(calib_r4f + delta_ticks)


