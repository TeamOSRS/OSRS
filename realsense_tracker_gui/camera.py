# pyrefly: ignore [missing-import]
import pyrealsense2 as rs
# pyrefly: ignore [missing-import]
import cv2
import numpy as np

class RealSenseCamera:
    def __init__(self, width=640, height=480, fps=30):
        self.width = width
        self.height = height
        self.fps = fps
        self.pipeline = rs.pipeline()
        self.config = rs.config()
        
        # Enable depth and color streams
        self.config.enable_stream(rs.stream.depth, self.width, self.height, rs.format.z16, self.fps)
        self.config.enable_stream(rs.stream.color, self.width, self.height, rs.format.bgr8, self.fps)
        
        self.profile = None
        self.align = rs.align(rs.stream.color)
        self.intrinsics = None
        self.device = None
        self.depth_sensor = None
        self.color_sensor = None

    def start(self):
        self.profile = self.pipeline.start(self.config)
        # Retrieve camera intrinsics for color stream
        color_stream = self.profile.get_stream(rs.stream.color)
        self.intrinsics = color_stream.as_video_stream_profile().get_intrinsics()

        # Retrieve device and individual sensors for manipulating options
        self.device = self.profile.get_device()
        self.depth_sensor = self.device.first_depth_sensor()
        
        self.color_sensor = None
        for sensor in self.device.query_sensors():
            if sensor.get_info(rs.camera_info.name) == 'RGB Camera':
                self.color_sensor = sensor

    def set_laser_power(self, power_mw):
        """Sets the IR projector laser power in milliwatts (range: 0 to 360 mW)."""
        if self.depth_sensor and self.depth_sensor.supports(rs.option.laser_power):
            self.depth_sensor.set_option(rs.option.laser_power, float(power_mw))

    def set_emitter_state(self, state):
        """0 = Disable, 1 = Enable Laser Projector, 2 = Auto Laser"""
        if self.depth_sensor and self.depth_sensor.supports(rs.option.emitter_enabled):
            self.depth_sensor.set_option(rs.option.emitter_enabled, float(state))

    def set_visual_preset(self, preset_val):
        """Sets depth sensor visual preset (0=Custom, 1=Default, 2=Hand, 3=High Accuracy, 4=High Density, 5=Medium Density)"""
        if self.depth_sensor and self.depth_sensor.supports(rs.option.visual_preset):
            self.depth_sensor.set_option(rs.option.visual_preset, float(preset_val))

    def get_visual_preset(self):
        """Gets depth sensor visual preset index."""
        if self.depth_sensor and self.depth_sensor.supports(rs.option.visual_preset):
            return int(self.depth_sensor.get_option(rs.option.visual_preset))
        return 0

    def set_exposure(self, exposure_us):
        """Sets color camera exposure time in microseconds (disables auto-exposure)."""
        if self.color_sensor and self.color_sensor.supports(rs.option.exposure):
            # Disable auto exposure first so manual exposure takes effect
            if self.color_sensor.supports(rs.option.enable_auto_exposure):
                self.color_sensor.set_option(rs.option.enable_auto_exposure, 0.0)
            self.color_sensor.set_option(rs.option.exposure, float(exposure_us))

    def set_auto_exposure(self, enable=True):
        """Enables or disables auto-exposure on the color camera."""
        if self.color_sensor and self.color_sensor.supports(rs.option.enable_auto_exposure):
            self.color_sensor.set_option(rs.option.enable_auto_exposure, 1.0 if enable else 0.0)
            
    def set_white_balance(self, value_kelvin):
        """Sets manual white balance (disables auto white balance)."""
        if self.color_sensor and self.color_sensor.supports(rs.option.white_balance):
            if self.color_sensor.supports(rs.option.enable_auto_white_balance):
                self.color_sensor.set_option(rs.option.enable_auto_white_balance, 0.0)
            self.color_sensor.set_option(rs.option.white_balance, float(value_kelvin))

    def set_auto_white_balance(self, enable=True):
        """Enables or disables auto white balance on the color camera."""
        if self.color_sensor and self.color_sensor.supports(rs.option.enable_auto_white_balance):
            self.color_sensor.set_option(rs.option.enable_auto_white_balance, 1.0 if enable else 0.0)

    def get_laser_power(self):
        """Gets the IR projector laser power in milliwatts."""
        if self.depth_sensor and self.depth_sensor.supports(rs.option.laser_power):
            return self.depth_sensor.get_option(rs.option.laser_power)
        return 150.0

    def get_emitter_state(self):
        """Gets the IR emitter state: 0 = Off, 1 = On, 2 = Auto."""
        if self.depth_sensor and self.depth_sensor.supports(rs.option.emitter_enabled):
            return int(self.depth_sensor.get_option(rs.option.emitter_enabled))
        return 1

    def get_exposure(self):
        """Gets color camera exposure time in microseconds."""
        if self.color_sensor and self.color_sensor.supports(rs.option.exposure):
            return self.color_sensor.get_option(rs.option.exposure)
        return 1560.0

    def get_auto_exposure(self):
        """Gets color camera auto-exposure enabled state."""
        if self.color_sensor and self.color_sensor.supports(rs.option.enable_auto_exposure):
            return bool(self.color_sensor.get_option(rs.option.enable_auto_exposure))
        return True

    def get_frames(self):
        """
        Wait for frames, process alignment, and return (color_image, depth_image, depth_frame)
        """
        frames = self.pipeline.wait_for_frames()
        aligned_frames = self.align.process(frames)
        depth_frame = aligned_frames.get_depth_frame()
        color_frame = aligned_frames.get_color_frame()
        
        if not depth_frame or not color_frame:
            return None, None, None
            
        color_image = np.asanyarray(color_frame.get_data()).copy()
        depth_image = np.asanyarray(depth_frame.get_data()).copy()
        return color_image, depth_image, depth_frame

    def get_3d_coordinates(self, pixel_x, pixel_y, depth_frame):
        """
        Converts 2D pixel coordinates and depth to real-world 3D coordinates (X, Y, Z) in meters.
        Supports robust searching in a neighborhood if the center pixel has invalid depth (glare/holes).
        """
        px = int(max(0, min(pixel_x, self.width - 1)))
        py = int(max(0, min(pixel_y, self.height - 1)))
        
        distance = depth_frame.get_distance(px, py)
        
        # Fallback: if depth is invalid (0.0), search a small window (up to 9x9) for valid depth
        if distance <= 0:
            valid_distances = []
            for r in range(1, 5): # search up to radius of 4 pixels
                for dx in range(-r, r + 1):
                    for dy in range(-r, r + 1):
                        nx = px + dx
                        ny = py + dy
                        if 0 <= nx < self.width and 0 <= ny < self.height:
                            dist = depth_frame.get_distance(nx, ny)
                            if dist > 0:
                                valid_distances.append(dist)
                if valid_distances:
                    distance = float(np.median(valid_distances))
                    break
                    
        if distance > 0:
            point_3d = rs.rs2_deproject_pixel_to_point(self.intrinsics, [px, py], distance)
            return point_3d # [X, Y, Z] in meters
        return None

    def stop(self):
        if self.pipeline:
            try:
                self.pipeline.stop()
            except RuntimeError:
                pass
