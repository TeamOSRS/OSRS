from typing import Dict, List, Any, Optional

class JointDescription:
    """
    Structured representation of a single robot joint/actuator.
    """
    def __init__(self, id: int, name: str, min_limit: float, max_limit: float, default_val: float):
        self.id = id
        self.name = name
        self.min_limit = min_limit
        self.max_limit = max_limit
        self.default_val = default_val

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "min_limit": self.min_limit,
            "max_limit": self.max_limit,
            "default_val": self.default_val
        }


class ControlModelDescription:
    """
    Control model specification derived from the simulation_ref validated parameters.
    """
    def __init__(self, coordinate_system: str, kinematics: str, joint_ranges: Dict[int, List[float]], pid_gains: Dict[str, float], xml_scene: Optional[str] = None):
        self.coordinate_system = coordinate_system # e.g. "MuJoCo", "ENU", "NED"
        self.kinematics = kinematics               # e.g. "DualArm7DOF_IK", "RoverDifferential"
        self.joint_ranges = joint_ranges           # mappings from motor ID to [min, max]
        self.pid_gains = pid_gains                 # default gains: kp, ki, kd
        self.xml_scene = xml_scene                 # path to simulated environment scene (if any)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "coordinate_system": self.coordinate_system,
            "kinematics": self.kinematics,
            "joint_ranges": {str(k): v for k, v in self.joint_ranges.items()},
            "pid_gains": self.pid_gains,
            "xml_scene": self.xml_scene
        }


class VisualAssetDescription:
    """
    Visual model representation for asset loading in the Digital Twin, independent of kinematics.
    """
    def __init__(self, asset_type: str, path: str, offsets: Dict[str, float], scale: float = 1.0):
        self.asset_type = asset_type   # "MJCF", "URDF", "GLTF", "GLB"
        self.path = path               # path to asset file
        self.offsets = offsets         # translation offsets {x, y, z}
        self.scale = scale             # uniform scaling factor

    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset_type": self.asset_type,
            "path": self.path,
            "offsets": self.offsets,
            "scale": self.scale
        }


class RobotDescription:
    """
    Aggregated robot description container serving as the single source of truth
    for a robot's properties and structures.
    """
    def __init__(self, name: str, version: str, joints: List[JointDescription], control_model: ControlModelDescription, visual_model: VisualAssetDescription):
        self.name = name
        self.version = version
        self.joints = joints
        self.control_model = control_model
        self.visual_model = visual_model

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "joints": [j.to_dict() for j in self.joints],
            "control_model": self.control_model.to_dict(),
            "visual_model": self.visual_model.to_dict()
        }
