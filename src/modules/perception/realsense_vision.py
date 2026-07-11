"""
Intel RealSense D415 Vision System for Ball Balancing.
Author: Senior Robotics and Computer Vision Engineer
"""

import sys
import logging
import time
import collections
from typing import Dict, Tuple, List, Optional, Any
import numpy as np
import cv2
import threading
import base64

class MovingAverageFilter:
    """
    A simple moving average filter for smoothing target 3D coordinates.
    """
    def __init__(self, window_size=10):
        self.window_size = max(1, window_size)
        self.history = collections.deque(maxlen=self.window_size)

    def set_window_size(self, size):
        self.window_size = max(1, size)
        old_history = list(self.history)
        self.history = collections.deque(old_history, maxlen=self.window_size)

    def filter(self, x, y, z):
        self.history.append((x, y, z))
        xs = [pt[0] for pt in self.history]
        ys = [pt[1] for pt in self.history]
        zs = [pt[2] for pt in self.history]
        return sum(xs) / len(xs), sum(ys) / len(ys), sum(zs) / len(zs)

    def reset(self):
        self.history.clear()


class KalmanFilter1D:
    """
    A simple 1D Kalman filter to estimate coordinate states.
    """
    def __init__(self, process_noise=1e-4, measurement_noise=1e-2):
        self.Q = process_noise      # Process noise covariance
        self.R = measurement_noise  # Measurement noise covariance
        self.x = None               # Estimated value
        self.P = 1.0                # Estimation error covariance

    def set_parameters(self, process_noise, measurement_noise):
        self.Q = process_noise
        self.R = measurement_noise

    def filter(self, measurement):
        if self.x is None:
            self.x = measurement
            self.P = 1.0
            return self.x

        P_pred = self.P + self.Q
        K = P_pred / (P_pred + self.R)
        self.x = self.x + K * (measurement - self.x)
        self.P = (1.0 - K) * P_pred
        return self.x

    def reset(self):
        self.x = None
        self.P = 1.0


class CoordinateFilter3D:
    """
    A wrapper class running three independent filters for X, Y, Z.
    """
    def __init__(self, filter_type="moving_average", window_size=8, process_noise=1e-4, measurement_noise=1e-2):
        self.filter_type = filter_type
        self.window_size = window_size
        self.process_noise = process_noise
        self.measurement_noise = measurement_noise

        self.ma_filter = MovingAverageFilter(window_size)
        self.kf_x = KalmanFilter1D(process_noise, measurement_noise)
        self.kf_y = KalmanFilter1D(process_noise, measurement_noise)
        self.kf_z = KalmanFilter1D(process_noise, measurement_noise)

    def set_filter_type(self, filter_type):
        self.filter_type = filter_type

    def set_ma_window(self, size):
        self.window_size = size
        self.ma_filter.set_window_size(size)

    def set_kf_parameters(self, process_noise, measurement_noise):
        self.process_noise = process_noise
        self.measurement_noise = measurement_noise
        self.kf_x.set_parameters(process_noise, measurement_noise)
        self.kf_y.set_parameters(process_noise, measurement_noise)
        self.kf_z.set_parameters(process_noise, measurement_noise)

    def filter(self, x, y, z):
        if self.filter_type == "none":
            return x, y, z
        elif self.filter_type == "moving_average":
            return self.ma_filter.filter(x, y, z)
        elif self.filter_type == "kalman":
            fx = self.kf_x.filter(x)
            fy = self.kf_y.filter(y)
            fz = self.kf_z.filter(z)
            return fx, fy, fz
        return x, y, z

    def reset(self):
        self.ma_filter.reset()
        self.kf_x.reset()
        self.kf_y.reset()
        self.kf_z.reset()

# Import pyrealsense2. Catch exception if the driver is not installed locally.
try:
    import pyrealsense2 as rs
except ImportError:
    rs = None

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("RealSenseVision")

class RealSenseVisionSystem:
    """
    Real-time perception system using an Intel RealSense D415 depth camera
    to detect a plate between two ArUco markers and track a rolling ball.
    """
    
    def __init__(
        self, 
        aruco_dict_id: int = cv2.aruco.DICT_4X4_50, 
        center_threshold: float = 0.15,
        min_ball_area: float = 30.0,
        min_circularity: float = 0.4
    ):
        """
        Initialize the vision system parameters.
        
        Args:
            aruco_dict_id: OpenCV ArUco dictionary identifier.
            center_threshold: Threshold on normalized error to define the CENTER state.
            min_ball_area: Minimum area in pixels to consider a contour as the ball.
            min_circularity: Minimum circularity shape factor to match the ball.
        """
        self.aruco_dict_id = aruco_dict_id
        self.center_threshold = center_threshold
        self.min_ball_area = min_ball_area
        self.min_circularity = min_circularity
        
        # RealSense pipeline variables
        self.pipeline: Optional[Any] = None
        self.config: Optional[Any] = None
        self.profile: Optional[Any] = None
        self.align: Optional[Any] = None
        self.intrinsics: Optional[Any] = None
        self.width = 1280
        self.height = 720
        
        # ArUco parameters and dictionary setup
        self._init_aruco()
        self._cached_preset = 1
        
    def _init_aruco(self):
        """
        Initialize the ArUco detector using a version-agnostic API.
        Attempts OpenCV 4.7+ API and falls back to legacy API.
        """
        try:
            # OpenCV 4.7+ API
            self.aruco_dict = cv2.aruco.getPredefinedDictionary(self.aruco_dict_id)
            self.aruco_params = cv2.aruco.DetectorParameters()
            # In OpenCV 4.7+, ArUcoDetector is used
            self.detector = cv2.aruco.ArucoDetector(self.aruco_dict, self.aruco_params)
            self.use_modern_aruco = True
            logger.info("Initialized modern OpenCV ArUco detector.")
        except (AttributeError, TypeError):
            # Legacy OpenCV ArUco API
            self.aruco_dict = cv2.aruco.Dictionary_get(self.aruco_dict_id)
            self.aruco_params = cv2.aruco.DetectorParameters_create()
            self.use_modern_aruco = False
            logger.info("Initialized legacy OpenCV ArUco detector.")

    def initialize_camera(self, width: int = 1280, height: int = 720, fps: int = 30) -> bool:
        """
        Configure and start the Intel RealSense pipeline (RGB + Depth),
        align depth to color, and retrieve camera intrinsics.
        
        Args:
            width: Horizontal resolution in pixels.
            height: Vertical resolution in pixels.
            fps: Frame rate for both streams.
            
        Returns:
            bool: True if pipeline successfully started, False otherwise.
        """
        if rs is None:
            logger.error("pyrealsense2 is not installed or available on this system.")
            return False
            
        try:
            self.width = width
            self.height = height
            self.pipeline = rs.pipeline()
            self.config = rs.config()
            
            # Request aligned streams
            self.config.enable_stream(rs.stream.color, width, height, rs.format.bgr8, fps)
            self.config.enable_stream(rs.stream.depth, width, height, rs.format.z16, fps)
            
            # Start streaming
            self.profile = self.pipeline.start(self.config)
            self.device = self.profile.get_device()
            
            # Check USB connection type
            is_usb2 = False
            try:
                if self.device.supports(rs.camera_info.usb_type_descriptor):
                    usb_type = self.device.get_info(rs.camera_info.usb_type_descriptor)
                    logger.info(f"RealSense device connected via USB {usb_type}")
                    if usb_type.startswith("2."):
                        is_usb2 = True
            except Exception as e:
                logger.warning(f"Could not verify USB connection type: {e}")
                
            # If USB 2.0, force fallback
            if is_usb2 and (width > 640 or height > 480):
                logger.warning("USB 2.0 connection detected. Widescreen 1280x720 requires USB 3.0. Falling back to 640x480 at 30 FPS...")
                self.pipeline.stop()
                width, height = 640, 480
                self.width = width
                self.height = height
                self.pipeline = rs.pipeline()
                self.config = rs.config()
                self.config.enable_stream(rs.stream.color, width, height, rs.format.bgr8, fps)
                self.config.enable_stream(rs.stream.depth, width, height, rs.format.z16, fps)
                self.profile = self.pipeline.start(self.config)
                self.device = self.profile.get_device()
            
            # Setup depth-to-color alignment
            align_to = rs.stream.color
            self.align = rs.align(align_to)
            
            # Warm up and verify frames arrive
            logger.info("Warming up camera streams...")
            try:
                for _ in range(5):
                    self.pipeline.wait_for_frames(timeout_ms=2500)
            except RuntimeError as e:
                # If warm up fails at high res, try falling back to 640x480
                if width > 640 or height > 480:
                    logger.warning(f"Frame acquisition timed out at {width}x{height}. Falling back to 640x480 at 30 FPS: {e}")
                    try:
                        self.pipeline.stop()
                    except Exception:
                        pass
                    width, height = 640, 480
                    self.width = width
                    self.height = height
                    self.pipeline = rs.pipeline()
                    self.config = rs.config()
                    self.config.enable_stream(rs.stream.color, width, height, rs.format.bgr8, fps)
                    self.config.enable_stream(rs.stream.depth, width, height, rs.format.z16, fps)
                    self.profile = self.pipeline.start(self.config)
                    self.device = self.profile.get_device()
                    # Re-align
                    self.align = rs.align(align_to)
                    # Try warming up again
                    logger.info("Warming up camera streams at fallback resolution...")
                    for _ in range(5):
                        self.pipeline.wait_for_frames(timeout_ms=2500)
                else:
                    raise e
            
            # Extract color stream intrinsics for 3D deprojection
            color_stream = self.profile.get_stream(rs.stream.color)
            video_profile = color_stream.as_video_stream_profile()
            self.intrinsics = video_profile.get_intrinsics()
            
            # Retrieve sensors
            self.depth_sensor = self.device.first_depth_sensor()
            self.color_sensor = None
            for sensor in self.device.query_sensors():
                if sensor.get_info(rs.camera_info.name) == 'RGB Camera':
                    self.color_sensor = sensor
            
            logger.info(f"Successfully started RealSense D415 camera at {self.width}x{self.height} @ {fps} FPS.")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Intel RealSense camera: {e}")
            self.stop()
            return False

    def set_laser_power(self, power_mw):
        if self.depth_sensor and self.depth_sensor.supports(rs.option.laser_power):
            self.depth_sensor.set_option(rs.option.laser_power, float(power_mw))

    def set_emitter_state(self, state):
        if self.depth_sensor and self.depth_sensor.supports(rs.option.emitter_enabled):
            self.depth_sensor.set_option(rs.option.emitter_enabled, float(state))

    def set_visual_preset(self, preset_val):
        self._cached_preset = int(preset_val)
        if self.depth_sensor and self.depth_sensor.supports(rs.option.visual_preset):
            try:
                self.depth_sensor.set_option(rs.option.visual_preset, float(preset_val))
            except Exception as e:
                logger.warning(f"Failed to set hardware visual preset: {e}")

    def get_visual_preset(self):
        if self.depth_sensor and self.depth_sensor.supports(rs.option.visual_preset):
            try:
                return int(self.depth_sensor.get_option(rs.option.visual_preset))
            except Exception:
                pass
        return self._cached_preset

    def set_exposure(self, exposure_us):
        if self.color_sensor and self.color_sensor.supports(rs.option.exposure):
            if self.color_sensor.supports(rs.option.enable_auto_exposure):
                self.color_sensor.set_option(rs.option.enable_auto_exposure, 0.0)
            self.color_sensor.set_option(rs.option.exposure, float(exposure_us))

    def set_auto_exposure(self, enable=True):
        if self.color_sensor and self.color_sensor.supports(rs.option.enable_auto_exposure):
            self.color_sensor.set_option(rs.option.enable_auto_exposure, 1.0 if enable else 0.0)
            
    def set_white_balance(self, value_kelvin):
        if self.color_sensor and self.color_sensor.supports(rs.option.white_balance):
            if self.color_sensor.supports(rs.option.enable_auto_white_balance):
                self.color_sensor.set_option(rs.option.enable_auto_white_balance, 0.0)
            self.color_sensor.set_option(rs.option.white_balance, float(value_kelvin))

    def set_auto_white_balance(self, enable=True):
        if self.color_sensor and self.color_sensor.supports(rs.option.enable_auto_white_balance):
            self.color_sensor.set_option(rs.option.enable_auto_white_balance, 1.0 if enable else 0.0)

    def get_laser_power(self):
        if self.depth_sensor and self.depth_sensor.supports(rs.option.laser_power):
            return self.depth_sensor.get_option(rs.option.laser_power)
        return 150.0

    def get_emitter_state(self):
        if self.depth_sensor and self.depth_sensor.supports(rs.option.emitter_enabled):
            return int(self.depth_sensor.get_option(rs.option.emitter_enabled))
        return 1

    def get_exposure(self):
        if self.color_sensor and self.color_sensor.supports(rs.option.exposure):
            return self.color_sensor.get_option(rs.option.exposure)
        return 1560.0

    def get_auto_exposure(self):
        if self.color_sensor and self.color_sensor.supports(rs.option.enable_auto_exposure):
            return bool(self.color_sensor.get_option(rs.option.enable_auto_exposure))
        return True

    def get_white_balance(self):
        if self.color_sensor and self.color_sensor.supports(rs.option.white_balance):
            return self.color_sensor.get_option(rs.option.white_balance)
        return 4600.0

    def get_auto_white_balance(self):
        if self.color_sensor and self.color_sensor.supports(rs.option.enable_auto_white_balance):
            return bool(self.color_sensor.get_option(rs.option.enable_auto_white_balance))
        return True

    def detect_aruco_markers(self, color_image: np.ndarray) -> Tuple[Optional[np.ndarray], Optional[np.ndarray], Optional[np.ndarray], Optional[float], List[np.ndarray], Optional[np.ndarray]]:
        """
        Detect ArUco markers 0 (left) and 1 (right) in the image.
        
        Args:
            color_image: Input BGR image.
            
        Returns:
            Tuple containing:
                - left_center: [x, y] coordinates of Marker 0.
                - right_center: [x, y] coordinates of Marker 1.
                - plate_center: [x, y] coordinates of the plate midpoint.
                - plate_width: Euclidean distance in pixels between the markers.
                - plate_axis: Normalized 2D vector [ux, uy] pointing from left to right marker.
                - corners: Detected marker corners.
                - ids: Detected marker IDs.
        """
        # Convert color image to grayscale for stable edge and marker detection
        gray = cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY)
        
        # Run detection
        if self.use_modern_aruco:
            corners, ids, rejected = self.detector.detectMarkers(gray)
        else:
            corners, ids, rejected = cv2.aruco.detectMarkers(
                gray, self.aruco_dict, parameters=self.aruco_params
            )
            
        if ids is None or len(ids) == 0:
            return None, None, None, None, None, None
            
        # Map detected markers
        marker_map = {}
        for i, m_id in enumerate(ids.flatten()):
            # Get corners for this marker
            c = corners[i][0]  # Shape: (4, 2)
            # Center is the mean of the 4 corners
            center = np.mean(c, axis=0)
            marker_map[m_id] = center
            
        # We need both left (0) and right (1) markers
        if 0 not in marker_map or 1 not in marker_map:
            return None, None, None, None, None, ids
            
        left_center = marker_map[0]
        right_center = marker_map[1]
        
        # Plate center is the midpoint between left and right centers
        plate_center = (left_center + right_center) / 2.0
        
        # Vector along plate axis (left to right)
        axis_vector = right_center - left_center
        plate_width = np.linalg.norm(axis_vector)
        
        if plate_width == 0:
            return None, None, None, None, None, ids
            
        plate_axis = axis_vector / plate_width
        
        return left_center, right_center, plate_center, plate_width, plate_axis, ids

    def detect_ball(self, color_image: np.ndarray, hsv_bounds: Dict[str, int], plate_box: Optional[np.ndarray] = None) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Segment a colored ball in BGR space using HSV bounds and select the largest circular contour.
        
        Args:
            color_image: Input BGR image.
            hsv_bounds: Dictionary with 'h_low', 's_low', 'v_low', 'h_high', 's_high', 'v_high'.
            plate_box: Optional numpy array of 4 corners of the plate rotated bounding box.
            
        Returns:
            Tuple containing:
                - ball_center: [x, y] center coordinates of the ball, or None if not detected.
                - best_contour: The selected contour, or None.
        """
        # Convert to HSV color space
        hsv_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2HSV)
        
        # Build lower and upper range arrays
        lower_bound = np.array([hsv_bounds['h_low'], hsv_bounds['s_low'], hsv_bounds['v_low']])
        upper_bound = np.array([hsv_bounds['h_high'], hsv_bounds['s_high'], hsv_bounds['v_high']])
        
        # Threshold the HSV image
        mask = cv2.inRange(hsv_image, lower_bound, upper_bound)
        
        # Apply plate mask boundary to prevent detecting background surroundings/reflections
        if plate_box is not None:
            plate_mask = np.zeros(mask.shape, dtype=np.uint8)
            cv2.drawContours(plate_mask, [np.array(plate_box, dtype=np.int32)], -1, 255, -1)
            # Dilate plate mask slightly to prevent clipping ball coordinates near edge of plate
            dilation_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25))
            plate_mask = cv2.dilate(plate_mask, dilation_kernel)
            mask = cv2.bitwise_and(mask, plate_mask)
            
        # Morphological operations to remove noise
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        best_contour = None
        max_area = 0.0
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < self.min_ball_area:
                continue
                
            # Compute circularity: 4 * pi * area / (perimeter^2)
            perimeter = cv2.arcLength(contour, True)
            if perimeter == 0:
                continue
                
            circularity = (4.0 * np.pi * area) / (perimeter ** 2)
            
            # Check circularity and select largest
            if circularity >= self.min_circularity:
                if area > max_area:
                    max_area = area
                    best_contour = contour
                    
        # If no circular contour matches, fall back to the largest contour overall if valid
        if best_contour is None and len(contours) > 0:
            largest_contour = max(contours, key=cv2.contourArea)
            if cv2.contourArea(largest_contour) >= self.min_ball_area:
                best_contour = largest_contour
                
        if best_contour is None:
            return None, None
            
        # Fit enclosing circle to get sub-pixel precision center
        (x, y), radius = cv2.minEnclosingCircle(best_contour)
        ball_center = np.array([x, y])
        
        return ball_center, best_contour

    def detect_red_plate(self, color_image: np.ndarray) -> Tuple[Optional[np.ndarray], Optional[float], Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Segment the red plate using HSV color thresholding and fit a rotated bounding box.
        
        Returns:
            Tuple containing:
                - plate_center: [x, y] midpoint of the plate.
                - plate_width: Length in pixels along the plate's major axis.
                - plate_axis: Unit vector [ux, uy] pointing left-to-right.
                - box_points: Rotated box corner points for visualization.
        """
        # Convert to HSV
        hsv = cv2.cvtColor(color_image, cv2.COLOR_BGR2HSV)
        
        # Red has two regions in HSV
        lower_red1 = np.array([0, 50, 40])
        upper_red1 = np.array([15, 255, 255])
        lower_red2 = np.array([160, 50, 40])
        upper_red2 = np.array([180, 255, 255])
        
        mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        mask = cv2.bitwise_or(mask1, mask2)
        
        # Clean noise
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Sort contours by area in descending order
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        
        valid_contours = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 400:  # Primary contour (largest red plate piece)
                valid_contours.append(contour)
            elif area > 100 and len(valid_contours) > 0:
                # Secondary contours (split plate pieces), merge if close to primary
                c_centroid = np.mean(contour[:, 0, :], axis=0)
                prim_centroid = np.mean(valid_contours[0][:, 0, :], axis=0)
                dist = np.linalg.norm(c_centroid - prim_centroid)
                if dist < 450:  # Within maximum plate length in pixels
                    valid_contours.append(contour)
                    
        if not valid_contours:
            return None, None, None, None
            
        # Concatenate all valid red contours to handle ball occlusion splitting the plate
        merged_pts = np.concatenate(valid_contours)
        rect = cv2.minAreaRect(merged_pts)
        box = cv2.boxPoints(rect)
        box_points = np.int32(box)
        
        center = np.array(rect[0])
        size = rect[1]
        angle = rect[2]
        
        # Determine plate orientation (longer side is the plate axis)
        if size[0] > size[1]:
            plate_width = size[0]
            rad = np.deg2rad(angle)
            plate_axis = np.array([np.cos(rad), np.sin(rad)])
        else:
            plate_width = size[1]
            rad = np.deg2rad(angle + 90)
            plate_axis = np.array([np.cos(rad), np.sin(rad)])
            
        # Guarantee left-to-right orientation (+X pointing right)
        if plate_axis[0] < 0:
            plate_axis = -plate_axis
            
        return center, plate_width, plate_axis, box_points

    def project_coordinate(
        self, 
        plate_center: np.ndarray, 
        plate_axis: np.ndarray, 
        plate_width: float, 
        ball_center: np.ndarray
    ) -> Tuple[float, float, str]:
        """
        Project the ball coordinate onto the plate axis and calculate normalized error and state.
        
        Args:
            plate_center: [x, y] center of the plate.
            plate_axis: Normalized unit vector along the plate axis.
            plate_width: Length of the plate in pixels.
            ball_center: [x, y] center of the ball.
            
        Returns:
            Tuple containing:
                - ball_error: Normalized position between [-1.0, 1.0]
                - ball_offset_pixels: Signed offset distance in pixels from the plate center.
                - ball_state: State string ('LEFT', 'CENTER', or 'RIGHT').
        """
        # Vector from plate center to ball center
        to_ball = ball_center - plate_center
        
        # Signed projection offset in pixels
        ball_offset_pixels = np.dot(to_ball, plate_axis)
        
        # Normalized error (-1.0 at marker 0, +1.0 at marker 1)
        half_width = plate_width / 2.0
        normalized_error = ball_offset_pixels / half_width
        
        # Clamp to [-1.0, 1.0]
        ball_error = float(np.clip(normalized_error, -1.0, 1.0))
        
        # Determine LEFT, CENTER, RIGHT state based on thresholds
        if ball_error < -self.center_threshold:
            ball_state = "LEFT"
        elif ball_error > self.center_threshold:
            ball_state = "RIGHT"
        else:
            ball_state = "CENTER"
            
        return ball_error, ball_offset_pixels, ball_state

    def estimate_depth(self, depth_frame: Any, ball_center: np.ndarray) -> Tuple[float, List[float]]:
        """
        Extract the distance at the ball center pixel using a noise-resistant 9x9 neighborhood search,
        and deproject to 3D camera coordinates in millimeters.
        
        Args:
            depth_frame: RealSense depth frame object.
            ball_center: [x, y] coordinates of the ball center.
            
        Returns:
            Tuple containing:
                - distance_m: Extracted depth distance in meters.
                - ball_xyz_mm: Real-world camera coordinates [X, Y, Z] in millimeters.
        """
        x_pixel = int(round(ball_center[0]))
        y_pixel = int(round(ball_center[1]))
        
        h, w = depth_frame.get_height(), depth_frame.get_width()
        px = int(max(0, min(x_pixel, w - 1)))
        py = int(max(0, min(y_pixel, h - 1)))
        
        distance_m = depth_frame.get_distance(px, py)
        
        # Fallback: if depth is invalid (0.0), search a small window (up to 9x9) for valid depth
        if distance_m <= 0.0:
            valid_distances = []
            for r in range(1, 5): # search up to radius of 4 pixels
                for dx in range(-r, r + 1):
                    for dy in range(-r, r + 1):
                        nx = px + dx
                        ny = py + dy
                        if 0 <= nx < w and 0 <= ny < h:
                            dist = depth_frame.get_distance(nx, ny)
                            if dist > 0.0:
                                valid_distances.append(dist)
                if valid_distances:
                    distance_m = float(np.median(valid_distances))
                    break
            
        # Deproject pixel coordinate to 3D point using camera intrinsics
        if distance_m > 0.0 and self.intrinsics is not None:
            # rs2_deproject_pixel_to_point returns coordinates in meters
            point_m = rs.rs2_deproject_pixel_to_point(self.intrinsics, [px, py], distance_m)
            # Convert to millimeters
            ball_xyz_mm = [float(coord * 1000.0) for coord in point_m]
        else:
            ball_xyz_mm = [0.0, 0.0, 0.0]
            
        return distance_m, ball_xyz_mm

    def visualize(
        self, 
        color_image: np.ndarray, 
        detection_data: Dict[str, Any],
        best_contour: Optional[np.ndarray] = None,
        left_center: Optional[np.ndarray] = None,
        right_center: Optional[np.ndarray] = None,
        plate_box: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Overlay annotations on the RGB image.
        
        Args:
            color_image: Original RGB frame (modified in-place).
            detection_data: Result dictionary returned by run_step.
            best_contour: Contour of the detected ball.
            left_center: [x, y] of Marker 0.
            right_center: [x, y] of Marker 1.
            plate_box: Rotated bounding box points of the red plate (markerless fallback).
            
        Returns:
            np.ndarray: Annotated BGR frame.
        """
        vis_image = color_image.copy()
        
        # Draw vertical and horizontal center lines (crosshair)
        height, width = vis_image.shape[:2]
        center_x = width // 2
        center_y = height // 2
        
        # Subtly colored crosshair lines (dark gray) and a white origin circle
        cv2.line(vis_image, (center_x, 0), (center_x, height), (80, 80, 80), 1)
        cv2.line(vis_image, (0, center_y), (width, center_y), (80, 80, 80), 1)
        cv2.circle(vis_image, (center_x, center_y), 4, (255, 255, 255), -1)
        
        # 1. Draw Plate Axis (Green Line) and Plate Center (Blue Point)
        if left_center is not None and right_center is not None:
            pt_left = tuple(np.round(left_center).astype(int))
            pt_right = tuple(np.round(right_center).astype(int))
            cv2.line(vis_image, pt_left, pt_right, (0, 255, 0), 2)
            
            pt_plate_center = tuple(np.round(detection_data["plate_center"]).astype(int))
            cv2.circle(vis_image, pt_plate_center, 6, (255, 0, 0), -1)
            
            # Label Marker IDs
            cv2.putText(vis_image, "L_0", (pt_left[0] - 10, pt_left[1] - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            cv2.putText(vis_image, "R_1", (pt_right[0] - 10, pt_right[1] - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        elif plate_box is not None:
            # Draw detected red plate rotated bounding box (orange outline)
            cv2.drawContours(vis_image, [plate_box], 0, (0, 165, 255), 2)
            pt_plate_center = tuple(np.round(detection_data["plate_center"]).astype(int))
            cv2.circle(vis_image, pt_plate_center, 6, (255, 0, 0), -1)
            cv2.putText(vis_image, "RED PLATE", (pt_plate_center[0] - 35, pt_plate_center[1] - 12), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 165, 255), 1, cv2.LINE_AA)
                        
        # 2. Draw Ball Contour (Yellow Outline) and Ball Center (Red Point)
        if best_contour is not None:
            cv2.drawContours(vis_image, [best_contour], -1, (0, 255, 255), 2)
            pt_ball_center = tuple(np.round(detection_data["ball_center"]).astype(int))
            cv2.circle(vis_image, pt_ball_center, 6, (0, 0, 255), -1)

        # 3. Draw tracked ball coordinates next to the ball center
        ball_center_raw = detection_data.get("ball_center")
        if ball_center_raw is not None and ball_center_raw != [0.0, 0.0] and ball_center_raw != (0.0, 0.0):
            pt_ball = tuple(np.round(ball_center_raw).astype(int))
            x_px = int(round(pt_ball[0] - center_x))
            y_px = int(round(center_y - pt_ball[1]))  # +Y is up
            
            xyz_mm = detection_data.get("ball_xyz_mm", [0.0, 0.0, 0.0])
            x_mm = xyz_mm[0]
            y_mm = -xyz_mm[1]  # +Y is up (negated realsense Y)
            z_mm = xyz_mm[2]
            
            text_px = f"({x_px:d}px, {y_px:d}px)"
            text_mm = f"({x_mm:.1f}, {y_mm:.1f}, {z_mm:.1f})mm"
            
            text_x = pt_ball[0] + 12
            text_y = pt_ball[1] - 6
            cv2.putText(vis_image, text_px, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 255, 255), 1, cv2.LINE_AA)
            cv2.putText(vis_image, text_mm, (text_x, text_y + 13), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 255, 0), 1, cv2.LINE_AA)
        # 3.5. Draw Target Balance Point (Expected Ball Position)
        plate_center_val = detection_data.get("plate_center")
        if plate_center_val is not None and plate_center_val != [0.0, 0.0] and plate_center_val != (0.0, 0.0):
            pt_plate_center = tuple(np.round(plate_center_val).astype(int))
            
            # Draw translucent target ball body (Cyber-Control accent color #CFFF3E -> BGR: 62, 255, 207)
            overlay = vis_image.copy()
            target_radius = 22
            cv2.circle(overlay, pt_plate_center, target_radius, (62, 255, 207), -1)
            cv2.addWeighted(overlay, 0.25, vis_image, 0.75, 0, dst=vis_image)
            
            # Target ball border and crosshair
            cv2.circle(vis_image, pt_plate_center, target_radius, (62, 255, 207), 1, cv2.LINE_AA)
            cv2.drawMarker(vis_image, pt_plate_center, (255, 255, 255), markerType=cv2.MARKER_CROSS, markerSize=10, thickness=1)
            cv2.putText(vis_image, "TARGET", (pt_plate_center[0] - 20, pt_plate_center[1] - target_radius - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.35, (62, 255, 207), 1, cv2.LINE_AA)
                        
        # 4. Draw Telemetry Overlay
        # Background box for readability
        cv2.rectangle(vis_image, (10, 10), (320, 185), (0, 0, 0), -1)
        alpha = 0.65
        cv2.addWeighted(vis_image, alpha, color_image, 1 - alpha, 0, dst=vis_image)
        
        state_color = (255, 255, 255)
        state_str = detection_data["ball_state"]
        if state_str == "LEFT":
            state_color = (0, 165, 255)  # Orange/Yellow
        elif state_str == "RIGHT":
            state_color = (255, 191, 0)  # Light Blue
        elif state_str == "CENTER":
            state_color = (0, 255, 0)    # Green
        else:
            state_color = (0, 0, 255)    # Red (Errors)
            
        # Add labels
        cv2.putText(vis_image, f"STATE: {state_str}", (20, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, state_color, 2)
        cv2.putText(vis_image, f"Error (Norm): {detection_data['ball_error']:.3f}", (20, 55), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(vis_image, f"Offset (px): {detection_data['ball_offset_pixels']:.1f}", (20, 80), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Display physical offsets in mm!
        ball_x_mm = detection_data.get("ball_x_3d", 0.0) * 1000.0
        ball_y_mm = detection_data.get("ball_y_3d", 0.0) * 1000.0
        cv2.putText(vis_image, f"Pos (X, Y): [{ball_x_mm:+.1f}, {ball_y_mm:+.1f}] mm", (20, 105), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
                    
        cv2.putText(vis_image, f"Depth (m): {detection_data['ball_depth_m']:.3f}m", (20, 130), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                    
        xyz = detection_data["ball_xyz_mm"]
        cv2.putText(vis_image, f"XYZ (mm): [{xyz[0]:.1f}, {xyz[1]:.1f}, {xyz[2]:.1f}]", (20, 155), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                    
        return vis_image

    def run_step(self, color_image: np.ndarray, depth_frame: Optional[Any], hsv_bounds: Dict[str, int]) -> Tuple[Dict[str, Any], np.ndarray]:
        """
        Process a single image frame to detect markers, detect ball, project coordinate, 
        estimate depth, and generate visualization.
        
        Args:
            color_image: Input RGB frame from camera.
            depth_frame: Depth frame aligned to the color image.
            hsv_bounds: HSV lower/upper parameters dictionary.
            
        Returns:
            Tuple containing:
                - output_api: Dict as defined in requirements.
                - visual_frame: Annotated output image.
        """
        h, w = color_image.shape[:2]
        
        # 1. Detect ArUco markers first (primary method for high-stability, zero-occlusion tracking)
        left_center, right_center, plate_center, plate_width, plate_axis, ids = self.detect_aruco_markers(color_image)
        using_aruco = False
        plate_box = None
        
        if plate_center is not None:
            using_aruco = True
            # Construct a highly robust synthetic plate box bounding polygon from ArUco markers
            perp_axis = np.array([-plate_axis[1], plate_axis[0]])
            half_w = plate_width * 0.16
            p0 = left_center + perp_axis * half_w
            p1 = left_center - perp_axis * half_w
            p2 = right_center - perp_axis * half_w
            p3 = right_center + perp_axis * half_w
            plate_box = np.array([p0, p1, p2, p3], dtype=np.int32)
        else:
            # Fallback to red plate if ArUco markers are not both detected
            plate_center, plate_width, plate_axis, plate_box = self.detect_red_plate(color_image)
            using_aruco = False
            
        # 2. Detect Ball
        ball_center, best_contour = self.detect_ball(color_image, hsv_bounds, plate_box)
        
        # Handle Marker / Plate Loss first
        if plate_center is None or plate_axis is None or plate_width is None:
            # Error handling: Missing plate reference
            out_api = {
                "ball_error": 0.0,
                "ball_offset_pixels": 0.0,
                "ball_y_3d": 0.0,
                "ball_x_3d": 0.0,
                "ball_state": "LOST_MARKERS",
                "ball_depth_m": 0.0,
                "ball_xyz_mm": [0.0, 0.0, 0.0],
                "plate_center": [0.0, 0.0],
                "ball_center": [float(ball_center[0]), float(ball_center[1])] if ball_center is not None else [0.0, 0.0],
                "frame_width": w,
                "frame_height": h
            }
            # Generate visualization with warnings
            vis = self.visualize(color_image, out_api, best_contour=best_contour, plate_box=plate_box)
            return out_api, vis
            
        # Handle Ball Loss next
        if ball_center is None:
            # Error handling: Missing ball
            out_api = {
                "ball_error": 0.0,
                "ball_offset_pixels": 0.0,
                "ball_y_3d": 0.0,
                "ball_x_3d": 0.0,
                "ball_state": "LOST_BALL",
                "ball_depth_m": 0.0,
                "ball_xyz_mm": [0.0, 0.0, 0.0],
                "plate_center": [float(plate_center[0]), float(plate_center[1])],
                "ball_center": [0.0, 0.0],
                "frame_width": w,
                "frame_height": h
            }
            vis = self.visualize(
                color_image, out_api, 
                left_center=left_center, right_center=right_center,
                plate_box=plate_box
            )
            return out_api, vis
            
        # 3. Coordinate Projection and Scaling
        ball_error, ball_offset_pixels, ball_state = self.project_coordinate(
            plate_center, plate_axis, plate_width, ball_center
        )
        
        # Calculate dynamic physical coordinates based on actual dimensions:
        # Length is 384mm outer (380mm inner), Width is 54mm outer (50mm inner)
        to_ball = ball_center - plate_center
        ball_offset_pixels = float(np.dot(to_ball, plate_axis))
        
        # Transverse axis (perpendicular to plate axis)
        plate_perp_axis = np.array([-plate_axis[1], plate_axis[0]])
        ball_perp_offset_pixels = float(np.dot(to_ball, plate_perp_axis))
        
        if not using_aruco:
            # Bounding box width represents 384mm (0.384m) length
            scale = 0.384 / plate_width
            ball_y_3d = ball_offset_pixels * scale
            ball_x_3d = ball_perp_offset_pixels * scale
            # Clamp to inner bounds: length is 380mm [-0.190, 0.190] m, width is 50mm [-0.025, 0.025] m
            ball_y_3d = float(np.clip(ball_y_3d, -0.190, 0.190))
            ball_x_3d = float(np.clip(ball_x_3d, -0.025, 0.025))
        else:
            # ArUco fallback: use standard 220mm half-width (0.220m)
            scale = 0.22 / (plate_width / 2.0)
            ball_y_3d = ball_offset_pixels * scale
            ball_x_3d = ball_perp_offset_pixels * scale
            ball_y_3d = float(np.clip(ball_y_3d, -0.22, 0.22))
            ball_x_3d = float(np.clip(ball_x_3d, -0.03, 0.03))
            
        # 4. Depth Extraction (if depth frame is available)
        distance_m = 0.0
        ball_xyz_mm = [0.0, 0.0, 0.0]
        if depth_frame is not None:
            distance_m, ball_xyz_mm = self.estimate_depth(depth_frame, ball_center)
            
        # Build Output API Dictionary
        out_api = {
            "ball_error": ball_error,
            "ball_offset_pixels": float(ball_offset_pixels),
            "ball_y_3d": ball_y_3d,
            "ball_x_3d": ball_x_3d,
            "ball_state": ball_state,
            "ball_depth_m": distance_m,
            "ball_xyz_mm": ball_xyz_mm,
            "plate_center": [float(plate_center[0]), float(plate_center[1])],
            "ball_center": [float(ball_center[0]), float(ball_center[1])],
            "frame_width": w,
            "frame_height": h
        }
        
        # 5. Build visualization frame
        vis = self.visualize(
            color_image, out_api, 
            best_contour=best_contour, 
            left_center=left_center, 
            right_center=right_center,
            plate_box=plate_box
        )
        
        return out_api, vis

    def stop(self):
        """Release the pipeline resources."""
        if self.pipeline is not None:
            try:
                self.pipeline.stop()
                logger.info("Intel RealSense pipeline stopped.")
            except Exception as e:
                logger.warning(f"Error when stopping RealSense pipeline: {e}")
            finally:
                self.pipeline = None
                
        cv2.destroyAllWindows()


class MockDepthFrame:
    """Mock RealSense depth frame for simulation mode."""
    def __init__(self, width: int = 1280, height: int = 720, base_depth_m: float = 0.85):
        self.width = width
        self.height = height
        self.base_depth_m = base_depth_m
        
    def get_width(self) -> int:
        return self.width
        
    def get_height(self) -> int:
        return self.height
        
    def get_distance(self, x: int, y: int) -> float:
        # Generate depth centered around base_depth with small noise
        return self.base_depth_m + np.random.normal(0, 0.001)


class RealSenseTrackerThread:
    """
    Background worker thread that drives RealSenseVisionSystem acquisition 
    and handles coordinate tracking and base64 compression.
    """
    def __init__(self, camera_index: int = 0):
        self.camera_index = camera_index
        self.running = False
        self.thread = None
        self.lock = threading.Lock()
        
        self.vision_system = RealSenseVisionSystem()
        self.latest_frame = None
        self.latest_base64_frame = None
        self.latest_tracking_data = None
        self.fps = 0.0
        
        # Default HSV tuning values (targets a green ball on a red plate)
        self.hsv_bounds = {
            "h_low": 35,
            "s_low": 40,
            "v_low": 40,
            "h_high": 85,
            "s_high": 255,
            "v_high": 255
        }
        self.mock_mode = False
        self.coord_filter = CoordinateFilter3D()
        
        # Mock settings properties
        self._mock_laser_power = 150.0
        self._mock_emitter_state = 1
        self._mock_visual_preset = 1
        self._mock_auto_exposure = True
        self._mock_exposure_us = 1560.0
        self._mock_auto_white_balance = True
        self._mock_white_balance_temp = 4600.0
        
        # Camera settings cache to prevent continuous hardware querying overhead
        self.camera_settings_cache = {}
        
    def refresh_camera_settings_cache(self):
        if self.mock_mode:
            self.camera_settings_cache = {
                "laser_power": self._mock_laser_power,
                "emitter_state": self._mock_emitter_state,
                "visual_preset": self._mock_visual_preset,
                "auto_exposure": self._mock_auto_exposure,
                "exposure_us": self._mock_exposure_us,
                "auto_white_balance": self._mock_auto_white_balance,
                "white_balance_temp": self._mock_white_balance_temp,
                "hsv_bounds": self.hsv_bounds,
                "filter_mode": self.coord_filter.filter_type,
                "filter_window": self.coord_filter.window_size,
                "filter_process_noise": self.coord_filter.process_noise,
                "filter_measurement_noise": self.coord_filter.measurement_noise,
            }
        else:
            try:
                self.camera_settings_cache = {
                    "laser_power": self.vision_system.get_laser_power(),
                    "emitter_state": self.vision_system.get_emitter_state(),
                    "visual_preset": self.vision_system.get_visual_preset(),
                    "auto_exposure": self.vision_system.get_auto_exposure(),
                    "exposure_us": self.vision_system.get_exposure(),
                    "auto_white_balance": self.vision_system.get_auto_white_balance(),
                    "white_balance_temp": self.vision_system.get_white_balance(),
                    "hsv_bounds": self.hsv_bounds,
                    "filter_mode": self.coord_filter.filter_type,
                    "filter_window": self.coord_filter.window_size,
                    "filter_process_noise": self.coord_filter.process_noise,
                    "filter_measurement_noise": self.coord_filter.measurement_noise,
                }
            except Exception as e:
                logger.warning(f"Error querying camera settings from hardware, using defaults: {e}")
                self.camera_settings_cache = {
                    "laser_power": 150.0,
                    "emitter_state": 1,
                    "visual_preset": 1,
                    "auto_exposure": True,
                    "exposure_us": 1560.0,
                    "auto_white_balance": True,
                    "white_balance_temp": 4600.0,
                    "hsv_bounds": self.hsv_bounds,
                    "filter_mode": self.coord_filter.filter_type,
                    "filter_window": self.coord_filter.window_size,
                    "filter_process_noise": self.coord_filter.process_noise,
                    "filter_measurement_noise": self.coord_filter.measurement_noise,
                }

    def get_camera_settings(self) -> Dict[str, Any]:
        if not self.camera_settings_cache:
            self.refresh_camera_settings_cache()
        return self.camera_settings_cache

    def set_camera_settings(self, settings: Dict[str, Any]):
        if "hsv_bounds" in settings:
            self.hsv_bounds.update(settings["hsv_bounds"])
        
        if "filter_mode" in settings:
            self.coord_filter.set_filter_type(settings["filter_mode"])
        if "filter_window" in settings:
            self.coord_filter.set_ma_window(int(settings["filter_window"]))
        if "filter_process_noise" in settings or "filter_measurement_noise" in settings:
            pn = settings.get("filter_process_noise", self.coord_filter.process_noise)
            mn = settings.get("filter_measurement_noise", self.coord_filter.measurement_noise)
            self.coord_filter.set_kf_parameters(float(pn), float(mn))

        if self.mock_mode:
            if "laser_power" in settings: self._mock_laser_power = float(settings["laser_power"])
            if "emitter_state" in settings: self._mock_emitter_state = int(settings["emitter_state"])
            if "visual_preset" in settings: self._mock_visual_preset = int(settings["visual_preset"])
            if "auto_exposure" in settings: self._mock_auto_exposure = bool(settings["auto_exposure"])
            if "exposure_us" in settings: self._mock_exposure_us = float(settings["exposure_us"])
            if "auto_white_balance" in settings: self._mock_auto_white_balance = bool(settings["auto_white_balance"])
            if "white_balance_temp" in settings: self._mock_white_balance_temp = float(settings["white_balance_temp"])
        else:
            try:
                if "laser_power" in settings:
                    self.vision_system.set_laser_power(settings["laser_power"])
                if "emitter_state" in settings:
                    self.vision_system.set_emitter_state(settings["emitter_state"])
                if "visual_preset" in settings:
                    self.vision_system.set_visual_preset(settings["visual_preset"])
                if "auto_exposure" in settings:
                    self.vision_system.set_auto_exposure(settings["auto_exposure"])
                if "exposure_us" in settings:
                    self.vision_system.set_exposure(settings["exposure_us"])
                if "auto_white_balance" in settings:
                    self.vision_system.set_auto_white_balance(settings["auto_white_balance"])
                if "white_balance_temp" in settings:
                    self.vision_system.set_white_balance(settings["white_balance_temp"])
            except Exception as e:
                logger.error(f"Error applying camera settings to hardware: {e}")

        # Refresh cache after setting new values
        self.refresh_camera_settings_cache()

    def start(self) -> bool:
        if self.running:
            return True
            
        camera_active = self.vision_system.initialize_camera()
        self.mock_mode = not camera_active
        if self.mock_mode:
            logger.warning("[RealSenseTrackerThread] Physical camera failed or missing. Starting in Mock Mode.")
            
        self.running = True
        self.refresh_camera_settings_cache()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        return True
        
    def stop(self):
        self.running = False
        if self.thread is not None:
            self.thread.join(timeout=1.0)
            self.thread = None
        self.vision_system.stop()
        
    def _run_loop(self):
        sim_time = 0.0
        prev_time = time.time()
        width = self.vision_system.width
        height = self.vision_system.height
        mock_depth = MockDepthFrame(width, height)
        
        while self.running:
            loop_start = time.time()
            color_image = None
            depth_frame = None
            
            if not self.mock_mode:
                try:
                    frames = self.vision_system.pipeline.wait_for_frames(timeout_ms=1000)
                    aligned_frames = self.vision_system.align.process(frames)
                    
                    color_frame = aligned_frames.get_color_frame()
                    depth_frame = aligned_frames.get_depth_frame()
                    
                    if not color_frame or not depth_frame:
                        time.sleep(0.01)
                        continue
                        
                    color_image = np.asanyarray(color_frame.get_data())
                except Exception as e:
                    logger.error(f"[RealSenseTrackerThread] Pipeline read error: {e}")
                    time.sleep(0.01)
                    continue
            else:
                # --- MOCK SIMULATION MODE ---
                # Plate is Red, Ball is Green, markers on left/right robot hands
                color_image = np.zeros((height, width, 3), dtype=np.uint8) + 40 # Grey background
                
                # Draw mock robot hands ArUco markers
                pt0 = (int(width * 0.23), int(height * 0.5))
                pt1 = (int(width * 0.77), int(height * 0.5))
                
                cv2.rectangle(color_image, (pt0[0]-25, pt0[1]-25), (pt0[0]+25, pt0[1]+25), (255, 255, 255), -1)
                cv2.rectangle(color_image, (pt0[0]-15, pt0[1]-15), (pt0[0]+15, pt0[1]+15), (0, 0, 0), -1)
                cv2.putText(color_image, "0", (pt0[0]-5, pt0[1]+5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                
                cv2.rectangle(color_image, (pt1[0]-25, pt1[1]-25), (pt1[0]+25, pt1[1]+25), (255, 255, 255), -1)
                cv2.rectangle(color_image, (pt1[0]-15, pt1[1]-15), (pt1[0]+15, pt1[1]+15), (0, 0, 0), -1)
                cv2.putText(color_image, "1", (pt1[0]-5, pt1[1]+5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                
                # Draw a thick red plate suspended between the two markers (BGR: 50, 50, 220)
                cv2.rectangle(color_image, (pt0[0]+25, pt0[1]-6), (pt1[0]-25, pt1[1]+6), (50, 50, 220), -1)
                
                # Simulate ball rolling back and forth along the axis
                sim_time += 0.033
                ball_pos_factor = np.sin(sim_time)
                plate_center_x = (pt0[0] + pt1[0]) / 2.0
                plate_half_width = (pt1[0] - pt0[0]) / 2.0
                
                ball_x = int(plate_center_x + ball_pos_factor * plate_half_width * 0.7)
                ball_y = int(height * 0.5)
                
                # Draw a green ball on the plate (BGR: 0, 200, 0)
                ball_radius = int(18 * height / 480)
                cv2.circle(color_image, (ball_x, ball_y), ball_radius, (0, 200, 0), -1)
                
                # Set mock depth
                depth_frame = mock_depth
                
                if self.vision_system.intrinsics is None:
                    class MockIntrinsics:
                        width = 1280
                        height = 720
                        ppx = 640.0
                        ppy = 360.0
                        fx = 900.0
                        fy = 900.0
                        model = None
                        coeffs = [0.0, 0.0, 0.0, 0.0, 0.0]
                    
                    MockIntrinsics.width = width
                    MockIntrinsics.height = height
                    MockIntrinsics.ppx = width / 2.0
                    MockIntrinsics.ppy = height / 2.0
                    MockIntrinsics.fx = width * 615.0 / 640.0
                    MockIntrinsics.fy = height * 615.0 / 480.0
                    self.vision_system.intrinsics = MockIntrinsics()
                    
                    global rs
                    if rs is None:
                        class MockRS:
                            @staticmethod
                            def rs2_deproject_pixel_to_point(intrinsics, pixel, depth):
                                x = (pixel[0] - intrinsics.ppx) * depth / intrinsics.fx
                                y = (pixel[1] - intrinsics.ppy) * depth / intrinsics.fy
                                z = depth
                                return [x, y, z]
                        rs = MockRS
            
            # Run perception step
            if not self.mock_mode:
                api_data, annotated_image = self.vision_system.run_step(color_image, depth_frame, self.hsv_bounds)
            else:
                # In Mock Mode, bypass the OpenCV ArUco detector (which fails on simple drawn grids)
                # and directly populate the telemetry state coordinates for a rolling green ball on a red plate.
                ball_error = float(ball_pos_factor * 0.7)
                ball_offset_pixels = float(ball_pos_factor * plate_half_width * 0.7)
                ball_state = "LEFT" if ball_error < -0.15 else "RIGHT" if ball_error > 0.15 else "CENTER"
                
                # Mock dimensions: length = 380mm (0.380m)
                ball_y_3d = ball_error * 0.190
                ball_x_3d = 0.0
                
                api_data = {
                    "ball_error": ball_error,
                    "ball_offset_pixels": ball_offset_pixels,
                    "ball_y_3d": ball_y_3d,
                    "ball_x_3d": ball_x_3d,
                    "ball_state": ball_state,
                    "ball_depth_m": 0.85,
                    "ball_xyz_mm": [float((ball_x - self.vision_system.intrinsics.ppx) * 850.0 / self.vision_system.intrinsics.fx), 0.0, 850.0],
                    "plate_center": [float(plate_center_x), float(height * 0.5)],
                    "ball_center": [float(ball_x), float(ball_y)],
                    "frame_width": width,
                    "frame_height": height
                }
                
                annotated_image = self.vision_system.visualize(
                    color_image, api_data,
                    best_contour=None,
                    left_center=np.array(pt0),
                    right_center=np.array(pt1)
                )
                
            # Inject camera settings cache into the API data dictionary so the frontend gets it
            if api_data is not None:
                api_data["camera_settings"] = self.get_camera_settings()
                
            # Apply motion filter on the 3D target coordinates
            if api_data is not None and "ball_y_3d" in api_data:
                rx = api_data.get("ball_x_3d", 0.0)
                ry = api_data.get("ball_y_3d", 0.0)
                rz = api_data.get("ball_depth_m", 0.0)
                
                # Filter coordinates
                fx, fy, fz = self.coord_filter.filter(rx, ry, rz)
                
                api_data["ball_x_3d_filtered"] = fx
                api_data["ball_y_3d_filtered"] = fy
                api_data["ball_depth_m_filtered"] = fz
                
                # Overwrite coordinate sent to balancer with filtered version
                api_data["ball_y_3d"] = fy
            
            # Base64 encode the frame
            base64_encoded = None
            if annotated_image is not None:
                try:
                    h, w = annotated_image.shape[:2]
                    scale = 640.0 / w
                    resized = cv2.resize(annotated_image, (640, int(h * scale)))
                    ret, buffer = cv2.imencode('.jpg', resized, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
                    if ret:
                        base64_encoded = base64.b64encode(buffer).decode('utf-8')
                except Exception as e:
                    logger.error(f"[RealSenseTrackerThread] Base64 encoding error: {e}")
                    
            # Calculate FPS
            curr_time = time.time()
            dt = curr_time - prev_time
            prev_time = curr_time
            if dt > 0:
                self.fps = 0.9 * self.fps + 0.1 * (1.0 / dt)
                
            # Update outputs safely
            with self.lock:
                self.latest_frame = annotated_image
                self.latest_base64_frame = base64_encoded
                self.latest_tracking_data = api_data
                
            # Sleep to maintain FPS
            elapsed = time.time() - loop_start
            sleep_time = max(0.001, 0.033 - elapsed)
            time.sleep(sleep_time)
            
    def get_latest_data(self):
        with self.lock:
            return self.latest_frame, self.latest_tracking_data, None, self.fps
            
    def get_latest_base64_frame(self) -> Optional[str]:
        with self.lock:
            return self.latest_base64_frame
