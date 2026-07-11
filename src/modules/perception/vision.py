from typing import Tuple, Optional, Any
import numpy as np
import logging

# Import hand_tracker from main path
from hand_tracker import HandTracker
# Import RealSense background tracker thread
from src.modules.perception.realsense_vision import RealSenseTrackerThread

class VisionPerception:
    """
    Unified perception module supporting both MediaPipe HandTracker
    and Intel RealSense D415 ball/plate tracking.
    """
    def __init__(self, camera_index: int = 0):
        self.camera_index = camera_index
        self.mode = "realsense"  # default to realsense for ball balancing
        self.tracker: Optional[Any] = None

    def start(self, camera_index: int = 0) -> bool:
        self.camera_index = camera_index
        if self.tracker is not None:
            self.tracker.stop()
            self.tracker = None
            
        if self.mode == "realsense":
            logging.info(f"Starting RealSense tracker thread on Camera Index {self.camera_index}...")
            self.tracker = RealSenseTrackerThread(camera_index=self.camera_index)
        else:
            logging.info(f"Starting MediaPipe HandTracker thread on Camera Index {self.camera_index}...")
            self.tracker = HandTracker(camera_index=self.camera_index)
            
        return self.tracker.start()

    def stop(self):
        if self.tracker is not None:
            self.tracker.stop()
            self.tracker = None

    def get_latest_data(self) -> Tuple[Optional[np.ndarray], Optional[Any], Optional[Any], float]:
        """Returns (annotated_frame, tracker_data, world_landmarks, fps)."""
        if self.tracker is None:
            return None, None, None, 0.0
        return self.tracker.get_latest_data()

    def get_latest_base64_frame(self) -> Optional[str]:
        """Returns the pre-encoded base64 JPEG string of the latest frame."""
        if self.tracker is None:
            return None
        return self.tracker.get_latest_base64_frame()

    def is_active(self) -> bool:
        # Check running state based on tracker thread presence
        if self.tracker is None:
            return False
        # Both trackers have 'running' flag
        return getattr(self.tracker, "running", False)

    def set_mode(self, mode: str):
        """Sets the mode dynamically and restarts the tracker if running."""
        if mode not in ["realsense", "hand_tracker"]:
            return
        if self.mode == mode:
            return
            
        logging.info(f"VisionPerception changing tracking mode from '{self.mode}' to '{mode}'")
        self.mode = mode
        if self.is_active():
            self.start(self.camera_index)
