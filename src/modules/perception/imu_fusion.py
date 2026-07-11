import random
from typing import Dict, List, Any

class ImuFusion:
    """
    Perception plugin representing dynamic IMU sensor fusion.
    """
    def __init__(self):
        self.orientation = [0.0, 0.0, 0.0] # Roll, Pitch, Yaw

    def get_orientation(self) -> List[float]:
        # Tiny noise around zero rotation
        return [random.uniform(-0.01, 0.01) for _ in range(3)]

    def get_telemetry(self) -> Dict[str, Any]:
        roll, pitch, yaw = self.get_orientation()
        return {
            "imu_roll": roll,
            "imu_pitch": pitch,
            "imu_yaw": yaw,
            "linear_accel_g": [0.0, 0.0, 1.0] # Z gravity vector
        }
