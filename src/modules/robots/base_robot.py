from typing import Dict, List, Any, Optional
from src.core.robot_description import (
    RobotDescription, JointDescription, ControlModelDescription, VisualAssetDescription
)

class BaseRobot:
    """
    Abstract base class defining the standard interface for all robot plugins in OSRS.
    """
    def __init__(self, name: str, version: str):
        self.name = name
        self.version = version
        self.limits: Dict[int, Dict[str, Any]] = {}

    def get_joint_layout(self) -> Dict[int, Dict[str, Any]]:
        """
        Returns the joint limits and defaults for calibration and control.
        Format: { motor_id: {"name": str, "min": int, "max": int, "default": int} }
        """
        return self.limits

    def get_control_model(self) -> Dict[str, Any]:
        """
        Returns control-specific details derived from simulation_ref:
        - Kinematic architecture, coordinate systems, mathematical models, controller parameters (PID/Gravity).
        """
        return {
            "coordinate_system": "ENU",
            "kinematics": "None",
            "pid_gains": {"kp": 200, "ki": 0, "kd": 80}
        }

    def get_digital_twin_model(self) -> Dict[str, Any]:
        """
        Returns the independent visual asset loading specification:
        - Visual file path: URDF/MJCF/GLTF/GLB path.
        - Simplified geometries stubs.
        """
        return {
            "asset_type": "simplified",
            "asset_path": None,
            "visual_offsets": {"x": 0.0, "y": 0.0, "z": 0.0}
        }

    def get_robot_description(self) -> RobotDescription:
        """
        Compiles and returns the unified RobotDescription representation.
        """
        joint_list = []
        for mid, info in self.get_joint_layout().items():
            joint_list.append(
                JointDescription(
                    id=mid,
                    name=info["name"],
                    min_limit=info["min"],
                    max_limit=info["max"],
                    default_val=info["default"]
                )
            )

        ctrl = self.get_control_model()
        ctrl_desc = ControlModelDescription(
            coordinate_system=ctrl.get("coordinate_system", "ENU"),
            kinematics=ctrl.get("kinematics", "None"),
            joint_ranges={mid: [info["min"], info["max"]] for mid, info in self.get_joint_layout().items()},
            pid_gains=ctrl.get("pid_gains", {"kp": 200.0, "ki": 0.0, "kd": 80.0}),
            xml_scene=ctrl.get("xml_scene")
        )

        vis = self.get_digital_twin_model()
        vis_desc = VisualAssetDescription(
            asset_type=vis.get("asset_type", "simplified"),
            path=vis.get("asset_path", ""),
            offsets=vis.get("visual_offsets", {"x": 0.0, "y": 0.0, "z": 0.0}),
            scale=vis.get("scale", 1.0)
        )

        return RobotDescription(
            name=self.name,
            version=self.version,
            joints=joint_list,
            control_model=ctrl_desc,
            visual_model=vis_desc
        )

    def process_pose(self, landmarks: Any) -> Dict[int, int]:
        """
        Maps perception inputs (e.g. MediaPipe landmarks) to raw motor ticks.
        Returns: Dict[motor_id, target_tick]
        """
        return {mid: info["default"] for mid, info in self.get_joint_layout().items()}

    def get_emotes(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Returns a dictionary of named presets/emotes for this robot.
        """
        return {}

    def get_calibration_trajectory(self, active_ids: List[int], start_pose: Dict[int, int], end_pose: Dict[int, int]) -> List[Dict[int, int]]:
        """
        Compiles and returns a safe motion trajectory for joint calibration.
        """
        steps = 100
        trajectory = []
        for i in range(steps):
            t = i / float(steps - 1)
            # Quintic profile
            s = 10 * (t ** 3) - 15 * (t ** 4) + 6 * (t ** 5)
            frame = {}
            for mid in active_ids:
                start = start_pose.get(mid, end_pose.get(mid, 2048))
                end = end_pose.get(mid, 2048)
                frame[mid] = int(start + s * (end - start))
            trajectory.append(frame)
        return trajectory

    def apply_control_offset(self, offset_name: str, value: Any, manual_positions: Dict[int, int]):
        """
        Applies a high-level task/control offset directly to the manual positions dictionary.
        Each robot subclass determines which joints and conversions are used.
        """
        pass

