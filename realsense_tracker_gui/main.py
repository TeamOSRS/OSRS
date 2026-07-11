import sys
import os
import time
from datetime import datetime
import cv2
import numpy as np
import pyrealsense2 as rs
# pyrefly: ignore [missing-import]
import pyqtgraph as pg

# pyrefly: ignore [missing-import]
from PySide6 import QtCore, QtGui, QtWidgets
from camera import RealSenseCamera
from ball_tracker import BallTracker
from robot_comms import RobotCommunicator, CoordinateFilter3D

# Ensure absolute captures directory exists relative to this file
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
CAPTURES_DIR = os.path.join(PROJECT_DIR, "captures")
os.makedirs(CAPTURES_DIR, exist_ok=True)


class VideoLabel(QtWidgets.QLabel):
    """
    A custom QLabel that preserves aspect ratio while dynamically scaling its pixmap
    to fit the widget size. Prevents the window from expanding layout issues.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(100, 100)
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.current_pixmap = None
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

    def setPixmap(self, pixmap):
        self.current_pixmap = pixmap
        self.update_pixmap()

    def update_pixmap(self):
        if self.current_pixmap and not self.current_pixmap.isNull():
            scaled = self.current_pixmap.scaled(
                self.size(),
                QtCore.Qt.KeepAspectRatio,
                QtCore.Qt.SmoothTransformation
            )
            super().setPixmap(scaled)
        else:
            super().setPixmap(QtGui.QPixmap())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_pixmap()


class LabeledSlider(QtWidgets.QWidget):
    """
    A custom widget combining a label, a slider, and a value display layout.
    """
    valueChanged = QtCore.Signal(int)

    def __init__(self, label_text, min_val, max_val, default_val, suffix="", parent=None):
        super().__init__(parent)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.name_label = QtWidgets.QLabel(label_text)
        self.name_label.setFixedWidth(90)
        self.name_label.setStyleSheet("color: #8b949e; font-size: 11px;")

        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider.setRange(min_val, max_val)
        self.slider.setValue(default_val)
        self.slider.setFixedHeight(20)
        self.slider.valueChanged.connect(self.on_value_changed)

        self.suffix = suffix
        self.val_label = QtWidgets.QLabel(f"{default_val}{suffix}")
        self.val_label.setFixedWidth(50)
        self.val_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.val_label.setStyleSheet("color: #58a6ff; font-weight: bold; font-size: 11px;")

        layout.addWidget(self.name_label)
        layout.addWidget(self.slider)
        layout.addWidget(self.val_label)

    def on_value_changed(self, val):
        self.val_label.setText(f"{val}{self.suffix}")
        self.valueChanged.emit(val)

    def setValue(self, val):
        self.slider.setValue(int(val))

    def value(self):
        return self.slider.value()

    def setEnabled(self, enabled):
        super().setEnabled(enabled)
        self.slider.setEnabled(enabled)
        self.name_label.setEnabled(enabled)
        self.val_label.setEnabled(enabled)


class CollapsibleSection(QtWidgets.QWidget):
    """
    A custom collapsible container widget for sidebar options.
    """
    def __init__(self, title, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.toggle_btn = QtWidgets.QPushButton(f"▼  {title}")
        self.toggle_btn.setObjectName("collapsibleHeader")
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.setChecked(True)
        self.toggle_btn.clicked.connect(self.toggle_content)
        self.toggle_btn.setStyleSheet("""
            QPushButton#collapsibleHeader {
                background-color: #21262d;
                color: #c9d1d9;
                border: 1px solid #30363d;
                border-radius: 4px;
                text-align: left;
                padding: 8px 12px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton#collapsibleHeader:hover {
                background-color: #30363d;
            }
        """)

        layout.addWidget(self.toggle_btn)

        self.content_area = QtWidgets.QWidget()
        self.content_layout = QtWidgets.QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(12, 6, 12, 12)
        self.content_layout.setSpacing(8)
        layout.addWidget(self.content_area)

    def toggle_content(self, checked):
        if checked:
            self.toggle_btn.setText(self.toggle_btn.text().replace("▶", "▼"))
            self.content_area.setVisible(True)
        else:
            self.toggle_btn.setText(self.toggle_btn.text().replace("▼", "▶"))
            self.content_area.setVisible(False)

    def addWidget(self, widget):
        self.content_layout.addWidget(widget)

    def addLayout(self, layout):
        self.content_layout.addLayout(layout)


class CoverageGrid(QtWidgets.QWidget):
    """
    A custom 3x3 grid widget representing the camera lens coverage sectors.
    Turns green as checkerboard poses are successfully captured in corresponding sectors.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        self.cells = {}
        for r in range(3):
            for c in range(3):
                cell = QtWidgets.QFrame()
                cell.setFixedSize(28, 28)
                cell.setStyleSheet("background-color: #161b22; border: 1px solid #30363d; border-radius: 3px;")
                layout.addWidget(cell, r, c)
                self.cells[(r, c)] = cell

    def set_cell_active(self, r, c, active=True):
        if (r, c) in self.cells:
            color = "#2ea043" if active else "#161b22"
            border = "#3fb950" if active else "#30363d"
            self.cells[(r, c)].setStyleSheet(f"background-color: {color}; border: 1px solid {border}; border-radius: 3px;")

    def reset_grid(self):
        for r in range(3):
            for c in range(3):
                self.set_cell_active(r, c, False)


class CameraWorker(QtCore.QThread):
    """
    Thread-safe background worker running the RealSense capture pipeline.
    Calculates ball tracking, checkerboard calibration, and telemetry updates.
    """
    frame_ready = QtCore.Signal(np.ndarray, np.ndarray, np.ndarray, np.ndarray, bool, tuple, object)
    error_occurred = QtCore.Signal(str)
    fps_updated = QtCore.Signal(float)
    camera_started = QtCore.Signal()
    
    # Calibration signals
    calibration_update = QtCore.Signal(np.ndarray, object, bool, int, float, float, float, float, str)
    calib_frame_captured = QtCore.Signal(int, float, float, float, float, str, int, int)
    calib_frame_rejected = QtCore.Signal(str)
    calib_success = QtCore.Signal(float, np.ndarray, np.ndarray)
    calib_error = QtCore.Signal(str)

    def __init__(self, cam, tracker):
        super().__init__()
        self.cam = cam
        self.tracker = tracker
        self.running = True
        self.rgb_enabled = True
        self.depth_enabled = True
        self.hsv_enabled = True
        
        # Calibration state
        self.calib_mode = False
        self.calib_rows = 6
        self.calib_cols = 8
        self.calib_square_size = 0.025
        self.calib_auto_capture = True
        self.manual_capture_requested = False
        
        # Calibration storage
        self.calib_img_points = []
        self.calib_obj_points = []
        self.calib_sectors = { (r, c): [] for r in range(3) for c in range(3) }
        
        self.last_capture_time = 0.0
        self.min_capture_cooldown = 1.5
        self.min_sharpness = 100.0
        
        self.camera_matrix = None
        self.dist_coeffs = None

        # Thread-safe control bound copies
        self.hsv_lower = self.tracker.hsv_lower.copy()
        self.hsv_upper = self.tracker.hsv_upper.copy()

        # Ball tracking trajectory path history
        self.trajectory_points = []
        self.max_history_len = 32
        
        # ArUco trajectories & colors
        self.trajectories = {}
        self.color_palette = [
            (0, 0, 255),    # Red
            (0, 255, 0),    # Green
            (255, 0, 0),    # Blue
            (0, 255, 255),  # Yellow
            (255, 0, 255),  # Magenta
            (255, 255, 0),  # Cyan
            (255, 128, 0),  # Orange
            (0, 128, 255),  # Sky Blue
            (128, 0, 255),  # Purple
            (0, 255, 128)   # Spring Green
        ]

        # Target tracking state (HSV ball vs ArUco marker)
        self.target_mode = "hsv"
        self.aruco_dict_id = cv2.aruco.DICT_4X4_50
        self.aruco_marker_size = 0.05  # meters
        self.aruco_target_id = 1  # default to track ID 1 (user marker)
        
        # Reference frame offset settings
        self.aruco_ref_enabled = False
        self.aruco_ref_id = 0
        self.ref_rvec = None
        self.ref_tvec = None
        self.aruco_ref_mode = "camera"
        self.static_ref_rvec = None
        self.static_ref_tvec = None

    @QtCore.Slot(str)
    def set_target_mode(self, mode):
        self.target_mode = mode

    @QtCore.Slot(int)
    def set_aruco_dictionary(self, dict_id):
        self.aruco_dict_id = dict_id

    @QtCore.Slot(float)
    def set_aruco_marker_size(self, size_meters):
        self.aruco_marker_size = size_meters

    @QtCore.Slot(int)
    def set_aruco_target_id(self, target_id):
        self.aruco_target_id = target_id

    @QtCore.Slot(bool)
    def set_aruco_ref_enabled(self, enabled):
        self.aruco_ref_enabled = enabled
        if not enabled:
            self.ref_rvec = None
            self.ref_tvec = None

    @QtCore.Slot(str)
    def set_aruco_ref_mode(self, mode):
        self.aruco_ref_mode = mode

    @QtCore.Slot(object, object)
    def update_static_ref(self, rvec, tvec):
        if rvec is not None and tvec is not None:
            self.static_ref_rvec = np.array(rvec, dtype=np.float32)
            self.static_ref_tvec = np.array(tvec, dtype=np.float32)
        else:
            self.static_ref_rvec = None
            self.static_ref_tvec = None

    @QtCore.Slot(int)
    def set_aruco_ref_id(self, ref_id):
        self.aruco_ref_id = ref_id
        self.ref_rvec = None
        self.ref_tvec = None

    @QtCore.Slot(np.ndarray, np.ndarray)
    def update_hsv_bounds(self, lower, upper):
        self.hsv_lower = lower.copy()
        self.hsv_upper = upper.copy()

    @QtCore.Slot(bool)
    def set_rgb_enabled(self, enabled):
        self.rgb_enabled = enabled

    @QtCore.Slot(bool)
    def set_depth_enabled(self, enabled):
        self.depth_enabled = enabled

    @QtCore.Slot(bool)
    def set_hsv_enabled(self, enabled):
        self.hsv_enabled = enabled

    @QtCore.Slot(bool)
    def set_calibration_mode(self, enabled):
        self.calib_mode = enabled

    @QtCore.Slot(int, int, float, bool)
    def update_calib_settings(self, cols, rows, square_size, auto_capture):
        self.calib_cols = cols
        self.calib_rows = rows
        self.calib_square_size = square_size
        self.calib_auto_capture = auto_capture

    @QtCore.Slot()
    def request_manual_capture(self):
        self.manual_capture_requested = True

    @QtCore.Slot()
    def clear_calibration_data(self):
        self.calib_img_points.clear()
        self.calib_obj_points.clear()
        self.calib_sectors = { (r, c): [] for r in range(3) for c in range(3) }
        self.camera_matrix = None
        self.dist_coeffs = None

    @QtCore.Slot()
    def run_camera_calibration(self):
        if len(self.calib_img_points) < 3:
            self.calib_error.emit("Calibration requires at least 3 valid checkerboard frames.")
            return
        try:
            ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(
                self.calib_obj_points,
                self.calib_img_points,
                (self.cam.width, self.cam.height),
                None,
                None
            )
            self.camera_matrix = mtx
            self.dist_coeffs = dist
            self.calib_success.emit(float(ret), mtx, dist)
        except Exception as e:
            self.calib_error.emit(f"Calibration computation failed: {e}")

    def capture_frame_internal(self, gray_img, corners, objp, sector_r, sector_c, tilt_x, tilt_y, distance, sharpness, current_time, manual=False):
        self.calib_img_points.append(corners)
        self.calib_obj_points.append(objp)
        if sector_r >= 0 and sector_c >= 0:
            self.calib_sectors[(sector_r, sector_c)].append((tilt_x, tilt_y))
        
        self.last_capture_time = current_time
        frame_idx = len(self.calib_img_points)
        self.calib_frame_captured.emit(
            frame_idx,
            sharpness,
            tilt_x,
            tilt_y,
            distance,
            f"Sector ({sector_r},{sector_c})",
            sector_r,
            sector_c
        )

    def run(self):
        try:
            self.cam.start()
            self.camera_started.emit()
        except Exception as e:
            self.error_occurred.emit(f"Failed to initialize RealSense camera: {e}")
            return

        frame_counter = 0
        fps_timer = QtCore.QElapsedTimer()
        fps_timer.start()

        while self.running:
            # If all modules disabled, sleep to reduce CPU usage
            if not self.rgb_enabled and not self.depth_enabled and not self.hsv_enabled and not self.calib_mode:
                self.msleep(30)
                continue

            try:
                color_image, depth_image, depth_frame = self.cam.get_frames()
            except Exception:
                self.msleep(5)
                continue

            if color_image is None or depth_image is None:
                self.msleep(5)
                continue

            frame_counter += 1
            if fps_timer.elapsed() >= 1000:
                fps = frame_counter / (fps_timer.elapsed() / 1000.0)
                self.fps_updated.emit(fps)
                frame_counter = 0
                fps_timer.restart()

            if not self.calib_mode:
                # Process tracking on RGB image
                mask = np.zeros((self.cam.height, self.cam.width), dtype=np.uint8)
                tracker_status = False
                coords = (0.0, 0.0, 0.0)
                target_pixel = None
                
                # Save raw color image before drawing tracking overlays
                raw_color = color_image.copy()
                
                # Setup ArUco data dict for GUI telemetry
                detected_markers_list = []
                ref_active = False
                target_name = "--"
                       # 1. ALWAYS run ArUco detection on raw color copy
                all_corners = None
                all_ids = None
                try:
                    dictionary = cv2.aruco.getPredefinedDictionary(self.aruco_dict_id)
                    params = cv2.aruco.DetectorParameters()
                    # Tune detection parameters to detect small, blurry, or low-contrast markers in high-glare environments
                    params.adaptiveThreshWinSizeMin = 3
                    params.adaptiveThreshWinSizeMax = 23
                    params.adaptiveThreshWinSizeStep = 4
                    params.adaptiveThreshConstant = 4  # Default is 7; reducing helps find dimmer borders
                    params.minMarkerDistanceRate = 0.02
                    params.perspectiveRemovePixelPerCell = 8
                    detector = cv2.aruco.ArucoDetector(dictionary, params)
                    all_corners, all_ids, _ = detector.detectMarkers(raw_color)
                except Exception:
                    pass

                # 2. Reference configuration based on mode
                if self.aruco_ref_mode == "static_world" and self.static_ref_rvec is not None and self.static_ref_tvec is not None:
                    self.ref_rvec = self.static_ref_rvec
                    self.ref_tvec = self.static_ref_tvec
                    ref_active = True
                elif self.aruco_ref_mode == "live_marker" and all_ids is not None:
                    try:
                        ids_flat = all_ids.flatten()
                        matching = np.where(ids_flat == self.aruco_ref_id)[0]
                        if len(matching) > 0:
                            ref_idx = matching[0]
                            marker_corners = all_corners[ref_idx][0]
                            
                            # Draw detected markers outline first if reference marker is live
                            cv2.aruco.drawDetectedMarkers(color_image, all_corners, all_ids)
                            
                            cam_mat = self.camera_matrix
                            dist_c = self.dist_coeffs
                            if cam_mat is None or dist_c is None:
                                try:
                                    cam_mat = np.array([
                                        [self.cam.intrinsics.fx, 0.0, self.cam.intrinsics.ppx],
                                        [0.0, self.cam.intrinsics.fy, self.cam.intrinsics.ppy],
                                        [0.0, 0.0, 1.0]
                                    ], dtype=np.float32)
                                    dist_c = np.array(self.cam.intrinsics.coeffs, dtype=np.float32)
                                except Exception:
                                    cam_mat = np.array([
                                        [615.0, 0.0, self.cam.width / 2.0],
                                        [0.0, 615.0, self.cam.height / 2.0],
                                        [0.0, 0.0, 1.0]
                                    ], dtype=np.float32)
                                    dist_c = np.zeros(5, dtype=np.float32)
                                    
                            s = self.aruco_marker_size
                            half_s = s / 2.0
                            obj_points = np.array([
                                [-half_s,  half_s, 0.0],
                                [ half_s,  half_s, 0.0],
                                [ half_s, -half_s, 0.0],
                                [-half_s, -half_s, 0.0]
                             ], dtype=np.float32)
                             
                            solve_ret, rvec, tvec = cv2.solvePnP(obj_points, marker_corners, cam_mat, dist_c)
                            if solve_ret:
                                self.ref_rvec = rvec
                                self.ref_tvec = tvec
                                ref_active = True
                                cv2.drawFrameAxes(color_image, cam_mat, dist_c, rvec, tvec, s * 1.5, 3)
                    except Exception:
                        pass
                else:
                    ref_active = False
                    self.ref_rvec = None
                    self.ref_tvec = None

                # 3. Process and draw ALL detected ArUco markers (so they show up in screen & table)
                if all_ids is not None:
                    try:
                        ids_flat = all_ids.flatten()
                        cam_mat = self.camera_matrix
                        dist_c = self.dist_coeffs
                        if cam_mat is None or dist_c is None:
                            try:
                                cam_mat = np.array([
                                    [self.cam.intrinsics.fx, 0.0, self.cam.intrinsics.ppx],
                                    [0.0, self.cam.intrinsics.fy, self.cam.intrinsics.ppy],
                                    [0.0, 0.0, 1.0]
                                ], dtype=np.float32)
                                dist_c = np.array(self.cam.intrinsics.coeffs, dtype=np.float32)
                            except Exception:
                                cam_mat = np.array([
                                    [615.0, 0.0, self.cam.width / 2.0],
                                    [0.0, 615.0, self.cam.height / 2.0],
                                    [0.0, 0.0, 1.0]
                                ], dtype=np.float32)
                                dist_c = np.zeros(5, dtype=np.float32)
                                
                        s = self.aruco_marker_size
                        half_s = s / 2.0
                        obj_points = np.array([
                            [-half_s,  half_s, 0.0],
                            [ half_s,  half_s, 0.0],
                            [ half_s, -half_s, 0.0],
                            [-half_s, -half_s, 0.0]
                        ], dtype=np.float32)
                        
                        # Draw outlines for all detected markers
                        cv2.aruco.drawDetectedMarkers(color_image, all_corners, all_ids)
                        
                        for idx, m_id in enumerate(ids_flat):
                            marker_corners = all_corners[idx][0]
                            solve_ret, rvec, tvec = cv2.solvePnP(obj_points, marker_corners, cam_mat, dist_c)
                            if solve_ret:
                                # Draw axes
                                cv2.drawFrameAxes(color_image, cam_mat, dist_c, rvec, tvec, s * 1.5, 3)
                                
                                # Position in camera coordinates
                                x_c = float(tvec[0][0])
                                y_c = float(tvec[1][0])
                                z_c = float(tvec[2][0])
                                dist_c_val = float(np.linalg.norm(tvec))
                                
                                # Apply reference transform if active
                                if self.aruco_ref_enabled and ref_active and self.ref_rvec is not None and self.ref_tvec is not None:
                                    R_ref, _ = cv2.Rodrigues(self.ref_rvec)
                                    T_ref = self.ref_tvec
                                    T_rel = R_ref.T @ (tvec - T_ref)
                                    x_w = float(T_rel[0][0])
                                    y_w = float(T_rel[1][0])
                                    z_w = float(T_rel[2][0])
                                    dist_w = float(np.linalg.norm(T_rel))
                                else:
                                    x_w, y_w, z_w, dist_w = x_c, y_c, z_c, dist_c_val
                                    
                                detected_markers_list.append({
                                    "id": int(m_id),
                                    "x": x_w,
                                    "y": y_w,
                                    "z": z_w,
                                    "dist": dist_w
                                })
                                
                                # Draw coordinate readout text next to each marker
                                center_x = int(np.mean(marker_corners[:, 0]))
                                center_y = int(np.mean(marker_corners[:, 1]))
                                ref_lbl = "Rel" if (self.aruco_ref_enabled and ref_active) else "Cam"
                                cv2.putText(
                                    color_image,
                                    f"ID {m_id} ({ref_lbl}): {x_w:+.2f}, {y_w:+.2f}, {z_w:+.2f}m",
                                    (center_x + 10, center_y - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX,
                                    0.5,
                                    (0, 255, 0),
                                    2,
                                )
                                
                        # Outline all detected marker masks
                        for idx in range(len(ids_flat)):
                            cv2.fillPoly(mask, [all_corners[idx][0].astype(np.int32)], 255)
                            
                        # Update trajectories for all detected markers
                        detected_ids = set(ids_flat)
                        for m_id in detected_ids:
                            if m_id not in self.trajectories:
                                self.trajectories[m_id] = []
                            idx = np.where(ids_flat == m_id)[0][0]
                            marker_corners = all_corners[idx][0]
                            center_x = int(np.mean(marker_corners[:, 0]))
                            center_y = int(np.mean(marker_corners[:, 1]))
                            self.trajectories[m_id].append((center_x, center_y))
                            if len(self.trajectories[m_id]) > self.max_history_len:
                                self.trajectories[m_id].pop(0)
                                
                        # Retract trajectories of markers that are not detected in this frame
                        for m_id in list(self.trajectories.keys()):
                            if m_id not in detected_ids:
                                if len(self.trajectories[m_id]) > 0:
                                    self.trajectories[m_id].pop(0)
                                if len(self.trajectories[m_id]) == 0:
                                    del self.trajectories[m_id]
                                    
                        # Draw trajectories for all active markers
                        for m_id, points in list(self.trajectories.items()):
                            color = self.color_palette[m_id % len(self.color_palette)]
                            for i in range(1, len(points)):
                                if points[i - 1] is None or points[i] is None:
                                    continue
                                thickness = int(np.sqrt(self.max_history_len / float(i + 1)) * 2.5)
                                cv2.line(
                                    color_image,
                                    points[i - 1],
                                    points[i],
                                    color,
                                    thickness,
                                )
                    except Exception as e:
                        import traceback
                        traceback.print_exc()

                # 4. Target Tracking Logic (Ball or Scissors)
                if self.target_mode in ["hsv", "hsv_scissors"]:
                    if self.target_mode == "hsv":
                        target_name = "Tennis Ball (HSV)"
                    else:
                        target_name = "Orange Scissors (HSV)"
                        
                    if self.rgb_enabled or self.hsv_enabled:
                        if self.target_mode == "hsv":
                            mask_hsv, center, radius = self.tracker.process_frame(
                                raw_color, self.hsv_lower, self.hsv_upper
                            )
                            bbox = None
                        else:
                            mask_hsv, center, bbox = self.tracker.process_frame_centroid(
                                raw_color, self.hsv_lower, self.hsv_upper
                            )
                            radius = 0
                            
                        # Merge HSV mask with ArUco mask
                        mask = cv2.bitwise_or(mask, mask_hsv)
                            
                        if center is not None:
                            if self.target_mode == "hsv":
                                cv2.circle(color_image, center, int(radius), (0, 255, 255), 2)
                                cv2.circle(color_image, center, 5, (0, 0, 255), -1)
                            else:
                                # Draw orange bounding box and crosshair for scissors
                                x_b, y_b, w_b, h_b = bbox
                                cv2.rectangle(color_image, (x_b, y_b), (x_b + w_b, y_b + h_b), (0, 165, 255), 2)
                                cv2.drawMarker(color_image, center, (0, 0, 255), cv2.MARKER_CROSS, 15, 2)
                                
                            target_pixel = (float(center[0]), float(center[1]))
                            point_3d = self.cam.get_3d_coordinates(center[0], center[1], depth_frame)
                            if point_3d is not None:
                                tracker_status = True
                                coords = point_3d
                                
                                # Apply reference transform if active
                                if self.aruco_ref_enabled and ref_active and self.ref_rvec is not None and self.ref_tvec is not None:
                                    R_ref, _ = cv2.Rodrigues(self.ref_rvec)
                                    T_ref = self.ref_tvec
                                    P_obj = np.array(point_3d, dtype=np.float32).reshape(3, 1)
                                    T_rel = R_ref.T @ (P_obj - T_ref)
                                    coords = (float(T_rel[0][0]), float(T_rel[1][0]), float(T_rel[2][0]))
                                    
                                x_3d, y_3d, z_3d = coords
                                ref_lbl = "Rel" if (self.aruco_ref_enabled and ref_active) else "Cam"
                                label_text = f"Ball ({ref_lbl}): {z_3d:.2f}m" if self.target_mode == "hsv" else f"Scissors ({ref_lbl}): {z_3d:.2f}m"
                                cv2.putText(
                                    color_image,
                                    label_text,
                                    (center[0] + 10, center[1] - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX,
                                    0.6,
                                    (0, 255, 255) if self.target_mode == "hsv" else (0, 165, 255),
                                    2,
                                )
                                self.trajectory_points.append(center)
                        else:
                            self.trajectory_points.clear()

                        if len(self.trajectory_points) > self.max_history_len:
                            self.trajectory_points.pop(0)

                        for i in range(1, len(self.trajectory_points)):
                            if self.trajectory_points[i - 1] is None or self.trajectory_points[i] is None:
                                continue
                            thickness = int(np.sqrt(self.max_history_len / float(i + 1)) * 2.5)
                            color_line = (0, 0, 255) if self.target_mode == "hsv" else (0, 100, 255)
                            cv2.line(
                                color_image,
                                self.trajectory_points[i - 1],
                                self.trajectory_points[i],
                                color_line,
                                thickness,
                            )
                    else:
                        self.trajectory_points.clear()
                        
                elif self.target_mode == "aruco":
                    # If target mode is ArUco, find target marker index for primary coordinates reporting
                    if all_ids is not None:
                        ids_flat = all_ids.flatten()
                        target_idx = None
                        if self.aruco_target_id == -1:
                            target_idx = 0
                        else:
                            matching = np.where(ids_flat == self.aruco_target_id)[0]
                            if len(matching) > 0:
                                target_idx = matching[0]
                                
                        if target_idx is not None:
                            t_id = int(ids_flat[target_idx])
                            target_name = f"Marker ID {t_id}"
                            
                            target_corners = all_corners[target_idx][0]
                            target_pixel = (float(np.mean(target_corners[:, 0])), float(np.mean(target_corners[:, 1])))
                            
                            # Get coordinates from detected list
                            target_info = [m for m in detected_markers_list if m["id"] == t_id]
                            if len(target_info) > 0:
                                tracker_status = True
                                coords = (target_info[0]["x"], target_info[0]["y"], target_info[0]["z"])

                depth_colormap = np.zeros((self.cam.height, self.cam.width, 3), dtype=np.uint8)
                if self.depth_enabled:
                    try:
                        non_zero = depth_image[depth_image > 0]
                        if len(non_zero) > 0:
                            hist, _ = np.histogram(non_zero, bins=0xFFFF, range=(1, 0x10000))
                            cdf = hist.cumsum()
                            cdf_normalized = (cdf * 254 / cdf[-1]) + 1
                            mapped_depth = np.zeros_like(depth_image, dtype=np.uint8)
                            mapped_depth[depth_image > 0] = cdf_normalized[depth_image[depth_image > 0] - 1].astype(np.uint8)
                            mapped_depth[depth_image > 0] = 255 - mapped_depth[depth_image > 0]
                            depth_colormap = cv2.applyColorMap(mapped_depth, cv2.COLORMAP_JET)
                            depth_colormap[depth_image == 0] = [0, 0, 0]
                        else:
                            depth_colormap = cv2.applyColorMap(
                                cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET
                            )
                    except Exception:
                        depth_colormap = cv2.applyColorMap(
                            cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET
                        )

                # Assemble telemetry data dict
                aruco_data = {
                    "detected_markers": detected_markers_list,
                    "ref_active": ref_active,
                    "ref_id": self.aruco_ref_id,
                    "target_name": target_name,
                    "ref_tvec": self.ref_tvec.tolist() if (ref_active and self.ref_tvec is not None) else None,
                    "ref_rvec": self.ref_rvec.tolist() if (ref_active and self.ref_rvec is not None) else None,
                    "target_pixel": target_pixel,
                }

                self.frame_ready.emit(
                    color_image.copy(),
                    raw_color.copy(),
                    depth_colormap.copy(),
                    mask.copy(),
                    tracker_status,
                    coords,
                    aruco_data
                )
            else:
                try:
                    # Calibration Processing
                    gray = cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY)
                    sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())

                    # Find checkerboard corners
                    ret, corners = cv2.findChessboardCorners(
                        gray, 
                        (self.calib_cols, self.calib_rows), 
                        cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_NORMALIZE_IMAGE
                    )

                    corners_found = 0
                    corners_detected = False
                    board_tilt_x = 0.0
                    board_tilt_y = 0.0
                    board_distance = 0.0
                    coverage_sector = "--"
                    sector_r, sector_c = -1, -1

                    annotated_img = color_image.copy()

                    if ret:
                        corners_detected = True
                        corners_found = len(corners)

                        try:
                            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
                            cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
                        except Exception:
                            pass

                        cv2.drawChessboardCorners(annotated_img, (self.calib_cols, self.calib_rows), corners, ret)

                        # SolvePnP for pose feedback
                        cam_mat = self.camera_matrix
                        if cam_mat is None:
                            cam_mat = np.array([
                                [615.0, 0.0, self.cam.width / 2.0],
                                [0.0, 615.0, self.cam.height / 2.0],
                                [0.0, 0.0, 1.0]
                            ], dtype=np.float32)
                        dist_c = self.dist_coeffs if self.dist_coeffs is not None else np.zeros(5, dtype=np.float32)

                        objp = np.zeros((self.calib_cols * self.calib_rows, 3), np.float32)
                        objp[:, :2] = np.mgrid[0:self.calib_cols, 0:self.calib_rows].T.reshape(-1, 2)
                        objp *= self.calib_square_size

                        try:
                            solve_ret, rvec, tvec = cv2.solvePnP(objp, corners, cam_mat, dist_c)
                            if solve_ret:
                                # Project 3D axis
                                axis_length = self.calib_square_size * 2
                                axis = np.float32([[axis_length, 0, 0], [0, axis_length, 0], [0, 0, -axis_length], [0, 0, 0]]).reshape(-1, 3)
                                imgpts, _ = cv2.projectPoints(axis, rvec, tvec, cam_mat, dist_c)
                                imgpts = imgpts.astype(int)
                                origin = tuple(imgpts[3].ravel())
                                cv2.line(annotated_img, origin, tuple(imgpts[0].ravel()), (0, 0, 255), 3) # X axis Red
                                cv2.line(annotated_img, origin, tuple(imgpts[1].ravel()), (0, 255, 0), 3) # Y axis Green
                                cv2.line(annotated_img, origin, tuple(imgpts[2].ravel()), (255, 0, 0), 3) # Z axis Blue

                                board_distance = float(np.linalg.norm(tvec))

                                R, _ = cv2.Rodrigues(rvec)
                                normal_cam = R[:, 2]
                                board_tilt_x = float(np.degrees(np.arcsin(np.clip(normal_cam[1], -1.0, 1.0))))
                                board_tilt_y = float(np.degrees(np.arctan2(normal_cam[0], normal_cam[2])))

                                # Determine coverage sector
                                board_center = np.mean(corners, axis=0)[0]
                                cell_w = self.cam.width / 3.0
                                cell_h = self.cam.height / 3.0
                                sector_c = int(board_center[0] // cell_w)
                                sector_r = int(board_center[1] // cell_h)
                                sector_c = max(0, min(2, sector_c))
                                sector_r = max(0, min(2, sector_r))

                                sectors_labels = [
                                    ["Top Left", "Top Center", "Top Right"],
                                    ["Mid Left", "Mid Center", "Mid Right"],
                                    ["Bot Left", "Bot Center", "Bot Right"]
                                ]
                                coverage_sector = sectors_labels[sector_r][sector_c]

                                # Auto capture logic
                                if self.calib_auto_capture:
                                    if time.time() - self.last_capture_time >= self.min_capture_cooldown:
                                        if sharpness >= self.min_sharpness:
                                            sector_poses = self.calib_sectors[(sector_r, sector_c)]
                                            is_unique = True
                                            for prev_tx, prev_ty in sector_poses:
                                                angle_diff = np.sqrt((board_tilt_x - prev_tx)**2 + (board_tilt_y - prev_ty)**2)
                                                if angle_diff < 10.0:
                                                    is_unique = False
                                                    break
                                            if is_unique:
                                                self.capture_frame_internal(gray, corners, objp, sector_r, sector_c, board_tilt_x, board_tilt_y, board_distance, sharpness, time.time())
                        except Exception:
                            pass

                    # Manual capture request
                    if self.manual_capture_requested:
                        self.manual_capture_requested = False
                        if corners_detected:
                            objp = np.zeros((self.calib_cols * self.calib_rows, 3), np.float32)
                            objp[:, :2] = np.mgrid[0:self.calib_cols, 0:self.calib_rows].T.reshape(-1, 2)
                            objp *= self.calib_square_size
                            self.capture_frame_internal(gray, corners, objp, sector_r, sector_c, board_tilt_x, board_tilt_y, board_distance, sharpness, time.time(), manual=True)
                        else:
                            self.calib_frame_rejected.emit("Manual capture failed: Chessboard corners not found.")

                    # Undistort preview
                    undistorted_img = None
                    if self.camera_matrix is not None and self.dist_coeffs is not None:
                        undistorted_img = cv2.undistort(color_image, self.camera_matrix, self.dist_coeffs)

                    self.calibration_update.emit(
                        annotated_img.copy(),
                        undistorted_img,
                        corners_detected,
                        corners_found,
                        sharpness,
                        board_tilt_x,
                        board_tilt_y,
                        board_distance,
                        coverage_sector
                    )
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    self.msleep(30)

        self.cam.stop()


class MainWindow(QtWidgets.QMainWindow):
    """
    Main dark-themed Qt Window for the RealSense modular viewer and ball tracker.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RealSense Viewer v2.58.1 - Custom Tracker")
        self.resize(1400, 780)
        self.setMinimumSize(900, 500)

        # Style Application in Dark GitHub/RealSense aesthetics
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0c1117;
            }
            QWidget#sidebarContainer {
                background-color: #161b22;
                border-right: 1px solid #30363d;
            }
            QLabel {
                color: #c9d1d9;
                font-family: 'Segoe UI', sans-serif;
            }
            QFrame#viewportCard {
                background-color: #161b22;
                border: 1px solid #30363d;
                border-radius: 6px;
            }
            QFrame#viewportHeader {
                background-color: #21262d;
                border-bottom: 1px solid #30363d;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            QFrame#graphPanel {
                background-color: #161b22;
                border: 1px solid #30363d;
                border-radius: 6px;
            }
            QPushButton#streamActionBtn {
                background-color: transparent;
                border: none;
                color: #8b949e;
                font-size: 13px;
                padding: 4px;
            }
            QPushButton#streamActionBtn:hover {
                color: #58a6ff;
            }
            QPushButton#streamActionBtn:checked {
                color: #ffaa00;
            }
            QStatusBar {
                background-color: #161b22;
                color: #8b949e;
                border-top: 1px solid #30363d;
                font-size: 11px;
            }
            QScrollBar:vertical {
                border: none;
                background: #161b22;
                width: 8px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: #30363d;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #8b949e;
            }
            QComboBox {
                background-color: #21262d;
                border: 1px solid #30363d;
                border-radius: 4px;
                padding: 4px 8px;
                color: #c9d1d9;
            }
            QComboBox::drop-down {
                border: none;
            }
            QCheckBox {
                color: #c9d1d9;
                font-size: 12px;
            }
            QCheckBox::indicator {
                width: 14px;
                height: 14px;
                background-color: #21262d;
                border: 1px solid #30363d;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background-color: #58a6ff;
                border-color: #58a6ff;
            }
        """)

        # Initialize modular backends
        self.cam = RealSenseCamera(width=640, height=480, fps=30)
        self.tracker = BallTracker()

        # Initialize Robot communicator and Coordinate filters
        self.robot_comm = RobotCommunicator()
        self.coord_filter = CoordinateFilter3D()

        # Cache variables
        self.fps = 30.0
        self.last_color_frame = None
        self.last_raw_color_frame = None
        self.last_depth_frame = None
        self.last_mask_frame = None
        
        self.play_rgb = True
        self.play_depth = True
        self.play_hsv = True
        self.graph_visible = False

        # Properties values list for Info panel
        self.info_properties = [
            ("Name", rs.camera_info.name, "Intel RealSense D435I"),
            ("Serial Number", rs.camera_info.serial_number, "347622073229"),
            ("Firmware Version", rs.camera_info.firmware_version, "5.17.0.10"),
            ("Physical Port", rs.camera_info.physical_port, "\\\\?\\usb#vid_8086&pid_0b3a..."),
            ("Debug Op Code", None, "15"),
            ("Advanced Mode", None, "YES"),
            ("Product Id", None, "0B3A"),
            ("Camera Locked", None, "YES"),
            ("Usb Type Descriptor", rs.camera_info.usb_type_descriptor, "3.2"),
            ("Product Line", None, "D400"),
            ("Asic Serial Number", None, "254343082273"),
            ("Firmware Update Id", None, "254343082273"),
            ("Connection Type", None, "USB"),
            ("Imu Type", None, "BMI085"),
        ]
        self.info_value_labels = {}

        # Distance measurements storage
        self.distance_specifications = []
        self.log_file = None
        self.log_writer = None
        self.log_start_time = 0.0
        self.log_frame_count = 0

        # Build UI Structure
        self.setup_ui()
        self.load_persistent_distances()

        # Initialize telemetry data buffers
        self.time_counter = 0
        self.z_history = []
        self.x_history = []
        self.y_history = []
        self.time_history = []

        # Start Camera background thread worker
        self.worker = CameraWorker(self.cam, self.tracker)
        self.load_persistent_world_calibration()
        self.worker.frame_ready.connect(self.on_frame_ready)
        self.worker.fps_updated.connect(self.on_fps_updated)
        self.worker.error_occurred.connect(self.on_error)
        self.worker.camera_started.connect(self.init_camera_sliders)
        
        # Connect calibration signals
        self.worker.calibration_update.connect(self.on_calibration_update)
        self.worker.calib_frame_captured.connect(self.on_calib_frame_captured)
        self.worker.calib_frame_rejected.connect(self.on_calib_frame_rejected)
        self.worker.calib_success.connect(self.on_calib_success)
        self.worker.calib_error.connect(self.on_calib_error)
        
        # Sync tracking target configurations initially
        self.on_tracking_target_changed()
        self.on_aruco_settings_changed()
        
        # Connect reference settings
        self.cmb_ref_mode.currentIndexChanged.connect(self.on_ref_settings_changed)
        self.spin_ref_id.valueChanged.connect(self.on_ref_settings_changed)
        self.btn_calib_world.clicked.connect(self.on_calibrate_world_origin)
        self.btn_clear_world.clicked.connect(self.on_clear_world_calibration)
        self.on_ref_settings_changed()

        # Connect robot settings
        self.btn_robot_connect.clicked.connect(self.on_robot_connect_clicked)
        self.refresh_robot_ports()
        self.on_filter_settings_changed()
        
        self.worker.start()

    def setup_ui(self):
        # Central horizontal layout splitter
        main_widget = QtWidgets.QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QtWidgets.QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ----------------- SIDEBAR PANEL (LEFT) -----------------
        sidebar_container = QtWidgets.QWidget()
        sidebar_container.setObjectName("sidebarContainer")
        sidebar_container.setFixedWidth(310)
        sidebar_layout = QtWidgets.QVBoxLayout(sidebar_container)
        sidebar_layout.setContentsMargins(10, 10, 10, 10)
        sidebar_layout.setSpacing(12)

        # Mode Selection Bar
        mode_layout = QtWidgets.QHBoxLayout()
        mode_layout.setSpacing(2)
        mode_layout.setContentsMargins(0, 0, 0, 4)
        
        self.btn_mode_tracker = QtWidgets.QPushButton("🎾 Tracker")
        self.btn_mode_tracker.setCheckable(True)
        self.btn_mode_tracker.setChecked(True)
        
        self.btn_mode_calib = QtWidgets.QPushButton("📷 Calibration")
        self.btn_mode_calib.setCheckable(True)
        
        self.mode_group = QtWidgets.QButtonGroup(self)
        self.mode_group.addButton(self.btn_mode_tracker)
        self.mode_group.addButton(self.btn_mode_calib)
        self.mode_group.setExclusive(True)
        
        mode_style = """
            QPushButton {
                background-color: #21262d;
                border: 1px solid #30363d;
                color: #8b949e;
                font-weight: bold;
                font-size: 11px;
                padding: 6px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #30363d;
                color: #c9d1d9;
            }
            QPushButton:checked {
                background-color: #1f6feb;
                border-color: #388bfd;
                color: #ffffff;
            }
        """
        self.btn_mode_tracker.setStyleSheet(mode_style)
        self.btn_mode_calib.setStyleSheet(mode_style)
        
        mode_layout.addWidget(self.btn_mode_tracker)
        mode_layout.addWidget(self.btn_mode_calib)
        sidebar_layout.addLayout(mode_layout)

        # Device Panel Card
        device_card = QtWidgets.QFrame()
        device_card.setStyleSheet("background-color: #1f242c; border: 1px solid #30363d; border-radius: 6px;")
        dc_layout = QtWidgets.QVBoxLayout(device_card)
        dc_layout.setContentsMargins(10, 10, 10, 10)
        dc_layout.setSpacing(6)

        # Title
        dev_title = QtWidgets.QLabel("Intel RealSense D435I")
        dev_title.setStyleSheet("font-weight: bold; font-size: 13px; color: #58a6ff; border: none;")
        self.usb_lbl = QtWidgets.QLabel("USB 3.2  |  S/N: 347622073229")
        self.usb_lbl.setStyleSheet("color: #8b949e; font-size: 11px; border: none;")
        self.fw_lbl = QtWidgets.QLabel("FW: 5.17.0.10")
        self.fw_lbl.setStyleSheet("color: #8b949e; font-size: 11px; border: none;")

        dc_layout.addWidget(dev_title)
        dc_layout.addWidget(self.usb_lbl)
        dc_layout.addWidget(self.fw_lbl)

        # Sub-header buttons for device info
        dev_btn_layout = QtWidgets.QHBoxLayout()
        dev_btn_layout.setSpacing(4)
        
        record_btn = QtWidgets.QPushButton("🔴 Record")
        sync_btn = QtWidgets.QPushButton("🔄 Sync")
        self.info_btn = QtWidgets.QPushButton("ℹ Info")
        more_btn = QtWidgets.QPushButton("☰ More")
        
        # Style buttons
        for btn in [record_btn, sync_btn, self.info_btn, more_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #21262d;
                    border: 1px solid #30363d;
                    color: #c9d1d9;
                    font-size: 10px;
                    padding: 4px 6px;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #30363d;
                }
            """)
            dev_btn_layout.addWidget(btn)
        dc_layout.addLayout(dev_btn_layout)

        # More dropdown popup menu
        self.more_menu = QtWidgets.QMenu(self)
        self.more_menu.setStyleSheet("""
            QMenu {
                background-color: #1f242c;
                border: 1px solid #30363d;
                color: #c9d1d9;
            }
            QMenu::item {
                padding: 6px 20px;
            }
            QMenu::item:selected {
                background-color: #30363d;
                color: #58a6ff;
            }
        """)
        self.adv_mode_action = self.more_menu.addAction("Advanced Mode")
        self.adv_mode_action.setCheckable(True)
        self.adv_mode_action.setChecked(True)
        
        hw_reset_action = self.more_menu.addAction("Hardware Reset")
        hw_reset_action.triggered.connect(self.on_hardware_reset)
        
        self.more_menu.addAction("Update Firmware")
        self.more_menu.addAction("Check For Updates")
        self.more_menu.addSeparator()
        self.more_menu.addAction("On-Chip Calibration")
        self.more_menu.addAction("Focal Length Calibration")
        self.more_menu.addAction("Tare Calibration")
        self.more_menu.addAction("Calibration Data")
        self.more_menu.addSeparator()
        self.more_menu.addAction("Recover Logs from Flash")

        more_btn.setMenu(self.more_menu)

        # Visual Preset selection row
        preset_layout = QtWidgets.QHBoxLayout()
        preset_lbl = QtWidgets.QLabel("Preset:")
        preset_lbl.setStyleSheet("color: #8b949e; font-size: 12px; font-weight: bold;")
        self.preset_combo = QtWidgets.QComboBox()
        self.preset_combo.addItems(["Custom", "Default", "Hand", "High Accuracy", "High Density", "Medium Density"])
        self.preset_combo.setCurrentIndex(0)
        self.preset_combo.currentIndexChanged.connect(self.on_preset_changed)

        upload_preset_btn = QtWidgets.QPushButton("📤")
        upload_preset_btn.setToolTip("Load pre-configured device settings")
        upload_preset_btn.clicked.connect(self.load_device_settings)

        download_preset_btn = QtWidgets.QPushButton("📥")
        download_preset_btn.setToolTip("Save current device settings to file")
        download_preset_btn.clicked.connect(self.save_device_settings)
        for btn in [upload_preset_btn, download_preset_btn]:
            btn.setFixedSize(22, 22)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #21262d;
                    border: 1px solid #30363d;
                    color: #c9d1d9;
                    font-size: 11px;
                    border-radius: 3px;
                    padding: 0px;
                }
                QPushButton:hover {
                    background-color: #30363d;
                }
            """)
        preset_layout.addWidget(preset_lbl)
        preset_layout.addWidget(self.preset_combo)
        preset_layout.addWidget(upload_preset_btn)
        preset_layout.addWidget(download_preset_btn)
        dc_layout.addLayout(preset_layout)

        # Toggleable Info Panel
        self.info_panel = QtWidgets.QFrame()
        self.info_panel.setVisible(False)
        self.info_panel.setStyleSheet("border-top: 1px solid #30363d; margin-top: 8px; padding-top: 8px;")
        info_gl = QtWidgets.QGridLayout(self.info_panel)
        info_gl.setContentsMargins(0, 0, 0, 0)
        info_gl.setSpacing(4)
        
        # Populate dynamic properties
        row_idx = 0
        for label_text, info_key, default_val in self.info_properties:
            lbl_key = QtWidgets.QLabel(f"{label_text}:")
            lbl_key.setStyleSheet("color: #8b949e; font-size: 10px; font-weight: normal; border: none;")
            lbl_val = QtWidgets.QLabel(default_val)
            lbl_val.setStyleSheet("color: #c9d1d9; font-size: 10px; font-weight: bold; border: none;")
            lbl_val.setWordWrap(True)
            self.info_value_labels[label_text] = lbl_val
            
            info_gl.addWidget(lbl_key, row_idx, 0)
            info_gl.addWidget(lbl_val, row_idx, 1)
            row_idx += 1
            
        download_fw_btn = QtWidgets.QPushButton("Download firmware...")
        download_fw_btn.setStyleSheet("""
            QPushButton {
                background-color: #21262d;
                border: 1px solid #30363d;
                color: #58a6ff;
                font-size: 10px;
                padding: 4px;
                border-radius: 3px;
                margin-top: 6px;
            }
            QPushButton:hover {
                background-color: #30363d;
            }
        """)
        info_gl.addWidget(download_fw_btn, row_idx, 0, 1, 2)
        dc_layout.addWidget(self.info_panel)

        self.info_btn.clicked.connect(self.toggle_info_panel)
        sidebar_layout.addWidget(device_card)

        # Scrollable area for camera controls
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll_content = QtWidgets.QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        scroll_layout = QtWidgets.QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(12)

        # SECTION 1: Stereo Module (Depth stream)
        self.sec_stereo = CollapsibleSection("Stereo Module")
        self.depth_toggle = QtWidgets.QCheckBox("Enable Depth Stream")
        self.depth_toggle.setChecked(True)
        self.depth_toggle.toggled.connect(self.on_depth_toggled)
        self.sec_stereo.addWidget(self.depth_toggle)

        # Emitter select combo
        emitter_layout = QtWidgets.QHBoxLayout()
        emitter_lbl = QtWidgets.QLabel("IR Emitter:")
        emitter_lbl.setStyleSheet("color: #8b949e; font-size: 12px;")
        self.emitter_combo = QtWidgets.QComboBox()
        self.emitter_combo.addItems(["Disable", "Enable Laser", "Auto Laser"])
        self.emitter_combo.setCurrentIndex(1)
        self.emitter_combo.currentIndexChanged.connect(self.on_emitter_changed)
        emitter_layout.addWidget(emitter_lbl)
        emitter_layout.addWidget(self.emitter_combo)
        self.sec_stereo.addLayout(emitter_layout)

        # Laser power slider
        self.laser_slider = LabeledSlider("Laser Power", 0, 360, 150, " mW")
        self.laser_slider.valueChanged.connect(self.on_laser_changed)
        self.sec_stereo.addWidget(self.laser_slider)

        scroll_layout.addWidget(self.sec_stereo)

        # SECTION 2: RGB Camera Module
        self.sec_rgb = CollapsibleSection("RGB Camera")
        self.rgb_toggle = QtWidgets.QCheckBox("Enable Color Stream")
        self.rgb_toggle.setChecked(True)
        self.rgb_toggle.toggled.connect(self.on_rgb_toggled)
        self.sec_rgb.addWidget(self.rgb_toggle)

        # Auto exposure toggle
        self.auto_exp_chk = QtWidgets.QCheckBox("Auto Exposure")
        self.auto_exp_chk.setChecked(True)
        self.auto_exp_chk.toggled.connect(self.on_auto_exp_changed)
        self.sec_rgb.addWidget(self.auto_exp_chk)

        # Exposure slider (manual mode)
        self.exp_slider = LabeledSlider("Exposure Time", 100, 10000, 1560, " us")
        self.exp_slider.valueChanged.connect(self.on_exposure_changed)
        self.exp_slider.setEnabled(False)  # Disabled by default since Auto Exp is checked
        self.sec_rgb.addWidget(self.exp_slider)

        # Resolution selection dropdown
        res_layout = QtWidgets.QHBoxLayout()
        res_lbl = QtWidgets.QLabel("Resolution:")
        res_lbl.setStyleSheet("color: #8b949e; font-size: 11px;")
        self.cmb_resolution = QtWidgets.QComboBox()
        self.cmb_resolution.addItems(["640x480", "848x480", "1280x720", "1920x1080"])
        self.cmb_resolution.setCurrentText("640x480")
        res_layout.addWidget(res_lbl)
        res_layout.addWidget(self.cmb_resolution)
        self.sec_rgb.addLayout(res_layout)

        # Frame rate selection dropdown
        fps_layout = QtWidgets.QHBoxLayout()
        fps_lbl = QtWidgets.QLabel("Frame Rate:")
        fps_lbl.setStyleSheet("color: #8b949e; font-size: 11px;")
        self.cmb_fps = QtWidgets.QComboBox()
        self.cmb_fps.addItems(["15", "30", "60"])
        self.cmb_fps.setCurrentText("30")
        fps_layout.addWidget(fps_lbl)
        fps_layout.addWidget(self.cmb_fps)
        self.sec_rgb.addLayout(fps_layout)

        # Apply settings button
        self.btn_apply_cam_settings = QtWidgets.QPushButton("🔄 Apply Resolution & FPS")
        self.btn_apply_cam_settings.setStyleSheet("""
            QPushButton {
                background-color: #21262d;
                border: 1px solid #30363d;
                color: #c9d1d9;
                font-size: 11px;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
                margin-top: 4px;
            }
            QPushButton:hover {
                background-color: #30363d;
                color: #58a6ff;
            }
            QPushButton:pressed {
                background-color: #161b22;
            }
        """)
        self.btn_apply_cam_settings.clicked.connect(self.on_apply_camera_settings)
        self.sec_rgb.addWidget(self.btn_apply_cam_settings)

        scroll_layout.addWidget(self.sec_rgb)

        # SECTION 3: Target Tracking Settings
        self.sec_tracker = CollapsibleSection("Target Tracking Settings")
        
        # Track Target Mode Selection Row
        target_layout = QtWidgets.QHBoxLayout()
        target_lbl = QtWidgets.QLabel("Track Target:")
        target_lbl.setStyleSheet("color: #8b949e; font-size: 11px;")
        self.tracker_target_combo = QtWidgets.QComboBox()
        self.tracker_target_combo.addItems(["Tennis Ball (HSV)", "Orange Scissors (HSV)", "ArUco Marker"])
        self.tracker_target_combo.setCurrentIndex(0)
        self.tracker_target_combo.currentIndexChanged.connect(self.on_tracking_target_changed)
        target_layout.addWidget(target_lbl)
        target_layout.addWidget(self.tracker_target_combo)
        self.sec_tracker.addLayout(target_layout)
        
        # HSV Settings container widget
        self.hsv_settings_widget = QtWidgets.QWidget()
        hsv_layout = QtWidgets.QVBoxLayout(self.hsv_settings_widget)
        hsv_layout.setContentsMargins(0, 0, 0, 0)
        hsv_layout.setSpacing(8)
        
        self.hsv_view_toggle = QtWidgets.QCheckBox("Enable Mask Viewport")
        self.hsv_view_toggle.setChecked(True)
        self.hsv_view_toggle.toggled.connect(self.on_hsv_view_toggled)
        hsv_layout.addWidget(self.hsv_view_toggle)
        
        self.h_min = LabeledSlider("Min Hue", 0, 179, self.tracker.hsv_lower[0])
        self.h_max = LabeledSlider("Max Hue", 0, 179, self.tracker.hsv_upper[0])
        self.s_min = LabeledSlider("Min Sat", 0, 255, self.tracker.hsv_lower[1])
        self.s_max = LabeledSlider("Max Sat", 0, 255, self.tracker.hsv_upper[1])
        self.v_min = LabeledSlider("Min Val", 0, 255, self.tracker.hsv_lower[2])
        self.v_max = LabeledSlider("Max Val", 0, 255, self.tracker.hsv_upper[2])

        for slider in [self.h_min, self.h_max, self.s_min, self.s_max, self.v_min, self.v_max]:
            slider.valueChanged.connect(self.on_hsv_changed)
            hsv_layout.addWidget(slider)
            
        self.sec_tracker.addWidget(self.hsv_settings_widget)

        # ArUco Settings container widget (hidden by default)
        self.aruco_settings_widget = QtWidgets.QWidget()
        self.aruco_settings_widget.setVisible(False)
        aruco_layout = QtWidgets.QVBoxLayout(self.aruco_settings_widget)
        aruco_layout.setContentsMargins(0, 0, 0, 0)
        aruco_layout.setSpacing(8)
        
        dict_layout = QtWidgets.QHBoxLayout()
        dict_lbl = QtWidgets.QLabel("Dictionary:")
        dict_lbl.setStyleSheet("color: #8b949e; font-size: 11px;")
        self.aruco_dict_combo = QtWidgets.QComboBox()
        self.aruco_dict_list = [
            ("DICT_4X4_50", cv2.aruco.DICT_4X4_50),
            ("DICT_4X4_100", cv2.aruco.DICT_4X4_100),
            ("DICT_4X4_250", cv2.aruco.DICT_4X4_250),
            ("DICT_5X5_50", cv2.aruco.DICT_5X5_50),
            ("DICT_5X5_100", cv2.aruco.DICT_5X5_100),
            ("DICT_5X5_250", cv2.aruco.DICT_5X5_250),
            ("DICT_5X5_1000", cv2.aruco.DICT_5X5_1000),
            ("DICT_6X6_50", cv2.aruco.DICT_6X6_50),
            ("DICT_6X6_100", cv2.aruco.DICT_6X6_100),
            ("DICT_6X6_250", cv2.aruco.DICT_6X6_250),
            ("DICT_6X6_1000", cv2.aruco.DICT_6X6_1000),
            ("DICT_ARUCO_ORIGINAL", cv2.aruco.DICT_ARUCO_ORIGINAL),
        ]
        if hasattr(cv2.aruco, "DICT_APRILTAG_36h11"):
            self.aruco_dict_list.append(("DICT_APRILTAG_36h11", cv2.aruco.DICT_APRILTAG_36h11))
        self.aruco_dict_combo.addItems([item[0] for item in self.aruco_dict_list])
        self.aruco_dict_combo.setCurrentIndex(0)
        self.aruco_dict_combo.currentIndexChanged.connect(self.on_aruco_settings_changed)
        dict_layout.addWidget(dict_lbl)
        dict_layout.addWidget(self.aruco_dict_combo)
        aruco_layout.addLayout(dict_layout)
        
        size_layout = QtWidgets.QHBoxLayout()
        size_lbl = QtWidgets.QLabel("Marker Size:")
        size_lbl.setStyleSheet("color: #8b949e; font-size: 11px;")
        self.aruco_size_spin = QtWidgets.QSpinBox()
        self.aruco_size_spin.setRange(10, 1000)
        self.aruco_size_spin.setValue(50)  # 50mm
        self.aruco_size_spin.setSuffix(" mm")
        self.aruco_size_spin.valueChanged.connect(self.on_aruco_settings_changed)
        size_layout.addWidget(size_lbl)
        size_layout.addWidget(self.aruco_size_spin)
        aruco_layout.addLayout(size_layout)
        
        id_layout = QtWidgets.QHBoxLayout()
        id_lbl = QtWidgets.QLabel("Target ID:")
        id_lbl.setStyleSheet("color: #8b949e; font-size: 11px;")
        self.aruco_id_spin = QtWidgets.QSpinBox()
        self.aruco_id_spin.setRange(-1, 1000)
        self.aruco_id_spin.setValue(1) # Default to track ID 1
        self.aruco_id_spin.setSpecialValueText("Any (-1)")
        self.aruco_id_spin.valueChanged.connect(self.on_aruco_settings_changed)
        id_layout.addWidget(id_lbl)
        id_layout.addWidget(self.aruco_id_spin)
        aruco_layout.addLayout(id_layout)
        
        self.sec_tracker.addWidget(self.aruco_settings_widget)

        # --- Coordinate Reference Origin controls ---
        ref_divider = QtWidgets.QFrame()
        ref_divider.setFrameShape(QtWidgets.QFrame.HLine)
        ref_divider.setFrameShadow(QtWidgets.QFrame.Sunken)
        ref_divider.setStyleSheet("background-color: #30363d; margin: 8px 0px; border: none;")
        self.sec_tracker.addWidget(ref_divider)

        ref_title = QtWidgets.QLabel("Coordinate Origin Reference")
        ref_title.setStyleSheet("color: #58a6ff; font-weight: bold; font-size: 11px; margin-bottom: 4px;")
        self.sec_tracker.addWidget(ref_title)

        # Origin Mode Selection
        mode_select_layout = QtWidgets.QHBoxLayout()
        mode_select_lbl = QtWidgets.QLabel("Reference Mode:")
        mode_select_lbl.setStyleSheet("color: #8b949e; font-size: 11px;")
        self.cmb_ref_mode = QtWidgets.QComboBox()
        self.cmb_ref_mode.addItems(["Camera Frame", "Live Marker", "Static World"])
        self.cmb_ref_mode.setStyleSheet("font-size: 11px;")
        mode_select_layout.addWidget(mode_select_lbl)
        mode_select_layout.addWidget(self.cmb_ref_mode)
        self.sec_tracker.addLayout(mode_select_layout)

        ref_id_layout = QtWidgets.QHBoxLayout()
        ref_id_lbl = QtWidgets.QLabel("Origin Marker ID:")
        ref_id_lbl.setStyleSheet("color: #8b949e; font-size: 11px;")
        self.spin_ref_id = QtWidgets.QSpinBox()
        self.spin_ref_id.setRange(0, 1000)
        self.spin_ref_id.setValue(0)
        ref_id_layout.addWidget(ref_id_lbl)
        ref_id_layout.addWidget(self.spin_ref_id)
        self.sec_tracker.addLayout(ref_id_layout)

        # Calibration Actions
        calib_btn_layout = QtWidgets.QHBoxLayout()
        self.btn_calib_world = QtWidgets.QPushButton("🔒 Calibrate Origin")
        self.btn_clear_world = QtWidgets.QPushButton("🗑️ Clear")
        
        btn_action_style = """
            QPushButton {
                background-color: #21262d;
                border: 1px solid #30363d;
                color: #c9d1d9;
                font-size: 10px;
                padding: 4px 8px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #30363d;
                color: #58a6ff;
            }
        """
        self.btn_calib_world.setStyleSheet(btn_action_style)
        self.btn_clear_world.setStyleSheet(btn_action_style)
        calib_btn_layout.addWidget(self.btn_calib_world)
        calib_btn_layout.addWidget(self.btn_clear_world)
        self.sec_tracker.addLayout(calib_btn_layout)

        self.lbl_world_calib_status = QtWidgets.QLabel("Status: Not Calibrated")
        self.lbl_world_calib_status.setStyleSheet("color: #8b949e; font-size: 10px; font-style: italic; margin-top: 2px;")
        self.sec_tracker.addWidget(self.lbl_world_calib_status)
        
        scroll_layout.addWidget(self.sec_tracker)

        # SECTION 4: Robot Connection Settings
        self.sec_robot = CollapsibleSection("Robot Connection")
        
        # Port Selection Row
        port_layout = QtWidgets.QHBoxLayout()
        port_lbl = QtWidgets.QLabel("COM Port:")
        port_lbl.setStyleSheet("color: #8b949e; font-size: 11px;")
        self.cmb_robot_port = QtWidgets.QComboBox()
        self.cmb_robot_port.setStyleSheet("font-size: 11px;")
        port_layout.addWidget(port_lbl)
        port_layout.addWidget(self.cmb_robot_port)
        self.sec_robot.addLayout(port_layout)
        
        # Baudrate Selection Row
        baud_layout = QtWidgets.QHBoxLayout()
        baud_lbl = QtWidgets.QLabel("Baud Rate:")
        baud_lbl.setStyleSheet("color: #8b949e; font-size: 11px;")
        self.cmb_robot_baud = QtWidgets.QComboBox()
        self.cmb_robot_baud.addItems(["9600", "19200", "38400", "57600", "115200"])
        self.cmb_robot_baud.setCurrentText("115200")
        self.cmb_robot_baud.setStyleSheet("font-size: 11px;")
        baud_layout.addWidget(baud_lbl)
        baud_layout.addWidget(self.cmb_robot_baud)
        self.sec_robot.addLayout(baud_layout)

        # Protocol Selection Row
        protocol_layout = QtWidgets.QHBoxLayout()
        protocol_lbl = QtWidgets.QLabel("Protocol:")
        protocol_lbl.setStyleSheet("color: #8b949e; font-size: 11px;")
        self.cmb_robot_protocol = QtWidgets.QComboBox()
        self.cmb_robot_protocol.addItems(["G-Code", "JSON"])
        self.cmb_robot_protocol.setCurrentText("G-Code")
        self.cmb_robot_protocol.setStyleSheet("font-size: 11px;")
        protocol_layout.addWidget(protocol_lbl)
        protocol_layout.addWidget(self.cmb_robot_protocol)
        self.sec_robot.addLayout(protocol_layout)

        # Connect / Transmit Control Row
        self.btn_robot_connect = QtWidgets.QPushButton("⚡ Connect Robot")
        self.btn_robot_connect.setStyleSheet("""
            QPushButton {
                background-color: #21262d;
                border: 1px solid #30363d;
                color: #c9d1d9;
                font-size: 11px;
                padding: 6px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #30363d;
                color: #58a6ff;
            }
        """)
        self.sec_robot.addWidget(self.btn_robot_connect)
        
        self.chk_robot_transmit = QtWidgets.QCheckBox("Enable Target Transmit")
        self.chk_robot_transmit.setChecked(False)
        self.sec_robot.addWidget(self.chk_robot_transmit)

        self.lbl_robot_status = QtWidgets.QLabel("Status: Disconnected")
        self.lbl_robot_status.setStyleSheet("color: #8b949e; font-size: 10px; font-style: italic;")
        self.sec_robot.addWidget(self.lbl_robot_status)

        scroll_layout.addWidget(self.sec_robot)

        # SECTION 5: Motion Filter Settings
        self.sec_filter = CollapsibleSection("Motion Filter Settings")
        
        filter_type_layout = QtWidgets.QHBoxLayout()
        filter_type_lbl = QtWidgets.QLabel("Filter Type:")
        filter_type_lbl.setStyleSheet("color: #8b949e; font-size: 11px;")
        self.cmb_filter_type = QtWidgets.QComboBox()
        self.cmb_filter_type.addItems(["None", "Moving Average", "Kalman Filter"])
        self.cmb_filter_type.setCurrentText("Moving Average")
        self.cmb_filter_type.setStyleSheet("font-size: 11px;")
        filter_type_layout.addWidget(filter_type_lbl)
        filter_type_layout.addWidget(self.cmb_filter_type)
        self.sec_filter.addLayout(filter_type_layout)

        self.sld_filter_smoothing = LabeledSlider("Window Size", 1, 30, 8)
        self.sec_filter.addWidget(self.sld_filter_smoothing)
        
        # Connect change signals for filters
        self.cmb_filter_type.currentIndexChanged.connect(self.on_filter_settings_changed)
        self.sld_filter_smoothing.valueChanged.connect(self.on_filter_settings_changed)

        scroll_layout.addWidget(self.sec_filter)
        
        scroll_layout.addStretch()

        scroll.setWidget(scroll_content)
        self.scroll_tracker_settings = scroll
        sidebar_layout.addWidget(self.scroll_tracker_settings)

        # ----------------- CALIBRATION PANEL (LEFT) -----------------
        self.calib_sidebar_widget = QtWidgets.QScrollArea()
        self.calib_sidebar_widget.setWidgetResizable(True)
        self.calib_sidebar_widget.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.calib_sidebar_widget.setVisible(False)
        
        calib_scroll_content = QtWidgets.QWidget()
        calib_scroll_content.setStyleSheet("background: transparent;")
        calib_sidebar_layout = QtWidgets.QVBoxLayout(calib_scroll_content)
        calib_sidebar_layout.setContentsMargins(0, 0, 0, 0)
        calib_sidebar_layout.setSpacing(12)
        
        # Chessboard Configuration
        self.sec_calib_config = CollapsibleSection("Chessboard Target")
        
        cols_layout = QtWidgets.QHBoxLayout()
        cols_lbl = QtWidgets.QLabel("Inner Columns:")
        cols_lbl.setStyleSheet("color: #8b949e; font-size: 11px;")
        self.spin_cols = QtWidgets.QSpinBox()
        self.spin_cols.setRange(3, 20)
        self.spin_cols.setValue(8)
        cols_layout.addWidget(cols_lbl)
        cols_layout.addWidget(self.spin_cols)
        self.sec_calib_config.addLayout(cols_layout)
        
        rows_layout = QtWidgets.QHBoxLayout()
        rows_lbl = QtWidgets.QLabel("Inner Rows:")
        rows_lbl.setStyleSheet("color: #8b949e; font-size: 11px;")
        self.spin_rows = QtWidgets.QSpinBox()
        self.spin_rows.setRange(3, 20)
        self.spin_rows.setValue(6)
        rows_layout.addWidget(rows_lbl)
        rows_layout.addWidget(self.spin_rows)
        self.sec_calib_config.addLayout(rows_layout)
        
        size_layout = QtWidgets.QHBoxLayout()
        size_lbl = QtWidgets.QLabel("Square Size:")
        size_lbl.setStyleSheet("color: #8b949e; font-size: 11px;")
        self.spin_size = QtWidgets.QDoubleSpinBox()
        self.spin_size.setRange(0.001, 1.0)
        self.spin_size.setSingleStep(0.001)
        self.spin_size.setDecimals(3)
        self.spin_size.setValue(0.025)
        self.spin_size.setSuffix(" m")
        size_layout.addWidget(size_lbl)
        size_layout.addWidget(self.spin_size)
        self.sec_calib_config.addLayout(size_layout)
        
        target_layout = QtWidgets.QHBoxLayout()
        target_lbl = QtWidgets.QLabel("Target Poses:")
        target_lbl.setStyleSheet("color: #8b949e; font-size: 11px;")
        self.spin_target = QtWidgets.QSpinBox()
        self.spin_target.setRange(5, 100)
        self.spin_target.setValue(25)
        target_layout.addWidget(target_lbl)
        target_layout.addWidget(self.spin_target)
        self.sec_calib_config.addLayout(target_layout)
        
        self.spin_cols.valueChanged.connect(self.on_calib_settings_changed)
        self.spin_rows.valueChanged.connect(self.on_calib_settings_changed)
        self.spin_size.valueChanged.connect(self.on_calib_settings_changed)
        self.spin_target.valueChanged.connect(self.on_calib_settings_changed)
        
        calib_sidebar_layout.addWidget(self.sec_calib_config)
        
        # Live Calibration Metrics
        self.sec_calib_metrics = CollapsibleSection("Live Tracking Metrics")
        
        self.lbl_calib_corners = QtWidgets.QLabel("Corners Detected: NO")
        self.lbl_calib_corners.setStyleSheet("color: #f85149; font-weight: bold; font-size: 11px;")
        self.sec_calib_metrics.addWidget(self.lbl_calib_corners)
        
        self.lbl_calib_found = QtWidgets.QLabel("Corners Found: 0 / 48")
        self.lbl_calib_found.setStyleSheet("color: #8b949e; font-size: 11px;")
        self.sec_calib_metrics.addWidget(self.lbl_calib_found)
        
        self.lbl_calib_sharpness = QtWidgets.QLabel("Sharpness: 0.0 (Blurry)")
        self.lbl_calib_sharpness.setStyleSheet("color: #f85149; font-size: 11px;")
        self.sec_calib_metrics.addWidget(self.lbl_calib_sharpness)
        
        self.lbl_calib_tilt = QtWidgets.QLabel("Tilt X/Y: 0.0° / 0.0°")
        self.lbl_calib_tilt.setStyleSheet("color: #8b949e; font-size: 11px;")
        self.sec_calib_metrics.addWidget(self.lbl_calib_tilt)
        
        self.lbl_calib_dist = QtWidgets.QLabel("Board Distance: 0.00 m")
        self.lbl_calib_dist.setStyleSheet("color: #8b949e; font-size: 11px;")
        self.sec_calib_metrics.addWidget(self.lbl_calib_dist)
        
        self.lbl_calib_coverage = QtWidgets.QLabel("Coverage: --")
        self.lbl_calib_coverage.setStyleSheet("color: #8b949e; font-size: 11px;")
        self.sec_calib_metrics.addWidget(self.lbl_calib_coverage)
        
        calib_sidebar_layout.addWidget(self.sec_calib_metrics)
        
        # Coverage map (3x3 grid)
        self.sec_calib_map = CollapsibleSection("Lens Coverage Map")
        map_h_layout = QtWidgets.QHBoxLayout()
        map_h_layout.setContentsMargins(10, 0, 10, 0)
        self.coverage_grid = CoverageGrid()
        map_h_lbl = QtWidgets.QLabel("Move board to cover\nall sectors (green):")
        map_h_lbl.setStyleSheet("color: #8b949e; font-size: 10px;")
        map_h_layout.addWidget(map_h_lbl)
        map_h_layout.addWidget(self.coverage_grid)
        self.sec_calib_map.addLayout(map_h_layout)
        calib_sidebar_layout.addWidget(self.sec_calib_map)
        
        # Calibration execution controls
        self.sec_calib_controls = CollapsibleSection("Calibration Controls")
        
        self.chk_auto_capture = QtWidgets.QCheckBox("Enable Auto-Capture")
        self.chk_auto_capture.setChecked(True)
        self.chk_auto_capture.toggled.connect(self.on_calib_settings_changed)
        self.sec_calib_controls.addWidget(self.chk_auto_capture)
        
        btn_grid = QtWidgets.QGridLayout()
        self.btn_calib_capture = QtWidgets.QPushButton("📥 Capture")
        self.btn_calib_run = QtWidgets.QPushButton("🔄 Calibrate")
        self.btn_calib_save = QtWidgets.QPushButton("💾 Save JSON")
        self.btn_calib_clear = QtWidgets.QPushButton("🗑️ Clear All")
        self.btn_calib_load = QtWidgets.QPushButton("📂 Load JSON")
        
        btn_style = """
            QPushButton {
                background-color: #21262d;
                border: 1px solid #30363d;
                color: #c9d1d9;
                font-size: 11px;
                padding: 6px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #30363d;
                color: #58a6ff;
            }
        """
        for btn in [self.btn_calib_capture, self.btn_calib_run, self.btn_calib_save, self.btn_calib_clear, self.btn_calib_load]:
            btn.setStyleSheet(btn_style)
            
        btn_grid.addWidget(self.btn_calib_capture, 0, 0)
        btn_grid.addWidget(self.btn_calib_run, 0, 1)
        btn_grid.addWidget(self.btn_calib_save, 1, 0)
        btn_grid.addWidget(self.btn_calib_clear, 1, 1)
        btn_grid.addWidget(self.btn_calib_load, 2, 0, 1, 2)
        
        self.sec_calib_controls.addLayout(btn_grid)
        calib_sidebar_layout.addWidget(self.sec_calib_controls)
        
        # Connect buttons slots
        self.btn_calib_capture.clicked.connect(self.on_calib_manual_capture)
        self.btn_calib_run.clicked.connect(self.on_calib_run_calibration)
        self.btn_calib_save.clicked.connect(self.on_calib_save_results)
        self.btn_calib_clear.clicked.connect(self.on_calib_clear_data)
        self.btn_calib_load.clicked.connect(self.on_calib_load_results)
        
        # SECTION 5: Calibration Guide / Instructions
        self.sec_calib_guide = CollapsibleSection("Calibration Guide")
        self.sec_calib_guide.toggle_btn.setChecked(False) # Collapsed by default
        self.sec_calib_guide.toggle_content(False)
        
        guide_text = QtWidgets.QLabel(
            "<b>1. Setup Checkerboard Target:</b><br>"
            "• Use a standard printed grid.<br>"
            "• Count <i>inner</i> corners (columns/rows).<br>"
            "• Input square size in meters (e.g., 0.025 m).<br><br>"
            "<b>2. Capture Poses:</b><br>"
            "• Move target to cover all 9 screen sectors.<br>"
            "• Auto-capture triggers when grid is sharp (&gt;100) and still.<br>"
            "• Rotate board to vary tilt angles (X/Y).<br><br>"
            "<b>3. Compute & Verify:</b><br>"
            "• Collect 15+ poses, then click <b>Calibrate</b>.<br>"
            "• Check Reprojection Error:<br>"
            "  - Green (&lt;0.3px): Excellent<br>"
            "  - Yellow (0.3-0.7px): Acceptable<br>"
            "  - Red (&gt;0.7px): Poor (Clear & retry)<br>"
            "• Verify rectified feed on the right.<br><br>"
            "<b>4. Save Intrinsics:</b><br>"
            "• Click <b>Save JSON</b> to export calibration."
        )
        guide_text.setStyleSheet("color: #8b949e; font-size: 11px;")
        guide_text.setWordWrap(True)
        self.sec_calib_guide.addWidget(guide_text)
        calib_sidebar_layout.addWidget(self.sec_calib_guide)
        
        calib_sidebar_layout.addStretch()
        self.calib_sidebar_widget.setWidget(calib_scroll_content)
        sidebar_layout.addWidget(self.calib_sidebar_widget)

        self.btn_mode_tracker.clicked.connect(self.switch_to_tracker_mode)
        self.btn_mode_calib.clicked.connect(self.switch_to_calib_mode)

        main_layout.addWidget(sidebar_container)

        # ----------------- CENTRAL PANEL (RIGHT) -----------------
        right_container = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right_container)
        right_layout.setContentsMargins(12, 12, 12, 12)
        right_layout.setSpacing(10)

        # Splitter to divide viewport streams (top) from tracking graph (bottom)
        self.main_splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        self.main_splitter.setChildrenCollapsible(False)

        # VIEWPORTS (TOP OF SPLITTER)
        viewport_container = QtWidgets.QWidget()
        self.viewport_layout = QtWidgets.QHBoxLayout(viewport_container)
        self.viewport_layout.setContentsMargins(0, 0, 0, 0)
        self.viewport_layout.setSpacing(10)

        # 1. RGB VIEWPORT CARD
        self.rgb_card = QtWidgets.QFrame()
        self.rgb_card.setObjectName("viewportCard")
        rgb_card_layout = QtWidgets.QVBoxLayout(self.rgb_card)
        rgb_card_layout.setContentsMargins(0, 0, 0, 0)
        rgb_card_layout.setSpacing(0)

        # Header bar
        rgb_header = QtWidgets.QFrame()
        rgb_header.setObjectName("viewportHeader")
        rgb_header.setFixedHeight(35)
        rgb_hl = QtWidgets.QHBoxLayout(rgb_header)
        rgb_hl.setContentsMargins(10, 0, 10, 0)

        rgb_title = QtWidgets.QLabel("RGB Camera | Color Stream")
        rgb_title.setStyleSheet("font-weight: bold; font-size: 11px;")
        rgb_hl.addWidget(rgb_title)
        rgb_hl.addStretch()

        self.btn_pause_rgb = QtWidgets.QPushButton("⏸")
        self.btn_pause_rgb.setObjectName("streamActionBtn")
        self.btn_pause_rgb.setToolTip("Pause Stream")
        self.btn_pause_rgb.clicked.connect(self.toggle_pause_rgb)

        self.btn_snap_rgb = QtWidgets.QPushButton("📷")
        self.btn_snap_rgb.setObjectName("streamActionBtn")
        self.btn_snap_rgb.setToolTip("Take Photo")
        self.btn_snap_rgb.clicked.connect(self.capture_rgb)

        self.btn_graph_rgb = QtWidgets.QPushButton("📊")
        self.btn_graph_rgb.setObjectName("streamActionBtn")
        self.btn_graph_rgb.setToolTip("Toggle Depth Graph")
        self.btn_graph_rgb.setCheckable(True)
        self.btn_graph_rgb.clicked.connect(self.toggle_graph_panel)
        self.btn_graph_rgb.setVisible(True)

        self.rgb_fps_lbl = QtWidgets.QLabel("640x480 @ 30 FPS")
        self.rgb_fps_lbl.setStyleSheet("color: #8b949e; font-size: 11px; margin-left: 8px;")

        rgb_hl.addWidget(self.btn_pause_rgb)
        rgb_hl.addWidget(self.btn_snap_rgb)
        rgb_hl.addWidget(self.btn_graph_rgb)
        rgb_hl.addWidget(self.rgb_fps_lbl)
        rgb_card_layout.addWidget(rgb_header)

        # Body Video Screen
        self.rgb_video_label = VideoLabel()
        rgb_card_layout.addWidget(self.rgb_video_label)
        self.viewport_layout.addWidget(self.rgb_card)

        # 2. DEPTH VIEWPORT CARD
        self.depth_card = QtWidgets.QFrame()
        self.depth_card.setObjectName("viewportCard")
        depth_card_layout = QtWidgets.QVBoxLayout(self.depth_card)
        depth_card_layout.setContentsMargins(0, 0, 0, 0)
        depth_card_layout.setSpacing(0)

        # Header bar
        depth_header = QtWidgets.QFrame()
        depth_header.setObjectName("viewportHeader")
        depth_header.setFixedHeight(35)
        depth_hl = QtWidgets.QHBoxLayout(depth_header)
        depth_hl.setContentsMargins(10, 0, 10, 0)

        depth_title = QtWidgets.QLabel("Stereo Module | Depth Stream")
        depth_title.setStyleSheet("font-weight: bold; font-size: 11px;")
        depth_hl.addWidget(depth_title)
        depth_hl.addStretch()

        self.btn_pause_depth = QtWidgets.QPushButton("⏸")
        self.btn_pause_depth.setObjectName("streamActionBtn")
        self.btn_pause_depth.setToolTip("Pause Stream")
        self.btn_pause_depth.clicked.connect(self.toggle_pause_depth)

        self.btn_snap_depth = QtWidgets.QPushButton("📷")
        self.btn_snap_depth.setObjectName("streamActionBtn")
        self.btn_snap_depth.setToolTip("Take Photo")
        self.btn_snap_depth.clicked.connect(self.capture_depth)

        self.btn_graph_depth = QtWidgets.QPushButton("📊")
        self.btn_graph_depth.setObjectName("streamActionBtn")
        self.btn_graph_depth.setToolTip("Toggle Depth Graph")
        self.btn_graph_depth.setCheckable(True)
        self.btn_graph_depth.clicked.connect(self.toggle_graph_panel)
        self.btn_graph_depth.setVisible(True)

        self.depth_fps_lbl = QtWidgets.QLabel("640x480 @ 30 FPS")
        self.depth_fps_lbl.setStyleSheet("color: #8b949e; font-size: 11px; margin-left: 8px;")

        depth_hl.addWidget(self.btn_pause_depth)
        depth_hl.addWidget(self.btn_snap_depth)
        depth_hl.addWidget(self.btn_graph_depth)
        depth_hl.addWidget(self.depth_fps_lbl)
        depth_card_layout.addWidget(depth_header)

        # Body Video Screen
        self.depth_video_label = VideoLabel()
        depth_card_layout.addWidget(self.depth_video_label)
        self.viewport_layout.addWidget(self.depth_card)

        # 3. HSV MASK VIEWPORT CARD
        self.hsv_card = QtWidgets.QFrame()
        self.hsv_card.setObjectName("viewportCard")
        hsv_card_layout = QtWidgets.QVBoxLayout(self.hsv_card)
        hsv_card_layout.setContentsMargins(0, 0, 0, 0)
        hsv_card_layout.setSpacing(0)

        # Header bar
        hsv_header = QtWidgets.QFrame()
        hsv_header.setObjectName("viewportHeader")
        hsv_header.setFixedHeight(35)
        hsv_hl = QtWidgets.QHBoxLayout(hsv_header)
        hsv_hl.setContentsMargins(10, 0, 10, 0)

        hsv_title = QtWidgets.QLabel("Ball Tracker | HSV Mask Stream")
        hsv_title.setStyleSheet("font-weight: bold; font-size: 11px;")
        hsv_hl.addWidget(hsv_title)
        hsv_hl.addStretch()

        self.btn_pause_hsv = QtWidgets.QPushButton("⏸")
        self.btn_pause_hsv.setObjectName("streamActionBtn")
        self.btn_pause_hsv.setToolTip("Pause Stream")
        self.btn_pause_hsv.clicked.connect(self.toggle_pause_hsv)

        self.btn_snap_hsv = QtWidgets.QPushButton("📷")
        self.btn_snap_hsv.setObjectName("streamActionBtn")
        self.btn_snap_hsv.setToolTip("Take Photo")
        self.btn_snap_hsv.clicked.connect(self.capture_hsv)

        self.hsv_fps_lbl = QtWidgets.QLabel("640x480 @ 30 FPS")
        self.hsv_fps_lbl.setStyleSheet("color: #8b949e; font-size: 11px; margin-left: 8px;")

        hsv_hl.addWidget(self.btn_pause_hsv)
        hsv_hl.addWidget(self.btn_snap_hsv)
        hsv_hl.addWidget(self.hsv_fps_lbl)
        hsv_card_layout.addWidget(hsv_header)

        # Body Video Screen
        self.hsv_video_label = VideoLabel()
        hsv_card_layout.addWidget(self.hsv_video_label)
        self.viewport_layout.addWidget(self.hsv_card)

        # 4. BLACK PLACEHOLDER FOR DISABLED STREAMS
        self.placeholder_widget = QtWidgets.QWidget()
        self.placeholder_widget.setStyleSheet("background-color: #0c1117; border: 1px solid #30363d; border-radius: 6px;")
        ph_layout = QtWidgets.QVBoxLayout(self.placeholder_widget)
        ph_label = QtWidgets.QLabel("All Streams Stopped.\nEnable Stereo Module, RGB Camera, or Mask Viewport in left panel.")
        ph_label.setAlignment(QtCore.Qt.AlignCenter)
        ph_label.setStyleSheet("color: #8b949e; font-size: 14px; font-weight: bold;")
        ph_layout.addWidget(ph_label)
        self.viewport_layout.addWidget(self.placeholder_widget)
        self.placeholder_widget.setVisible(False)

        self.viewport_container = viewport_container
        self.main_splitter.addWidget(self.viewport_container)

        # GRAPH PANEL (BOTTOM OF SPLITTER)
        self.graph_panel = QtWidgets.QFrame()
        self.graph_panel.setObjectName("graphPanel")
        graph_layout = QtWidgets.QVBoxLayout(self.graph_panel)
        graph_layout.setContentsMargins(6, 6, 6, 6)

        # Graph Header
        graph_header_layout = QtWidgets.QHBoxLayout()
        graph_title = QtWidgets.QLabel("Real-time Tracking Coordinate Deviation (meters)")
        graph_title.setStyleSheet("font-weight: bold; font-size: 11px; color: #58a6ff;")
        graph_header_layout.addWidget(graph_title)
        graph_header_layout.addStretch()

        # Legend indicator labels
        z_leg = QtWidgets.QLabel("● Z (Depth)")
        z_leg.setStyleSheet("color: #ffcc00; font-weight: bold; font-size: 11px; margin-right: 10px;")
        x_leg = QtWidgets.QLabel("● X (Left/Right)")
        x_leg.setStyleSheet("color: #ff3333; font-weight: bold; font-size: 11px; margin-right: 10px;")
        y_leg = QtWidgets.QLabel("● Y (Up/Down)")
        y_leg.setStyleSheet("color: #33cc33; font-weight: bold; font-size: 11px;")
        graph_header_layout.addWidget(z_leg)
        graph_header_layout.addWidget(x_leg)
        graph_header_layout.addWidget(y_leg)
        graph_layout.addLayout(graph_header_layout)

        # Build PyQtGraph
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground("#0c1117")
        self.plot_widget.showGrid(x=True, y=True, alpha=0.15)
        self.plot_widget.setLabel("left", "Value", units="m")
        self.plot_widget.setLabel("bottom", "Frame History")
        self.plot_widget.getViewBox().setMouseEnabled(x=False, y=True)

        self.z_curve = self.plot_widget.plot(pen=pg.mkPen(color="#ffcc00", width=2))
        self.x_curve = self.plot_widget.plot(pen=pg.mkPen(color="#ff3333", width=1.5))
        self.y_curve = self.plot_widget.plot(pen=pg.mkPen(color="#33cc33", width=1.5))

        graph_layout.addWidget(self.plot_widget)

        self.main_splitter.addWidget(self.graph_panel)
        self.graph_panel.setVisible(False)

        # ----------------- CALIBRATION VIEWPORTS (TOP OF SPLITTER) -----------------
        self.calib_viewports_container = QtWidgets.QWidget()
        self.calib_viewports_container.setVisible(False)
        calib_vp_layout = QtWidgets.QHBoxLayout(self.calib_viewports_container)
        calib_vp_layout.setContentsMargins(0, 0, 0, 0)
        calib_vp_layout.setSpacing(10)
        
        # Live Chessboard Feed Card
        self.calib_live_card = QtWidgets.QFrame()
        self.calib_live_card.setObjectName("viewportCard")
        clc_layout = QtWidgets.QVBoxLayout(self.calib_live_card)
        clc_layout.setContentsMargins(0, 0, 0, 0)
        clc_layout.setSpacing(0)
        
        clc_header = QtWidgets.QFrame()
        clc_header.setObjectName("viewportHeader")
        clc_header.setFixedHeight(35)
        clc_hl = QtWidgets.QHBoxLayout(clc_header)
        clc_hl.setContentsMargins(10, 0, 10, 0)
        clc_title = QtWidgets.QLabel("Live Camera Feed | Chessboard Overlay")
        clc_title.setStyleSheet("font-weight: bold; font-size: 11px;")
        clc_hl.addWidget(clc_title)
        clc_layout.addWidget(clc_header)
        
        self.calib_live_video_label = VideoLabel()
        clc_layout.addWidget(self.calib_live_video_label)
        calib_vp_layout.addWidget(self.calib_live_card)
        
        # Undistorted Preview Card
        self.calib_undistort_card = QtWidgets.QFrame()
        self.calib_undistort_card.setObjectName("viewportCard")
        cuc_layout = QtWidgets.QVBoxLayout(self.calib_undistort_card)
        cuc_layout.setContentsMargins(0, 0, 0, 0)
        cuc_layout.setSpacing(0)
        
        cuc_header = QtWidgets.QFrame()
        cuc_header.setObjectName("viewportHeader")
        cuc_header.setFixedHeight(35)
        cuc_hl = QtWidgets.QHBoxLayout(cuc_header)
        cuc_hl.setContentsMargins(10, 0, 10, 0)
        cuc_title = QtWidgets.QLabel("Undistorted Preview | Rectified Geometry")
        cuc_title.setStyleSheet("font-weight: bold; font-size: 11px;")
        cuc_hl.addWidget(cuc_title)
        cuc_layout.addWidget(cuc_header)
        
        self.calib_undistort_video_label = VideoLabel()
        cuc_layout.addWidget(self.calib_undistort_video_label)
        calib_vp_layout.addWidget(self.calib_undistort_card)
        
        self.main_splitter.addWidget(self.calib_viewports_container)

        # ----------------- CALIBRATION RESULTS PANEL (BOTTOM OF SPLITTER) -----------------
        self.calib_results_panel = QtWidgets.QFrame()
        self.calib_results_panel.setObjectName("viewportCard")
        self.calib_results_panel.setVisible(False)
        crp_layout = QtWidgets.QHBoxLayout(self.calib_results_panel)
        crp_layout.setContentsMargins(12, 12, 12, 12)
        crp_layout.setSpacing(16)
        
        # Left Part: Big Reprojection Error + Parameters
        left_res_widget = QtWidgets.QWidget()
        lr_layout = QtWidgets.QVBoxLayout(left_res_widget)
        lr_layout.setContentsMargins(0, 0, 0, 0)
        lr_layout.setSpacing(10)
        
        res_header = QtWidgets.QLabel("CALIBRATION METRICS & INTRINSICS")
        res_header.setStyleSheet("font-weight: bold; font-size: 11px; color: #58a6ff;")
        lr_layout.addWidget(res_header)
        
        self.lbl_reproj_error = QtWidgets.QLabel("Reprojection Error: -- px")
        self.lbl_reproj_error.setStyleSheet("color: #8b949e; font-size: 22px; font-weight: bold;")
        lr_layout.addWidget(self.lbl_reproj_error)
        
        self.lbl_calib_valid = QtWidgets.QLabel("Valid Poses Captured: 0 / 25")
        self.lbl_calib_valid.setStyleSheet("color: #c9d1d9; font-size: 12px; font-weight: bold;")
        lr_layout.addWidget(self.lbl_calib_valid)
        
        self.calib_results_text = QtWidgets.QTextBrowser()
        self.calib_results_text.setStyleSheet("""
            QTextBrowser {
                background-color: #0c1117;
                border: 1px solid #30363d;
                border-radius: 4px;
                color: #c9d1d9;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                padding: 6px;
            }
        """)
        self.calib_results_text.setText("Intrinsics fx, fy, cx, cy: Not Calibrated\nDistortion k1, k2, p1, p2, k3: Not Calibrated")
        lr_layout.addWidget(self.calib_results_text)
        
        crp_layout.addWidget(left_res_widget, stretch=4)
        
        # Right Part: Captured Poses Table
        right_res_widget = QtWidgets.QWidget()
        rr_layout = QtWidgets.QVBoxLayout(right_res_widget)
        rr_layout.setContentsMargins(0, 0, 0, 0)
        rr_layout.setSpacing(6)
        
        table_header = QtWidgets.QLabel("CAPTURED POSES HISTORY")
        table_header.setStyleSheet("font-weight: bold; font-size: 11px; color: #8b949e;")
        rr_layout.addWidget(table_header)
        
        self.calib_frames_table = QtWidgets.QTableWidget()
        self.calib_frames_table.setColumnCount(6)
        self.calib_frames_table.setHorizontalHeaderLabels(["Pose #", "Sharpness", "Tilt X", "Tilt Y", "Distance", "Sector"])
        self.calib_frames_table.horizontalHeader().setDefaultSectionSize(75)
        self.calib_frames_table.horizontalHeader().setStretchLastSection(True)
        self.calib_frames_table.setStyleSheet("""
            QTableWidget {
                background-color: #0c1117;
                border: 1px solid #30363d;
                border-radius: 4px;
                color: #c9d1d9;
                gridline-color: #30363d;
                font-size: 11px;
            }
            QHeaderView::section {
                background-color: #21262d;
                color: #c9d1d9;
                border: 1px solid #30363d;
                padding: 4px;
                font-size: 10px;
                font-weight: bold;
            }
        """)
        self.calib_frames_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.calib_frames_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        rr_layout.addWidget(self.calib_frames_table)
        
        crp_layout.addWidget(right_res_widget, stretch=6)
                
        self.main_splitter.addWidget(self.calib_results_panel)

        # ARUCO TELEMETRY & DETECTIONS PANEL (BOTTOM OF SPLITTER)
        self.aruco_panel = QtWidgets.QFrame()
        self.aruco_panel.setObjectName("viewportCard")
        self.aruco_panel.setVisible(False)
        aruco_panel_layout = QtWidgets.QHBoxLayout(self.aruco_panel)
        aruco_panel_layout.setContentsMargins(12, 12, 12, 12)
        aruco_panel_layout.setSpacing(16)

        # Left side: Relative Telemetry Readout
        telemetry_widget = QtWidgets.QWidget()
        telemetry_layout = QtWidgets.QVBoxLayout(telemetry_widget)
        telemetry_layout.setContentsMargins(0, 0, 0, 0)
        telemetry_layout.setSpacing(8)

        tel_header = QtWidgets.QLabel("TARGET TRACKING TELEMETRY")
        tel_header.setStyleSheet("font-weight: bold; font-size: 11px; color: #58a6ff;")
        telemetry_layout.addWidget(tel_header)

        self.lbl_aruco_target_title = QtWidgets.QLabel("Target: --")
        self.lbl_aruco_target_title.setStyleSheet("color: #c9d1d9; font-size: 13px; font-weight: bold;")
        telemetry_layout.addWidget(self.lbl_aruco_target_title)

        # Coordinates Readout Card (Physical & Pixel Panels)
        self.coords_card = QtWidgets.QFrame()
        self.coords_card.setStyleSheet("""
            QFrame {
                background-color: #161b22;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 10px;
                margin-top: 4px;
                margin-bottom: 4px;
            }
            QLabel {
                border: none;
                background-color: transparent;
            }
        """)
        
        card_layout = QtWidgets.QVBoxLayout(self.coords_card)
        card_layout.setContentsMargins(10, 10, 10, 10)
        card_layout.setSpacing(8)

        card_title = QtWidgets.QLabel("TARGET TRACKING READOUT")
        card_title.setStyleSheet("font-weight: bold; font-size: 10px; color: #58a6ff; letter-spacing: 1px;")
        card_layout.addWidget(card_title)

        # Horizontal layout for physical vs pixel columns
        columns_layout = QtWidgets.QHBoxLayout()
        columns_layout.setSpacing(16)

        # 1. Physical Space Column
        phys_widget = QtWidgets.QWidget()
        phys_layout = QtWidgets.QVBoxLayout(phys_widget)
        phys_layout.setContentsMargins(0, 0, 0, 0)
        phys_layout.setSpacing(6)

        phys_title = QtWidgets.QLabel("Physical Space (m)")
        phys_title.setStyleSheet("font-weight: bold; font-size: 10px; color: #8b949e; border-bottom: 1px solid #30363d; padding-bottom: 3px; margin-bottom: 2px;")
        phys_layout.addWidget(phys_title)

        self.lbl_phys_x = QtWidgets.QLabel("X: +0.000 m")
        self.lbl_phys_y = QtWidgets.QLabel("Y: +0.000 m")
        self.lbl_phys_z = QtWidgets.QLabel("Z:  0.000 m")
        self.lbl_phys_dist = QtWidgets.QLabel("Distance: 0.000 m")

        for lbl in [self.lbl_phys_x, self.lbl_phys_y, self.lbl_phys_z, self.lbl_phys_dist]:
            lbl.setStyleSheet("color: #ffcc00; font-family: 'Consolas', 'Courier New', monospace; font-size: 11px; font-weight: bold;")
            phys_layout.addWidget(lbl)

        columns_layout.addWidget(phys_widget)

        # Vertical divider line
        divider = QtWidgets.QFrame()
        divider.setFrameShape(QtWidgets.QFrame.VLine)
        divider.setFrameShadow(QtWidgets.QFrame.Sunken)
        divider.setStyleSheet("background-color: #30363d; border: none; width: 1px;")
        columns_layout.addWidget(divider)

        # 2. Pixel Screen Column
        pixel_widget = QtWidgets.QWidget()
        pixel_layout = QtWidgets.QVBoxLayout(pixel_widget)
        pixel_layout.setContentsMargins(0, 0, 0, 0)
        pixel_layout.setSpacing(6)

        pixel_title = QtWidgets.QLabel("Pixel Screen (px)")
        pixel_title.setStyleSheet("font-weight: bold; font-size: 10px; color: #8b949e; border-bottom: 1px solid #30363d; padding-bottom: 3px; margin-bottom: 2px;")
        pixel_layout.addWidget(pixel_title)

        self.lbl_pixel_u = QtWidgets.QLabel("U: -- px")
        self.lbl_pixel_v = QtWidgets.QLabel("V: -- px")
        self.lbl_pixel_norm = QtWidgets.QLabel("Norm: (--, --)")
        self.lbl_track_status = QtWidgets.QLabel("Status: SEARCHING")

        for lbl in [self.lbl_pixel_u, self.lbl_pixel_v, self.lbl_pixel_norm, self.lbl_track_status]:
            lbl.setStyleSheet("color: #58a6ff; font-family: 'Consolas', 'Courier New', monospace; font-size: 11px; font-weight: bold;")
            pixel_layout.addWidget(lbl)

        columns_layout.addWidget(pixel_widget)
        card_layout.addLayout(columns_layout)
        
        telemetry_layout.addWidget(self.coords_card)

        # Reference status label
        self.lbl_ref_status = QtWidgets.QLabel("Origin Reference: Inactive (Using Camera Frame)")
        self.lbl_ref_status.setStyleSheet("color: #8b949e; font-size: 11px;")
        telemetry_layout.addWidget(self.lbl_ref_status)

        # Origin reference telemetry sub-panel
        self.origin_info_box = QtWidgets.QFrame()
        self.origin_info_box.setStyleSheet("""
            QFrame {
                background-color: #0d1117;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 6px;
                margin-top: 4px;
            }
            QLabel {
                border: none;
                background-color: transparent;
            }
        """)
        origin_info_layout = QtWidgets.QVBoxLayout(self.origin_info_box)
        origin_info_layout.setContentsMargins(6, 6, 6, 6)
        origin_info_layout.setSpacing(4)
        
        self.lbl_origin_title = QtWidgets.QLabel("ORIGIN REFERENCE TELEMETRY")
        self.lbl_origin_title.setStyleSheet("font-weight: bold; font-size: 9px; color: #58a6ff;")
        origin_info_layout.addWidget(self.lbl_origin_title)
        
        self.lbl_origin_id = QtWidgets.QLabel("Reference ID: --")
        self.lbl_origin_id.setStyleSheet("color: #c9d1d9; font-size: 11px; font-weight: bold;")
        origin_info_layout.addWidget(self.lbl_origin_id)
        
        self.lbl_origin_coords_cam = QtWidgets.QLabel("Camera Frame (Before World):\n  X: +0.000m, Y: +0.000m, Z: 0.000m")
        self.lbl_origin_coords_cam.setStyleSheet("color: #8b949e; font-size: 11px;")
        origin_info_layout.addWidget(self.lbl_origin_coords_cam)

        self.lbl_camera_coords_world = QtWidgets.QLabel("Camera Position (in World Frame):\n  X: +0.000m, Y: +0.000m, Z: 0.000m")
        self.lbl_camera_coords_world.setStyleSheet("color: #ffaa00; font-size: 11px;")
        origin_info_layout.addWidget(self.lbl_camera_coords_world)
        
        self.lbl_origin_distance_obj = QtWidgets.QLabel("Object-to-Origin Distance: --")
        self.lbl_origin_distance_obj.setStyleSheet("color: #2ea043; font-weight: bold; font-size: 12px;")
        origin_info_layout.addWidget(self.lbl_origin_distance_obj)
        
        self.origin_info_box.setVisible(False)
        telemetry_layout.addWidget(self.origin_info_box)
        
        telemetry_layout.addSpacing(10)
        
        # Save and Log actions
        action_layout = QtWidgets.QHBoxLayout()
        action_layout.setSpacing(8)
        
        self.btn_save_coords = QtWidgets.QPushButton("💾 Save Snapshot")
        self.btn_log_coords = QtWidgets.QPushButton("📝 Start Logging")
        self.btn_log_coords.setCheckable(True)
        
        btn_action_style = """
            QPushButton {
                background-color: #21262d;
                border: 1px solid #30363d;
                color: #c9d1d9;
                font-size: 11px;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #30363d;
                color: #58a6ff;
            }
            QPushButton:checked {
                background-color: #f85149;
                border-color: #f85149;
                color: #ffffff;
            }
        """
        self.btn_save_coords.setStyleSheet(btn_action_style)
        self.btn_log_coords.setStyleSheet(btn_action_style)
        
        self.btn_save_coords.clicked.connect(self.on_save_coords_snapshot)
        self.btn_log_coords.toggled.connect(self.on_toggle_logging)
        
        action_layout.addWidget(self.btn_save_coords)
        action_layout.addWidget(self.btn_log_coords)
        telemetry_layout.addLayout(action_layout)
        
        telemetry_layout.addStretch()

        aruco_panel_layout.addWidget(telemetry_widget, stretch=4)

        # Right side: Tab Widget for Detections and Distances
        self.aruco_tab_widget = QtWidgets.QTabWidget()
        self.aruco_tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #30363d;
                background-color: #0c1117;
                border-radius: 4px;
            }
            QTabBar::tab {
                background-color: #161b22;
                color: #8b949e;
                border: 1px solid #30363d;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
                font-size: 11px;
            }
            QTabBar::tab:selected {
                background-color: #0c1117;
                color: #58a6ff;
                border-bottom: 1px solid #0c1117;
            }
            QTabBar::tab:hover {
                background-color: #21262d;
                color: #c9d1d9;
            }
        """)

        # Tab 1: Detected Markers
        tab_detections = QtWidgets.QWidget()
        tab_det_layout = QtWidgets.QVBoxLayout(tab_detections)
        tab_det_layout.setContentsMargins(8, 8, 8, 8)
        tab_det_layout.setSpacing(6)

        self.tbl_aruco_detections = QtWidgets.QTableWidget()
        self.tbl_aruco_detections.setColumnCount(5)
        self.tbl_aruco_detections.setHorizontalHeaderLabels(["Marker ID", "X (m)", "Y (m)", "Z (m)", "Distance (m)"])
        self.tbl_aruco_detections.horizontalHeader().setDefaultSectionSize(100)
        self.tbl_aruco_detections.horizontalHeader().setStretchLastSection(True)
        self.tbl_aruco_detections.setStyleSheet("""
            QTableWidget {
                background-color: #0c1117;
                border: 1px solid #30363d;
                border-radius: 4px;
                color: #c9d1d9;
                gridline-color: #30363d;
                font-size: 11px;
            }
            QHeaderView::section {
                background-color: #21262d;
                color: #c9d1d9;
                border: 1px solid #30363d;
                padding: 4px;
                font-size: 10px;
                font-weight: bold;
            }
        """)
        self.tbl_aruco_detections.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tbl_aruco_detections.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        tab_det_layout.addWidget(self.tbl_aruco_detections)
        self.aruco_tab_widget.addTab(tab_detections, "🔍 Detected Markers")

        # Tab 2: Distance Measurements
        tab_distances = QtWidgets.QWidget()
        tab_dist_layout = QtWidgets.QVBoxLayout(tab_distances)
        tab_dist_layout.setContentsMargins(8, 8, 8, 8)
        tab_dist_layout.setSpacing(8)

        self.tbl_aruco_distances = QtWidgets.QTableWidget()
        self.tbl_aruco_distances.setColumnCount(5)
        self.tbl_aruco_distances.setHorizontalHeaderLabels(["Description", "Point A", "Point B", "Distance (m)", "Status"])
        self.tbl_aruco_distances.horizontalHeader().setDefaultSectionSize(110)
        self.tbl_aruco_distances.horizontalHeader().setStretchLastSection(True)
        self.tbl_aruco_distances.setStyleSheet("""
            QTableWidget {
                background-color: #0c1117;
                border: 1px solid #30363d;
                border-radius: 4px;
                color: #c9d1d9;
                gridline-color: #30363d;
                font-size: 11px;
            }
            QHeaderView::section {
                background-color: #21262d;
                color: #c9d1d9;
                border: 1px solid #30363d;
                padding: 4px;
                font-size: 10px;
                font-weight: bold;
            }
        """)
        self.tbl_aruco_distances.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.tbl_aruco_distances.itemChanged.connect(self.on_distance_item_changed)
        tab_dist_layout.addWidget(self.tbl_aruco_distances)

        # Input controls to add a distance measurement specification
        add_layout = QtWidgets.QHBoxLayout()
        add_layout.setSpacing(6)

        self.txt_dist_desc = QtWidgets.QLineEdit()
        self.txt_dist_desc.setPlaceholderText("Name / Description (e.g. Table Width)")
        self.txt_dist_desc.setStyleSheet("""
            QLineEdit {
                background-color: #21262d;
                border: 1px solid #30363d;
                border-radius: 4px;
                padding: 4px;
                color: #c9d1d9;
                font-size: 11px;
            }
            QLineEdit:focus {
                border-color: #58a6ff;
            }
        """)

        self.cmb_point_a_type = QtWidgets.QComboBox()
        self.cmb_point_a_type.addItems(["Camera", "Origin", "Marker ID", "Target Object"])
        self.cmb_point_a_type.setStyleSheet("font-size: 11px;")

        self.spin_point_a_id = QtWidgets.QSpinBox()
        self.spin_point_a_id.setRange(0, 1000)
        self.spin_point_a_id.setValue(0)
        self.spin_point_a_id.setEnabled(False)
        self.cmb_point_a_type.currentIndexChanged.connect(lambda idx: self.spin_point_a_id.setEnabled(idx == 2))

        self.cmb_point_b_type = QtWidgets.QComboBox()
        self.cmb_point_b_type.addItems(["Camera", "Origin", "Marker ID", "Target Object"])
        self.cmb_point_b_type.setStyleSheet("font-size: 11px;")

        self.spin_point_b_id = QtWidgets.QSpinBox()
        self.spin_point_b_id.setRange(0, 1000)
        self.spin_point_b_id.setValue(1)
        self.spin_point_b_id.setEnabled(False)
        self.cmb_point_b_type.currentIndexChanged.connect(lambda idx: self.spin_point_b_id.setEnabled(idx == 2))

        self.btn_add_distance = QtWidgets.QPushButton("➕ Add")
        self.btn_delete_distance = QtWidgets.QPushButton("➖ Delete")

        btn_ctrl_style = """
            QPushButton {
                background-color: #21262d;
                border: 1px solid #30363d;
                color: #c9d1d9;
                font-size: 11px;
                padding: 4px 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #30363d;
                color: #58a6ff;
            }
        """
        self.btn_add_distance.setStyleSheet(btn_ctrl_style)
        self.btn_delete_distance.setStyleSheet(btn_ctrl_style)

        self.btn_add_distance.clicked.connect(self.on_add_distance_spec)
        self.btn_delete_distance.clicked.connect(self.on_delete_distance_spec)

        add_layout.addWidget(self.txt_dist_desc)
        add_layout.addWidget(QtWidgets.QLabel("A:"))
        add_layout.addWidget(self.cmb_point_a_type)
        add_layout.addWidget(self.spin_point_a_id)
        add_layout.addWidget(QtWidgets.QLabel("B:"))
        add_layout.addWidget(self.cmb_point_b_type)
        add_layout.addWidget(self.spin_point_b_id)
        add_layout.addWidget(self.btn_add_distance)
        add_layout.addWidget(self.btn_delete_distance)

        tab_dist_layout.addLayout(add_layout)
        self.aruco_tab_widget.addTab(tab_distances, "📏 Distance Measurements")

        aruco_panel_layout.addWidget(self.aruco_tab_widget, stretch=6)

        self.main_splitter.addWidget(self.aruco_panel)

        right_layout.addWidget(self.main_splitter)

        # Footer Telemetry Status Bar
        self.status_bar = QtWidgets.QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Connecting to hardware module...")

        main_layout.addWidget(right_container)

    def showEvent(self, event):
        super().showEvent(event)
        # Set dynamic splitter sizes after window renders (75% viewports, 25% graphs)
        self.main_splitter.setSizes([550, 180])

    def init_camera_sliders(self):
        try:
            # Query actual connection details
            dev = self.cam.device
            dev_name = dev.get_info(rs.camera_info.name) if dev.supports(rs.camera_info.name) else "D435i"
            dev_sn = dev.get_info(rs.camera_info.serial_number) if dev.supports(rs.camera_info.serial_number) else "347622073229"
            dev_fw = dev.get_info(rs.camera_info.firmware_version) if dev.supports(rs.camera_info.firmware_version) else "5.17.0.10"
            dev_usb = dev.get_info(rs.camera_info.usb_type_descriptor) if dev.supports(rs.camera_info.usb_type_descriptor) else "3.2"

            self.usb_lbl.setText(f"USB: {dev_usb}  |  S/N: {dev_sn}")
            self.fw_lbl.setText(f"FW: {dev_fw}")

            # Populate toggle info panel rows dynamically
            for label, info_key, default_val in self.info_properties:
                val = default_val
                if info_key is not None and dev.supports(info_key):
                    val = dev.get_info(info_key)
                if label in self.info_value_labels:
                    self.info_value_labels[label].setText(str(val))

            # Read camera baseline values and set sliders
            power = self.cam.get_laser_power()
            self.laser_slider.setValue(power)

            emitter = self.cam.get_emitter_state()
            self.emitter_combo.setCurrentIndex(emitter)

            preset = self.cam.get_visual_preset()
            if 0 <= preset <= 5:
                self.preset_combo.setCurrentIndex(preset)

            auto_exp = self.cam.get_auto_exposure()
            self.auto_exp_chk.setChecked(auto_exp)

            exp = self.cam.get_exposure()
            self.exp_slider.setValue(exp)

            self.status_bar.showMessage("RealSense Hardware configured and streaming successfully.", 4000)
        except Exception as e:
            self.status_bar.showMessage(f"Error reading initial hardware configurations: {e}")

    # ----------------- SIDEBAR CONTROLS SLOTS -----------------
    def toggle_info_panel(self):
        visible = not self.info_panel.isVisible()
        self.info_panel.setVisible(visible)
        self.info_btn.setText("ℹ Hide Details" if visible else "ℹ Info")

    def on_preset_changed(self, idx):
        self.cam.set_visual_preset(idx)
        self.status_bar.showMessage(f"Visual Preset changed to: {self.preset_combo.currentText()}", 2000)

    def load_device_settings(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Load Device Settings", "", "JSON Files (*.json)"
        )
        if file_path:
            try:
                with open(file_path, "r") as f:
                    settings_json = f.read()
                dev = self.cam.device
                adv_mode = rs.rs400_advanced_mode(dev)
                if adv_mode.is_enabled():
                    adv_mode.load_json(settings_json)
                    self.status_bar.showMessage(f"Device settings loaded from: {os.path.basename(file_path)}", 5000)
                    self.init_camera_sliders()
                else:
                    QtWidgets.QMessageBox.warning(self, "Load Settings", "Advanced Mode is not active on this sensor.")
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "Load Settings", f"Failed to load settings: {e}")

    def save_device_settings(self):
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Device Settings", "realsense_presets.json", "JSON Files (*.json)"
        )
        if file_path:
            try:
                dev = self.cam.device
                adv_mode = rs.rs400_advanced_mode(dev)
                if adv_mode.is_enabled():
                    settings_json = adv_mode.serialize_json()
                    with open(file_path, "w") as f:
                        f.write(settings_json)
                    self.status_bar.showMessage(f"Device settings saved to: {os.path.basename(file_path)}", 5000)
                else:
                    QtWidgets.QMessageBox.warning(self, "Save Settings", "Advanced Mode is not active on this sensor.")
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "Save Settings", f"Failed to save settings: {e}")

    def on_hardware_reset(self):
        try:
            self.status_bar.showMessage("Initiating Camera Hardware Reset...", 3000)
            self.cam.device.hardware_reset()
            QtWidgets.QMessageBox.information(
                self, "Hardware Reset", "RealSense device hardware reset command sent successfully. Reconnect camera if needed."
            )
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Hardware Reset", f"Failed to reset device: {e}")

    def on_depth_toggled(self, enabled):
        self.worker.set_depth_enabled(enabled)
        self.depth_card.setVisible(enabled)
        self.update_placeholder_visibility()

    def on_rgb_toggled(self, enabled):
        self.worker.set_rgb_enabled(enabled)
        self.rgb_card.setVisible(enabled)
        self.update_placeholder_visibility()

    def on_hsv_view_toggled(self, enabled):
        self.worker.set_hsv_enabled(enabled)
        self.hsv_card.setVisible(enabled)
        self.update_placeholder_visibility()

    def update_placeholder_visibility(self):
        rgb_visible = self.rgb_card.isVisible()
        depth_visible = self.depth_card.isVisible()
        hsv_visible = self.hsv_card.isVisible()
        self.placeholder_widget.setVisible(
            not rgb_visible and not depth_visible and not hsv_visible
        )

    def on_emitter_changed(self, idx):
        self.cam.set_emitter_state(idx)
        self.status_bar.showMessage(f"IR Emitter state changed to: {self.emitter_combo.currentText()}", 2000)

    def on_laser_changed(self, val):
        self.cam.set_laser_power(val)

    def on_auto_exp_changed(self, enabled):
        self.cam.set_auto_exposure(enabled)
        self.exp_slider.setEnabled(not enabled)
        if not enabled:
            self.cam.set_exposure(self.exp_slider.value())
        self.status_bar.showMessage(f"Auto Exposure: {'Enabled' if enabled else 'Disabled (Manual)'}", 2000)

    def on_exposure_changed(self, val):
        if not self.auto_exp_chk.isChecked():
            self.cam.set_exposure(val)

    @QtCore.Slot()
    def on_apply_camera_settings(self):
        res_text = self.cmb_resolution.currentText()
        fps_text = self.cmb_fps.currentText()
        
        try:
            w, h = map(int, res_text.split("x"))
            fps = int(fps_text)
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Invalid Selection", f"Could not parse selected resolution/fps: {e}")
            return
            
        if w == self.cam.width and h == self.cam.height and fps == self.cam.fps:
            self.status_bar.showMessage("Camera settings are already at the selected resolution and FPS.", 3000)
            return
            
        self.restart_camera_stream(w, h, fps)

    def restart_camera_stream(self, width, height, fps):
        self.status_bar.showMessage("Re-configuring camera stream, please wait...")
        
        # 1. Stop the worker thread
        self.worker.running = False
        self.worker.wait()
        
        # 2. Stop the current camera pipeline
        try:
            self.cam.stop()
        except Exception as e:
            print(f"Error stopping pipeline: {e}")
            
        old_width = self.cam.width
        old_height = self.cam.height
        old_fps = self.cam.fps
        
        try:
            # 3. Reconfigure the camera parameters
            self.cam.width = width
            self.cam.height = height
            self.cam.fps = fps
            self.cam.pipeline = rs.pipeline()
            self.cam.config = rs.config()
            self.cam.config.enable_stream(rs.stream.depth, width, height, rs.format.z16, fps)
            self.cam.config.enable_stream(rs.stream.color, width, height, rs.format.bgr8, fps)
            self.cam.align = rs.align(rs.stream.color)
            
            # 4. Start the camera
            self.cam.start()
            
            # 5. Restart the worker thread
            self.worker.running = True
            self.worker.start()
            
            # Re-initialize camera UI elements / sliders
            self.init_camera_sliders()
            
            self.status_bar.showMessage(f"Camera re-configured successfully: {width}x{height} @ {fps} FPS.", 5000)
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "Configuration Error",
                f"Failed to start RealSense camera at {width}x{height} @ {fps} FPS.\n"
                f"Error: {e}\n\n"
                f"Reverting to previous working configuration."
            )
            try:
                # Revert to old configuration
                self.cam.width = old_width
                self.cam.height = old_height
                self.cam.fps = old_fps
                self.cam.pipeline = rs.pipeline()
                self.cam.config = rs.config()
                self.cam.config.enable_stream(rs.stream.depth, old_width, old_height, rs.format.z16, old_fps)
                self.cam.config.enable_stream(rs.stream.color, old_width, old_height, rs.format.bgr8, old_fps)
                self.cam.align = rs.align(rs.stream.color)
                
                self.cam.start()
                
                self.worker.running = True
                self.worker.start()
                
                self.init_camera_sliders()
                
                # Reset UI dropdowns to previous working text
                self.cmb_resolution.setCurrentText(f"{old_width}x{old_height}")
                self.cmb_fps.setCurrentText(str(old_fps))
                
            except Exception as revert_err:
                QtWidgets.QMessageBox.critical(
                    self, "Fatal Error",
                    f"Fatal: Failed to revert to previous working camera configuration!\n"
                    f"Error: {revert_err}\n\n"
                    f"Please restart the application."
                )

    def on_hsv_changed(self, val):
        lower = np.array([self.h_min.value(), self.s_min.value(), self.v_min.value()])
        upper = np.array([self.h_max.value(), self.s_max.value(), self.v_max.value()])
        self.worker.update_hsv_bounds(lower, upper)

    def on_tracking_target_changed(self):
        idx = self.tracker_target_combo.currentIndex()
        if idx == 0:
            # Tennis Ball (HSV)
            self.hsv_settings_widget.setVisible(True)
            self.aruco_settings_widget.setVisible(False)
            self.aruco_panel.setVisible(True)
            if self.graph_visible:
                self.graph_panel.setVisible(True)
            self.worker.set_target_mode("hsv")
            
            # Reset sliders to Ball defaults
            self.h_min.setValue(29)
            self.h_max.setValue(64)
            self.s_min.setValue(86)
            self.s_max.setValue(255)
            self.v_min.setValue(6)
            self.v_max.setValue(255)
            
            self.status_bar.showMessage("Tracking Target: Tennis Ball (HSV Color Segmentation)", 3000)
        elif idx == 1:
            # Orange Scissors (HSV)
            self.hsv_settings_widget.setVisible(True)
            self.aruco_settings_widget.setVisible(False)
            self.aruco_panel.setVisible(True)
            if self.graph_visible:
                self.graph_panel.setVisible(True)
            self.worker.set_target_mode("hsv_scissors")
            
            # Reset sliders to Orange Scissors defaults
            self.h_min.setValue(0)
            self.h_max.setValue(18)
            self.s_min.setValue(100)
            self.s_max.setValue(255)
            self.v_min.setValue(100)
            self.v_max.setValue(255)
            
            self.status_bar.showMessage("Tracking Target: Orange Scissors (HSV Color Segmentation)", 3000)
        else:
            # ArUco Marker
            self.hsv_settings_widget.setVisible(False)
            self.aruco_settings_widget.setVisible(True)
            self.graph_panel.setVisible(False)
            self.aruco_panel.setVisible(True)
            self.worker.set_target_mode("aruco")
            self.status_bar.showMessage("Tracking Target: ArUco Marker 3D Pose Estimation", 3000)

    def on_aruco_settings_changed(self):
        # Dictionary
        dict_idx = self.aruco_dict_combo.currentIndex()
        dict_val = self.aruco_dict_list[dict_idx][1]
        self.worker.set_aruco_dictionary(dict_val)
        
        # Marker Size (convert mm to meters)
        size_mm = self.aruco_size_spin.value()
        self.worker.set_aruco_marker_size(size_mm / 1000.0)
        
        # Target ID
        target_id = self.aruco_id_spin.value()
        self.worker.set_aruco_target_id(target_id)

    @QtCore.Slot()
    def on_ref_settings_changed(self):
        idx = self.cmb_ref_mode.currentIndex()
        ref_id = self.spin_ref_id.value()
        
        mode = "camera"
        if idx == 1:
            mode = "live_marker"
        elif idx == 2:
            mode = "static_world"
            
        enabled = (mode != "camera")
        self.worker.set_aruco_ref_enabled(enabled)
        self.worker.set_aruco_ref_mode(mode)
        self.worker.set_aruco_ref_id(ref_id)

    # ----------------- ACTION BUTTONS SLOTS -----------------
    def toggle_pause_rgb(self):
        self.play_rgb = not self.play_rgb
        self.btn_pause_rgb.setText("▶" if not self.play_rgb else "⏸")
        self.btn_pause_rgb.setToolTip("Resume Stream" if not self.play_rgb else "Pause Stream")

    def toggle_pause_depth(self):
        self.play_depth = not self.play_depth
        self.btn_pause_depth.setText("▶" if not self.play_depth else "⏸")
        self.btn_pause_depth.setToolTip("Resume Stream" if not self.play_depth else "Pause Stream")

    def toggle_pause_hsv(self):
        self.play_hsv = not self.play_hsv
        self.btn_pause_hsv.setText("▶" if not self.play_hsv else "⏸")
        self.btn_pause_hsv.setToolTip("Resume Stream" if not self.play_hsv else "Pause Stream")

    def toggle_graph_panel(self, checked):
        self.graph_visible = checked
        self.graph_panel.setVisible(checked)
        self.btn_graph_rgb.setChecked(checked)
        self.btn_graph_depth.setChecked(checked)

    def capture_rgb(self):
        if self.last_raw_color_frame is not None:
            filename = os.path.join(CAPTURES_DIR, f"capture_color_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            success = cv2.imwrite(filename, self.last_raw_color_frame)
            if success:
                self.status_bar.showMessage(f"Saved Clean RGB Capture: {os.path.basename(filename)}", 5000)
            else:
                QtWidgets.QMessageBox.warning(self, "Screenshot Failed", f"Failed to save RGB image file: {filename}")
        else:
            QtWidgets.QMessageBox.warning(self, "Screenshot Failed", "No RGB frame captured yet.")

    def capture_depth(self):
        if self.last_depth_frame is not None:
            filename = os.path.join(CAPTURES_DIR, f"capture_depth_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            success = cv2.imwrite(filename, self.last_depth_frame)
            if success:
                self.status_bar.showMessage(f"Saved Depth Capture: {os.path.basename(filename)}", 5000)
            else:
                QtWidgets.QMessageBox.warning(self, "Screenshot Failed", f"Failed to save depth image file: {filename}")
        else:
            QtWidgets.QMessageBox.warning(self, "Screenshot Failed", "No depth frame captured yet.")

    def capture_hsv(self):
        if self.last_mask_frame is not None:
            filename = os.path.join(CAPTURES_DIR, f"capture_mask_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            success = cv2.imwrite(filename, self.last_mask_frame)
            if success:
                self.status_bar.showMessage(f"Saved HSV Mask Capture: {os.path.basename(filename)}", 5000)
            else:
                QtWidgets.QMessageBox.warning(self, "Screenshot Failed", f"Failed to save HSV mask image file: {filename}")
        else:
            QtWidgets.QMessageBox.warning(self, "Screenshot Failed", "No HSV mask frame captured yet.")

    # ----------------- INCOMING FRAME PROCESSING -----------------
    def on_frame_ready(self, color, raw_color, depth_map, mask, tracker_status, coords, aruco_data=None):
        # Cache frames for screenshots
        self.last_color_frame = color
        self.last_raw_color_frame = raw_color
        self.last_depth_frame = depth_map
        self.last_mask_frame = mask
 
        # Update reference coordinate system status and cache live pose for calibration
        if aruco_data:
            ref_active = aruco_data.get("ref_active", False)
            ref_id = aruco_data.get("ref_id", 0)
            ref_mode = self.worker.aruco_ref_mode
            
            if ref_active and ref_mode == "live_marker":
                self.last_ref_rvec = aruco_data.get("ref_rvec", None)
                self.last_ref_tvec = aruco_data.get("ref_tvec", None)
                
            if ref_mode == "static_world":
                self.lbl_ref_status.setText("Origin Reference: Active (Static Calibrated World)")
                self.lbl_ref_status.setStyleSheet("color: #2ea043; font-weight: bold; font-size: 11px;")
                
                self.origin_info_box.setVisible(True)
                self.lbl_origin_id.setText(f"Reference ID (Static World): ID {ref_id}")
                if self.worker.static_ref_tvec is not None and self.worker.static_ref_rvec is not None:
                    ot = np.array(self.worker.static_ref_tvec).flatten()
                    self.lbl_origin_coords_cam.setText(f"Camera Frame (Before World):\n  X: {ot[0]:+.3f}m, Y: {ot[1]:+.3f}m, Z: {ot[2]:.3f}m")
                    
                    # Compute camera position relative to origin
                    R_ref, _ = cv2.Rodrigues(np.array(self.worker.static_ref_rvec, dtype=np.float32))
                    T_ref = np.array(self.worker.static_ref_tvec, dtype=np.float32).reshape(3, 1)
                    cam_pos = -R_ref.T @ T_ref
                    cx, cy, cz = float(cam_pos[0][0]), float(cam_pos[1][0]), float(cam_pos[2][0])
                    self.lbl_camera_coords_world.setText(f"Camera Position (in World Frame):\n  X: {cx:+.3f}m, Y: {cy:+.3f}m, Z: {cz:.3f}m")
                else:
                    self.lbl_origin_coords_cam.setText("Camera Frame (Before World): --")
                    self.lbl_camera_coords_world.setText("Camera Position (in World Frame): --")
                
                # Object-to-Origin Distance
                if tracker_status:
                    dist_obj = np.linalg.norm(coords) if not np.isnan(coords).any() else 0.0
                    self.lbl_origin_distance_obj.setText(f"Object-to-Origin Distance: {dist_obj:.3f} m")
                    self.lbl_origin_distance_obj.setStyleSheet("color: #2ea043; font-weight: bold; font-size: 12px;")
                else:
                    self.lbl_origin_distance_obj.setText("Object-to-Origin Distance: -- (No Tracked Target)")
                    self.lbl_origin_distance_obj.setStyleSheet("color: #8b949e; font-size: 11px;")
                    
            elif ref_mode == "live_marker":
                if ref_active:
                    self.lbl_ref_status.setText(f"Origin Reference: Active (Live Marker ID {ref_id})")
                    self.lbl_ref_status.setStyleSheet("color: #2ea043; font-weight: bold; font-size: 11px;")
                else:
                    self.lbl_ref_status.setText(f"Origin Reference: Search Failed (Marker ID {ref_id} out of view)")
                    self.lbl_ref_status.setStyleSheet("color: #f85149; font-weight: bold; font-size: 11px;")
                    
                self.origin_info_box.setVisible(True)
                self.lbl_origin_id.setText(f"Reference ID (Live Marker): ID {ref_id}")
                if ref_active and aruco_data.get("ref_tvec") is not None and aruco_data.get("ref_rvec") is not None:
                    ot = np.array(aruco_data.get("ref_tvec")).flatten()
                    self.lbl_origin_coords_cam.setText(f"Camera Frame (Before World):\n  X: {ot[0]:+.3f}m, Y: {ot[1]:+.3f}m, Z: {ot[2]:.3f}m")
                    
                    # Compute camera position relative to origin
                    R_ref, _ = cv2.Rodrigues(np.array(aruco_data.get("ref_rvec"), dtype=np.float32))
                    T_ref = np.array(aruco_data.get("ref_tvec"), dtype=np.float32).reshape(3, 1)
                    cam_pos = -R_ref.T @ T_ref
                    cx, cy, cz = float(cam_pos[0][0]), float(cam_pos[1][0]), float(cam_pos[2][0])
                    self.lbl_camera_coords_world.setText(f"Camera Position (in World Frame):\n  X: {cx:+.3f}m, Y: {cy:+.3f}m, Z: {cz:.3f}m")
                else:
                    self.lbl_origin_coords_cam.setText("Camera Frame (Before World): Out of View")
                
                # Object-to-Origin Distance
                if tracker_status and ref_active:
                    dist_obj = np.linalg.norm(coords) if not np.isnan(coords).any() else 0.0
                    self.lbl_origin_distance_obj.setText(f"Object-to-Origin Distance: {dist_obj:.3f} m")
                    self.lbl_origin_distance_obj.setStyleSheet("color: #2ea043; font-weight: bold; font-size: 12px;")
                else:
                    self.lbl_origin_distance_obj.setText("Object-to-Origin Distance: -- (Origin Out of View)")
                    self.lbl_origin_distance_obj.setStyleSheet("color: #8b949e; font-size: 11px;")
            else:
                self.lbl_ref_status.setText("Origin Reference: Inactive (Using Camera Frame)")
                self.lbl_ref_status.setStyleSheet("color: #8b949e; font-size: 11px;")
                self.origin_info_box.setVisible(False)

        # 1. Update RGB Viewport
        if self.play_rgb and self.rgb_card.isVisible():
            q_img = self.cv_to_qimage(color)
            self.rgb_video_label.setPixmap(QtGui.QPixmap.fromImage(q_img))
        elif not self.play_rgb and self.rgb_card.isVisible():
            paused_pix = self.get_placeholder_pixmap("RGB STREAM PAUSED")
            self.rgb_video_label.setPixmap(paused_pix)

        # 2. Update Depth Viewport
        if self.play_depth and self.depth_card.isVisible():
            q_depth = self.cv_to_qimage(depth_map)
            self.depth_video_label.setPixmap(QtGui.QPixmap.fromImage(q_depth))
        elif not self.play_depth and self.depth_card.isVisible():
            paused_pix = self.get_placeholder_pixmap("DEPTH STREAM PAUSED")
            self.depth_video_label.setPixmap(paused_pix)

        # 3. Update HSV Viewport
        if self.play_hsv and self.hsv_card.isVisible():
            # Convert binary single channel mask to 3-channel for rendering
            mask_bgr = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
            q_mask = self.cv_to_qimage(mask_bgr)
            self.hsv_video_label.setPixmap(QtGui.QPixmap.fromImage(q_mask))
        elif not self.play_hsv and self.hsv_card.isVisible():
            paused_pix = self.get_placeholder_pixmap("HSV MASK STREAM PAUSED")
            self.hsv_video_label.setPixmap(paused_pix)

        # 4. Telemetry coordinates updates / Graphs
        if tracker_status:
            x, y, z = coords
            dist = np.linalg.norm(coords) if not np.isnan(coords).any() else 0.0
            
            # Apply motion filter
            fx, fy, fz = self.coord_filter.filter(x, y, z)
            f_dist = np.linalg.norm([fx, fy, fz]) if not np.isnan([fx, fy, fz]).any() else 0.0

            # Update physical coordinates displaying both smoothed and raw
            self.lbl_phys_x.setText(f"X: {fx:+.3f} m (Raw: {x:+.3f})")
            self.lbl_phys_y.setText(f"Y: {fy:+.3f} m (Raw: {y:+.3f})")
            self.lbl_phys_z.setText(f"Z:  {fz:.3f} m (Raw:  {z:.3f})")
            self.lbl_phys_dist.setText(f"Distance: {f_dist:.3f} m (Raw: {dist:.3f})")

            # Send coordinate to robot serial port / simulation if enabled
            if self.chk_robot_transmit.isChecked():
                success, tx_cmd = self.robot_comm.send_coordinates(fx, fy, fz)
                if success:
                    self.lbl_robot_status.setText(f"Status: Transmitting\nTX: {tx_cmd}")
                    self.lbl_robot_status.setStyleSheet("color: #2ea043; font-weight: bold; font-size: 10px;")
                else:
                    self.lbl_robot_status.setText(f"Status: TX Throttled / Offline")
                    self.lbl_robot_status.setStyleSheet("color: #8b949e; font-size: 10px; font-style: italic;")

            # Extract target pixel coordinates
            u, v = (None, None)
            if aruco_data:
                pixel_coords = aruco_data.get("target_pixel")
                if pixel_coords is not None:
                    u, v = pixel_coords

            if u is not None and v is not None:
                self.lbl_pixel_u.setText(f"U: {u:.1f} px")
                self.lbl_pixel_v.setText(f"V: {v:.1f} px")
                norm_u = u / self.cam.width
                norm_v = v / self.cam.height
                self.lbl_pixel_norm.setText(f"Norm: ({norm_u:.2f}, {norm_v:.2f})")
                self.lbl_track_status.setText("Status: TRACKING")
                self.lbl_track_status.setStyleSheet("color: #2ea043; font-family: 'Consolas', 'Courier New', monospace; font-size: 11px; font-weight: bold;")
            else:
                self.lbl_pixel_u.setText("U: -- px")
                self.lbl_pixel_v.setText("V: -- px")
                self.lbl_pixel_norm.setText("Norm: (--, --)")
                self.lbl_track_status.setText("Status: Searching")
                self.lbl_track_status.setStyleSheet("color: #f85149; font-family: 'Consolas', 'Courier New', monospace; font-size: 11px; font-weight: bold;")

            # If in ArUco mode, we can look up details in aruco_data
            if self.worker.target_mode == "aruco":
                t_name = aruco_data.get("target_name", "--") if aruco_data else "Marker"
                self.lbl_aruco_target_title.setText(f"Target: {t_name}")
            elif self.worker.target_mode == "hsv":
                self.lbl_aruco_target_title.setText("Target: Tennis Ball (HSV)")
                
                # Update status bar message
                ref_lbl = "Camera Frame"
                if aruco_data:
                    ref_active = aruco_data.get("ref_active", False)
                    ref_id = aruco_data.get("ref_id", 0)
                    if ref_active:
                        ref_lbl = f"Rel ID {ref_id}"
                self.status_bar.showMessage(
                    f"TARGET TRACKING ACTIVE  |  X: {fx:+.3f}m  |  Y: {fy:+.3f}m  |  Z: {fz:.3f}m ({ref_lbl})"
                )
            elif self.worker.target_mode == "hsv_scissors":
                self.lbl_aruco_target_title.setText("Target: Orange Scissors (HSV)")
                
                # Update status bar message
                ref_lbl = "Camera Frame"
                if aruco_data:
                    ref_active = aruco_data.get("ref_active", False)
                    ref_id = aruco_data.get("ref_id", 0)
                    if ref_active:
                        ref_lbl = f"Rel ID {ref_id}"
                self.status_bar.showMessage(
                    f"TARGET TRACKING ACTIVE  |  X: {fx:+.3f}m  |  Y: {fy:+.3f}m  |  Z: {fz:.3f}m ({ref_lbl})"
                )

            # Append history for graphs (using filtered values)
            self.z_history.append(fz)
            self.x_history.append(fx)
            self.y_history.append(fy)
        else:
            self.coord_filter.reset()
            self.lbl_phys_x.setText("X: +0.000 m")
            self.lbl_phys_y.setText("Y: +0.000 m")
            self.lbl_phys_z.setText("Z:  0.000 m")
            self.lbl_phys_dist.setText("Distance: 0.000 m")
            self.lbl_pixel_u.setText("U: -- px")
            self.lbl_pixel_v.setText("V: -- px")
            self.lbl_pixel_norm.setText("Norm: (--, --)")
            self.lbl_track_status.setText("Status: SEARCHING")
            self.lbl_track_status.setStyleSheet("color: #f85149; font-family: 'Consolas', 'Courier New', monospace; font-size: 11px; font-weight: bold;")
            
            # Reset connection status display back to standard connected when not transmitting
            if self.robot_comm.is_connected():
                port = self.robot_comm.port
                self.lbl_robot_status.setText(f"Status: Connected ({port})" if port != "Mock/Simulated" else "Status: Simulated Mode Active")
                self.lbl_robot_status.setStyleSheet("color: #2ea043; font-weight: bold; font-size: 10px;")

            if self.worker.target_mode == "aruco":
                self.status_bar.showMessage("SEARCHING FOR ARUCO MARKER TARGET...")
                self.lbl_aruco_target_title.setText("Target: --")
            elif self.worker.target_mode == "hsv":
                self.status_bar.showMessage("SEARCHING FOR BALL TARGET (Check HSV bounds)...")
                self.lbl_aruco_target_title.setText("Target: Tennis Ball (HSV)")
            else:
                self.status_bar.showMessage("SEARCHING FOR SCISSORS TARGET (Check HSV bounds)...")
                self.lbl_aruco_target_title.setText("Target: Orange Scissors (HSV)")
            
            self.z_history.append(float("nan"))
            self.x_history.append(float("nan"))
            self.y_history.append(float("nan"))

        # Update detected markers table if ArUco data is available (runs in all target modes)
        if aruco_data:
            detected = aruco_data.get("detected_markers", [])
            self.tbl_aruco_detections.setRowCount(0)
            for m in detected:
                row = self.tbl_aruco_detections.rowCount()
                self.tbl_aruco_detections.insertRow(row)
                self.tbl_aruco_detections.setItem(row, 0, QtWidgets.QTableWidgetItem(f"ID {m['id']}"))
                self.tbl_aruco_detections.setItem(row, 1, QtWidgets.QTableWidgetItem(f"{m['x']:+.3f}"))
                self.tbl_aruco_detections.setItem(row, 2, QtWidgets.QTableWidgetItem(f"{m['y']:+.3f}"))
                self.tbl_aruco_detections.setItem(row, 3, QtWidgets.QTableWidgetItem(f"{m['z']:+.3f}"))
                self.tbl_aruco_detections.setItem(row, 4, QtWidgets.QTableWidgetItem(f"{m['dist']:.3f}"))
                
                for col in range(5):
                    item = self.tbl_aruco_detections.item(row, col)
                    if item:
                        item.setTextAlignment(QtCore.Qt.AlignCenter)

            # Build coordinates mapping for active markers and special points
            point_coords = {}
            point_coords["Origin"] = (0.0, 0.0, 0.0)
            
            # Compute camera position
            ref_active = aruco_data.get("ref_active", False)
            ref_tvec = aruco_data.get("ref_tvec", None)
            ref_rvec = aruco_data.get("ref_rvec", None)
            
            if ref_active and ref_tvec is not None and ref_rvec is not None:
                R_ref, _ = cv2.Rodrigues(np.array(ref_rvec, dtype=np.float32))
                T_ref = np.array(ref_tvec, dtype=np.float32)
                cam_pos = -R_ref.T @ T_ref
                point_coords["Camera"] = (float(cam_pos[0][0]), float(cam_pos[1][0]), float(cam_pos[2][0]))
            else:
                point_coords["Camera"] = (0.0, 0.0, 0.0)
                
            for m in detected:
                point_coords[f"Marker {m['id']}"] = (m["x"], m["y"], m["z"])
                
            # Add target object if it's currently tracked
            if tracker_status:
                point_coords["Target Object"] = (x, y, z)

            # Populate distances table
            self.tbl_aruco_distances.blockSignals(True)
            self.tbl_aruco_distances.setRowCount(0)
            for spec in self.distance_specifications:
                desc = spec["desc"]
                pt_a = spec["point_a"]
                pt_b = spec["point_b"]
                
                missing = []
                if pt_a not in point_coords:
                    missing.append(pt_a)
                if pt_b not in point_coords:
                    missing.append(pt_b)
                    
                if len(missing) == 0:
                    coords_a = np.array(point_coords[pt_a])
                    coords_b = np.array(point_coords[pt_b])
                    d_val = float(np.linalg.norm(coords_a - coords_b))
                    status_lbl = "OK"
                else:
                    d_val = 0.0
                    status_lbl = "Missing " + " & ".join(missing)
                    
                row = self.tbl_aruco_distances.rowCount()
                self.tbl_aruco_distances.insertRow(row)
                
                self.tbl_aruco_distances.setItem(row, 0, QtWidgets.QTableWidgetItem(desc))
                self.tbl_aruco_distances.setItem(row, 1, QtWidgets.QTableWidgetItem(pt_a))
                self.tbl_aruco_distances.setItem(row, 2, QtWidgets.QTableWidgetItem(pt_b))
                
                dist_item = QtWidgets.QTableWidgetItem(f"{d_val:.3f}")
                status_item = QtWidgets.QTableWidgetItem(status_lbl)
                
                self.tbl_aruco_distances.setItem(row, 3, dist_item)
                self.tbl_aruco_distances.setItem(row, 4, status_item)
                
                # Center all items except description
                for col in range(5):
                    item = self.tbl_aruco_distances.item(row, col)
                    if item:
                        if col > 0:
                            item.setTextAlignment(QtCore.Qt.AlignCenter)
                        if col != 0:
                            item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
                            
            self.tbl_aruco_distances.blockSignals(False)

            # Log coordinates/distances to CSV if active
            if self.log_file and self.log_writer:
                self.log_frame_count += 1
                elapsed = time.time() - self.log_start_time
                timestamp = datetime.now().isoformat()
                ref_lbl = f"Relative (Marker ID {self.worker.aruco_ref_id})" if self.worker.aruco_ref_enabled else "Camera (Absolute)"
                
                try:
                    # Log all detected markers
                    for m in detected:
                        self.log_writer.writerow([
                            timestamp,
                            f"{elapsed:.3f}",
                            self.log_frame_count,
                            ref_lbl,
                            "MARKER",
                            f"ID {m['id']}",
                            f"{m['x']:.6f}",
                            f"{m['y']:.6f}",
                            f"{m['z']:.6f}",
                            f"{m['dist']:.6f}"
                        ])
                        
                    # Log all distances
                    for spec in self.distance_specifications:
                        desc = spec["desc"]
                        pt_a = spec["point_a"]
                        pt_b = spec["point_b"]
                        
                        missing = []
                        if pt_a not in point_coords:
                            missing.append(pt_a)
                        if pt_b not in point_coords:
                            missing.append(pt_b)
                            
                        if len(missing) == 0:
                            coords_a = np.array(point_coords[pt_a])
                            coords_b = np.array(point_coords[pt_b])
                            d_val = float(np.linalg.norm(coords_a - coords_b))
                            status_lbl = "OK"
                        else:
                            d_val = 0.0
                            status_lbl = "Missing " + " & ".join(missing)
                            
                        self.log_writer.writerow([
                            timestamp,
                            f"{elapsed:.3f}",
                            self.log_frame_count,
                            ref_lbl,
                            "DISTANCE",
                            desc,
                            pt_a,
                            pt_b,
                            status_lbl,
                            f"{d_val:.6f}"
                        ])
                    self.log_file.flush()
                except Exception as e:
                    print(f"Error writing to coordinates CSV: {e}")

        self.time_history.append(self.time_counter)
        self.time_counter += 1

        # Keep history buffer capped at 150 points
        if len(self.time_history) > 150:
            self.z_history.pop(0)
            self.x_history.pop(0)
            self.y_history.pop(0)
            self.time_history.pop(0)

        # 5. Update Graphs if visible
        if self.graph_visible:
            self.z_curve.setData(self.z_history)
            self.x_curve.setData(self.x_history)
            self.y_curve.setData(self.y_history)

    def on_fps_updated(self, fps):
        self.fps = fps
        self.rgb_fps_lbl.setText(f"640x480 @ {fps:.1f} FPS")
        self.depth_fps_lbl.setText(f"640x480 @ {fps:.1f} FPS")
        self.hsv_fps_lbl.setText(f"640x480 @ {fps:.1f} FPS")

    def on_error(self, err_msg):
        QtWidgets.QMessageBox.critical(self, "Camera Pipeline Error", err_msg)
        self.status_bar.showMessage(f"Pipeline error: {err_msg}")

    # ----------------- UTILITY FUNCTIONS -----------------
    def cv_to_qimage(self, cv_img):
        rgb_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_img.shape
        bytes_per_line = ch * w
        q_img = QtGui.QImage(rgb_img.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        return q_img.copy()

    def get_placeholder_pixmap(self, text):
        pix = QtGui.QPixmap(640, 480)
        pix.fill(QtGui.QColor("#161b22"))
        painter = QtGui.QPainter(pix)
        painter.setPen(QtGui.QPen(QtGui.QColor("#8b949e"), 2))
        font = QtGui.QFont("Segoe UI", 16, QtGui.QFont.Bold)
        painter.setFont(font)
        painter.drawText(pix.rect(), QtCore.Qt.AlignCenter, text)
        painter.end()
        return pix

    # ----------------- CALIBRATION SLOTS -----------------
    @QtCore.Slot()
    def switch_to_tracker_mode(self):
        self.btn_mode_tracker.setChecked(True)
        self.btn_mode_calib.setChecked(False)
        self.calib_sidebar_widget.setVisible(False)
        self.scroll_tracker_settings.setVisible(True)
        self.worker.set_calibration_mode(False)
        self.calib_viewports_container.setVisible(False)
        self.calib_results_panel.setVisible(False)
        
        # Show normal viewports
        self.viewport_container.setVisible(True)
        self.aruco_panel.setVisible(True)
        if self.graph_visible:
            self.graph_panel.setVisible(True)
        self.update_placeholder_visibility()
        self.status_bar.showMessage("Switched to Ball Tracker mode.")

    @QtCore.Slot()
    def switch_to_calib_mode(self):
        self.btn_mode_tracker.setChecked(False)
        self.btn_mode_calib.setChecked(True)
        self.scroll_tracker_settings.setVisible(False)
        self.calib_sidebar_widget.setVisible(True)
        self.worker.set_calibration_mode(True)
        
        # Hide normal viewports
        self.viewport_container.setVisible(False)
        self.graph_panel.setVisible(False)
        self.aruco_panel.setVisible(False)
        
        # Show calibration viewports & results
        self.calib_viewports_container.setVisible(True)
        self.calib_results_panel.setVisible(True)
        
        # Sync current settings
        self.on_calib_settings_changed()
        self.status_bar.showMessage("Switched to Intrinsic Calibration mode.")

    @QtCore.Slot()
    def on_calib_settings_changed(self):
        cols = self.spin_cols.value()
        rows = self.spin_rows.value()
        square_size = self.spin_size.value()
        auto_capture = self.chk_auto_capture.isChecked()
        self.worker.update_calib_settings(cols, rows, square_size, auto_capture)
        
        # Update expected corners
        expected = cols * rows
        self.lbl_calib_found.setText(f"Corners Found: 0 / {expected}")
        
        # Update target valid poses text
        captured = self.calib_frames_table.rowCount()
        target = self.spin_target.value()
        self.lbl_calib_valid.setText(f"Valid Poses Captured: {captured} / {target}")
        if captured >= target:
            self.lbl_calib_valid.setStyleSheet("color: #2ea043; font-size: 12px; font-weight: bold;")
        else:
            self.lbl_calib_valid.setStyleSheet("color: #c9d1d9; font-size: 12px; font-weight: bold;")

    @QtCore.Slot()
    def on_calib_manual_capture(self):
        self.worker.request_manual_capture()
        self.status_bar.showMessage("Manual capture requested.")

    @QtCore.Slot()
    def on_calib_run_calibration(self):
        self.status_bar.showMessage("Running calibration computation... Please wait.")
        self.worker.run_camera_calibration()

    @QtCore.Slot()
    def on_calib_clear_data(self):
        self.worker.clear_calibration_data()
        self.calib_frames_table.setRowCount(0)
        self.coverage_grid.reset_grid()
        self.lbl_reproj_error.setText("Reprojection Error: -- px")
        self.lbl_reproj_error.setStyleSheet("color: #8b949e; font-size: 22px; font-weight: bold;")
        
        cols = self.spin_cols.value()
        rows = self.spin_rows.value()
        expected = cols * rows
        self.lbl_calib_found.setText(f"Corners Found: 0 / {expected}")
        self.lbl_calib_valid.setText(f"Valid Poses Captured: 0 / {self.spin_target.value()}")
        self.lbl_calib_valid.setStyleSheet("color: #c9d1d9; font-size: 12px; font-weight: bold;")
        self.calib_results_text.setText("Intrinsics fx, fy, cx, cy: Not Calibrated\nDistortion k1, k2, p1, p2, k3: Not Calibrated")
        self.calib_undistort_video_label.setPixmap(QtGui.QPixmap())
        self.status_bar.showMessage("Calibration data and history cleared.")

    @QtCore.Slot()
    def on_calib_save_results(self):
        if self.worker.camera_matrix is None or self.worker.dist_coeffs is None:
            QtWidgets.QMessageBox.warning(self, "Save Calibration", "No calibration computed yet. Run calibration first.")
            return
            
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Calibration JSON", "calibration.json", "JSON Files (*.json)"
        )
        if file_path:
            import json
            try:
                # Get the error value from text label if possible
                err_text = self.lbl_reproj_error.text().replace("Reprojection Error: ", "").replace(" px", "")
                try:
                    reproj_err = float(err_text)
                except ValueError:
                    reproj_err = 0.0

                calib_dict = {
                    "camera_matrix": self.worker.camera_matrix.tolist(),
                    "distortion_coefficients": self.worker.dist_coeffs.tolist(),
                    "reprojection_error": reproj_err,
                    "resolution": [self.cam.width, self.cam.height],
                    "timestamp": datetime.now().isoformat()
                }
                with open(file_path, "w") as f:
                    json.dump(calib_dict, f, indent=4)
                self.status_bar.showMessage(f"Calibration saved to: {os.path.basename(file_path)}", 5000)
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "Save Calibration", f"Failed to save calibration: {e}")

    @QtCore.Slot()
    def on_calib_load_results(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Load Calibration JSON", "", "JSON Files (*.json)"
        )
        if file_path:
            import json
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                
                if "camera_matrix" not in data or "distortion_coefficients" not in data:
                    raise KeyError("Missing camera_matrix or distortion_coefficients key in JSON.")
                
                self.worker.camera_matrix = np.array(data["camera_matrix"], dtype=np.float32)
                self.worker.dist_coeffs = np.array(data["distortion_coefficients"], dtype=np.float32)
                
                # Update UI
                reproj_error = data.get("reprojection_error", 0.0)
                self.lbl_reproj_error.setText(f"Reprojection Error: {reproj_error:.3f} px")
                if reproj_error < 0.3:
                    self.lbl_reproj_error.setStyleSheet("color: #2ea043; font-size: 22px; font-weight: bold;")
                elif reproj_error <= 0.7:
                    self.lbl_reproj_error.setStyleSheet("color: #ffaa00; font-size: 22px; font-weight: bold;")
                else:
                    self.lbl_reproj_error.setStyleSheet("color: #f85149; font-size: 22px; font-weight: bold;")

                fx = self.worker.camera_matrix[0, 0]
                fy = self.worker.camera_matrix[1, 1]
                cx = self.worker.camera_matrix[0, 2]
                cy = self.worker.camera_matrix[1, 2]
                k1, k2, p1, p2, k3 = self.worker.dist_coeffs.ravel()[:5]
                
                results_str = (
                    f"Camera Matrix (Intrinsics):\n"
                    f"  fx = {fx:.3f} px\n"
                    f"  fy = {fy:.3f} px\n"
                    f"  cx = {cx:.3f} px\n"
                    f"  cy = {cy:.3f} px\n\n"
                    f"Distortion Coefficients:\n"
                    f"  k1 = {k1:+.6f}\n"
                    f"  k2 = {k2:+.6f}\n"
                    f"  p1 = {p1:+.6f}\n"
                    f"  p2 = {p2:+.6f}\n"
                    f"  k3 = {k3:+.6f}"
                )
                self.calib_results_text.setText(results_str)
                self.status_bar.showMessage(f"Calibration loaded from: {os.path.basename(file_path)}", 5000)
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "Load Calibration", f"Failed to load calibration: {e}")

    def on_calibration_update(self, annotated_img, undistorted_img, corners_detected, corners_found, sharpness, tilt_x, tilt_y, distance, coverage_sector):
        if not self.btn_mode_calib.isChecked():
            return
            
        q_img = self.cv_to_qimage(annotated_img)
        self.calib_live_video_label.setPixmap(QtGui.QPixmap.fromImage(q_img))
        
        if undistorted_img is not None:
            q_undist = self.cv_to_qimage(undistorted_img)
            self.calib_undistort_video_label.setPixmap(QtGui.QPixmap.fromImage(q_undist))
        else:
            self.calib_undistort_video_label.setPixmap(self.get_placeholder_pixmap("CALIBRATION REQUIRED\nUndistorted preview will appear here once calibrated."))
            
        # Update metrics panel
        if corners_detected:
            self.lbl_calib_corners.setText("Corners Detected: YES")
            self.lbl_calib_corners.setStyleSheet("color: #2ea043; font-weight: bold; font-size: 11px;")
        else:
            self.lbl_calib_corners.setText("Corners Detected: NO")
            self.lbl_calib_corners.setStyleSheet("color: #f85149; font-weight: bold; font-size: 11px;")
            
        expected = self.spin_cols.value() * self.spin_rows.value()
        self.lbl_calib_found.setText(f"Corners Found: {corners_found} / {expected}")
        
        self.lbl_calib_sharpness.setText(f"Sharpness: {sharpness:.1f} ({'Good' if sharpness >= 100 else 'Blurry'})")
        if sharpness >= 100:
            self.lbl_calib_sharpness.setStyleSheet("color: #2ea043; font-size: 11px;")
        else:
            self.lbl_calib_sharpness.setStyleSheet("color: #f85149; font-size: 11px;")
            
        self.lbl_calib_tilt.setText(f"Tilt X/Y: {tilt_x:+.1f}° / {tilt_y:+.1f}°")
        self.lbl_calib_dist.setText(f"Board Distance: {distance:.2f} m")
        self.lbl_calib_coverage.setText(f"Coverage: {coverage_sector}")

    def on_calib_frame_captured(self, frame_idx, sharpness, tilt_x, tilt_y, distance, sector_lbl, sector_r, sector_c):
        self.status_bar.showMessage(f"[CAPTURE] Pose #{frame_idx} captured in {sector_lbl}", 3000)
        
        # Add to table
        row = self.calib_frames_table.rowCount()
        self.calib_frames_table.insertRow(row)
        self.calib_frames_table.setItem(row, 0, QtWidgets.QTableWidgetItem(f"#{frame_idx}"))
        self.calib_frames_table.setItem(row, 1, QtWidgets.QTableWidgetItem(f"{sharpness:.1f}"))
        self.calib_frames_table.setItem(row, 2, QtWidgets.QTableWidgetItem(f"{tilt_x:+.1f}°"))
        self.calib_frames_table.setItem(row, 3, QtWidgets.QTableWidgetItem(f"{tilt_y:+.1f}°"))
        self.calib_frames_table.setItem(row, 4, QtWidgets.QTableWidgetItem(f"{distance:.2f} m"))
        self.calib_frames_table.setItem(row, 5, QtWidgets.QTableWidgetItem(sector_lbl))
        
        for col in range(6):
            item = self.calib_frames_table.item(row, col)
            if item:
                item.setTextAlignment(QtCore.Qt.AlignCenter)
                
        self.calib_frames_table.scrollToBottom()
        
        # Update valid poses text
        target = self.spin_target.value()
        self.lbl_calib_valid.setText(f"Valid Poses Captured: {frame_idx} / {target}")
        if frame_idx >= target:
            self.lbl_calib_valid.setStyleSheet("color: #2ea043; font-size: 12px; font-weight: bold;")
        else:
            self.lbl_calib_valid.setStyleSheet("color: #c9d1d9; font-size: 12px; font-weight: bold;")
            
        # Update lens coverage grid
        self.coverage_grid.set_cell_active(sector_r, sector_c, True)

    def on_calib_frame_rejected(self, reason):
        QtWidgets.QMessageBox.warning(self, "Capture Rejected", reason)
        self.status_bar.showMessage(f"Capture rejected: {reason}", 4000)

    def on_calib_success(self, reproj_error, camera_matrix, dist_coeffs):
        self.status_bar.showMessage(f"Calibration successful! Error: {reproj_error:.4f} px", 5000)
        QtWidgets.QMessageBox.information(
            self, "Calibration Complete", 
            f"Intrinsic calibration computed successfully!\n\n"
            f"Reprojection Error: {reproj_error:.4f} pixels."
        )
        
        self.lbl_reproj_error.setText(f"Reprojection Error: {reproj_error:.3f} px")
        if reproj_error < 0.3:
            self.lbl_reproj_error.setStyleSheet("color: #2ea043; font-size: 22px; font-weight: bold;")
        elif reproj_error <= 0.7:
            self.lbl_reproj_error.setStyleSheet("color: #ffaa00; font-size: 22px; font-weight: bold;")
        else:
            self.lbl_reproj_error.setStyleSheet("color: #f85149; font-size: 22px; font-weight: bold;")
            
        fx = camera_matrix[0, 0]
        fy = camera_matrix[1, 1]
        cx = camera_matrix[0, 2]
        cy = camera_matrix[1, 2]
        k1, k2, p1, p2, k3 = dist_coeffs.ravel()[:5]
        
        results_str = (
            f"Camera Matrix (Intrinsics):\n"
            f"  fx = {fx:.3f} px\n"
            f"  fy = {fy:.3f} px\n"
            f"  cx = {cx:.3f} px\n"
            f"  cy = {cy:.3f} px\n\n"
            f"Distortion Coefficients:\n"
            f"  k1 = {k1:+.6f}\n"
            f"  k2 = {k2:+.6f}\n"
            f"  p1 = {p1:+.6f}\n"
            f"  p2 = {p2:+.6f}\n"
            f"  k3 = {k3:+.6f}"
        )
        self.calib_results_text.setText(results_str)

    def on_calib_error(self, err_msg):
        QtWidgets.QMessageBox.critical(self, "Calibration Error", err_msg)
        self.status_bar.showMessage(f"Calibration failed: {err_msg}", 5000)

    @QtCore.Slot()
    def on_add_distance_spec(self):
        desc = self.txt_dist_desc.text().strip()
        
        # Point A name construction
        type_a = self.cmb_point_a_type.currentText()
        if type_a == "Marker ID":
            pt_a = f"Marker {self.spin_point_a_id.value()}"
        else:
            pt_a = type_a
            
        # Point B name construction
        type_b = self.cmb_point_b_type.currentText()
        if type_b == "Marker ID":
            pt_b = f"Marker {self.spin_point_b_id.value()}"
        else:
            pt_b = type_b
            
        if not desc:
            desc = f"Dist {pt_a} to {pt_b}"
            
        # Avoid duplicate description
        desc_exists = any(spec["desc"] == desc for spec in self.distance_specifications)
        if desc_exists:
            desc = f"{desc} ({len(self.distance_specifications)+1})"
            
        spec = {
            "desc": desc,
            "point_a": pt_a,
            "point_b": pt_b
        }
        self.distance_specifications.append(spec)
        self.save_persistent_distances()
        self.txt_dist_desc.clear()
        self.status_bar.showMessage(f"Added distance measurement: {desc}", 3000)

    @QtCore.Slot()
    def on_delete_distance_spec(self):
        selected_ranges = self.tbl_aruco_distances.selectedRanges()
        if not selected_ranges:
            self.status_bar.showMessage("Please select a row in the Distance Table to delete.", 4000)
            return
            
        # Collect rows to delete
        rows_to_delete = []
        for r in selected_ranges:
            for row in range(r.topRow(), r.bottomRow() + 1):
                if row not in rows_to_delete:
                    rows_to_delete.append(row)
                    
        # Sort in reverse to delete correctly
        rows_to_delete.sort(reverse=True)
        for row in rows_to_delete:
            if 0 <= row < len(self.distance_specifications):
                desc = self.distance_specifications[row]["desc"]
                self.distance_specifications.pop(row)
                self.status_bar.showMessage(f"Deleted distance measurement: {desc}", 3000)
                
        self.save_persistent_distances()

    @QtCore.Slot(QtWidgets.QTableWidgetItem)
    def on_distance_item_changed(self, item):
        # Only handle edits to the description column (column 0)
        if item.column() == 0:
            row = item.row()
            if 0 <= row < len(self.distance_specifications):
                new_desc = item.text().strip()
                if new_desc:
                    self.distance_specifications[row]["desc"] = new_desc
                    self.save_persistent_distances()

    def load_persistent_distances(self):
        settings = QtCore.QSettings("Antigravity", "RealSenseViewerTracker")
        import json
        specs_json = settings.value("distance_specs", "[]")
        try:
            self.distance_specifications = json.loads(specs_json)
        except Exception:
            self.distance_specifications = []

    def save_persistent_distances(self):
        settings = QtCore.QSettings("Antigravity", "RealSenseViewerTracker")
        import json
        settings.setValue("distance_specs", json.dumps(self.distance_specifications))

    @QtCore.Slot()
    def on_save_coords_snapshot(self):
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Coordinates Snapshot", "coordinates_snapshot.txt", "Text Files (*.txt);;CSV Files (*.csv);;All Files (*)"
        )
        if not file_path:
            return
            
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("Intel RealSense ArUco Coordinates Snapshot\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                ref_lbl = f"Relative (Marker ID {self.worker.aruco_ref_id})" if self.worker.aruco_ref_enabled else "Camera (Absolute)"
                f.write(f"Coordinate Origin Reference: {ref_lbl}\n")
                f.write("="*60 + "\n\n")
                
                f.write("--- DETECTED MARKERS ---\n")
                f.write(f"{'Marker ID':<12} | {'X (m)':<10} | {'Y (m)':<10} | {'Z (m)':<10} | {'Distance (m)':<12}\n")
                f.write("-"*60 + "\n")
                
                for row in range(self.tbl_aruco_detections.rowCount()):
                    m_id = self.tbl_aruco_detections.item(row, 0).text() if self.tbl_aruco_detections.item(row, 0) else ""
                    x = self.tbl_aruco_detections.item(row, 1).text() if self.tbl_aruco_detections.item(row, 1) else ""
                    y = self.tbl_aruco_detections.item(row, 2).text() if self.tbl_aruco_detections.item(row, 2) else ""
                    z = self.tbl_aruco_detections.item(row, 3).text() if self.tbl_aruco_detections.item(row, 3) else ""
                    dist = self.tbl_aruco_detections.item(row, 4).text() if self.tbl_aruco_detections.item(row, 4) else ""
                    f.write(f"{m_id:<12} | {x:<10} | {y:<10} | {z:<10} | {dist:<12}\n")
                    
                f.write("\n--- DISTANCE MEASUREMENTS ---\n")
                f.write(f"{'Description':<25} | {'Point A':<10} | {'Point B':<10} | {'Distance (m)':<12} | {'Status':<15}\n")
                f.write("-"*78 + "\n")
                
                for row in range(self.tbl_aruco_distances.rowCount()):
                    desc = self.tbl_aruco_distances.item(row, 0).text() if self.tbl_aruco_distances.item(row, 0) else ""
                    pt_a = self.tbl_aruco_distances.item(row, 1).text() if self.tbl_aruco_distances.item(row, 1) else ""
                    pt_b = self.tbl_aruco_distances.item(row, 2).text() if self.tbl_aruco_distances.item(row, 2) else ""
                    dist = self.tbl_aruco_distances.item(row, 3).text() if self.tbl_aruco_distances.item(row, 3) else ""
                    status = self.tbl_aruco_distances.item(row, 4).text() if self.tbl_aruco_distances.item(row, 4) else ""
                    f.write(f"{desc:<25} | {pt_a:<10} | {pt_b:<10} | {dist:<12} | {status:<15}\n")
                    
            self.status_bar.showMessage(f"Snapshot saved to: {os.path.basename(file_path)}", 5000)
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Save Snapshot Failed", f"Failed to save snapshot: {e}")

    @QtCore.Slot(bool)
    def on_toggle_logging(self, checked):
        if checked:
            file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
                self, "Save Coordinates Log CSV", "coordinates_log.csv", "CSV Files (*.csv)"
            )
            if not file_path:
                self.btn_log_coords.setChecked(False)
                return
                
            try:
                self.log_file = open(file_path, "w", newline="", encoding="utf-8")
                import csv
                self.log_writer = csv.writer(self.log_file)
                self.log_writer.writerow([
                    "Timestamp", 
                    "Elapsed_Seconds", 
                    "Frame_Number", 
                    "Coordinate_Reference", 
                    "Type", 
                    "Name_or_Description", 
                    "X_or_PointA", 
                    "Y_or_PointB", 
                    "Z_or_Status", 
                    "Value"
                ])
                self.log_start_time = time.time()
                self.log_frame_count = 0
                self.btn_log_coords.setText("🛑 Stop Logging")
                self.status_bar.showMessage(f"Logging coordinates to: {os.path.basename(file_path)}")
            except Exception as e:
                self.btn_log_coords.setChecked(False)
                QtWidgets.QMessageBox.warning(self, "Logging Failed", f"Failed to start logger: {e}")
        else:
            if self.log_file:
                try:
                    self.log_file.close()
                except Exception:
                    pass
                self.log_file = None
                self.log_writer = None
                self.btn_log_coords.setText("📝 Start Logging")
                self.status_bar.showMessage("Coordinates logging stopped.", 4000)

    @QtCore.Slot()
    def on_calibrate_world_origin(self):
        if hasattr(self, 'last_ref_rvec') and self.last_ref_rvec is not None and self.last_ref_tvec is not None:
            settings = QtCore.QSettings("Antigravity", "RealSenseViewerTracker")
            import json
            settings.setValue("static_world_rvec", json.dumps(self.last_ref_rvec))
            settings.setValue("static_world_tvec", json.dumps(self.last_ref_tvec))
            
            self.worker.update_static_ref(self.last_ref_rvec, self.last_ref_tvec)
            self.lbl_world_calib_status.setText("Status: Calibrated (Locked)")
            self.lbl_world_calib_status.setStyleSheet("color: #2ea043; font-weight: bold; font-size: 10px; margin-top: 2px;")
            
            # Switch view to static world
            self.cmb_ref_mode.setCurrentIndex(2)
            
            x = self.last_ref_tvec[0][0]
            y = self.last_ref_tvec[1][0]
            z = self.last_ref_tvec[2][0]
            
            QtWidgets.QMessageBox.information(
                self, "World Sense Calibrated",
                f"Camera static pose successfully calibrated relative to origin marker!\n\n"
                f"Locked Translation:\n"
                f"  X = {x:+.3f} m\n"
                f"  Y = {y:+.3f} m\n"
                f"  Z = {z:+.3f} m\n\n"
                f"Reference coordinate frame switched to Static World."
            )
        else:
            QtWidgets.QMessageBox.warning(
                self, "Calibration Failed",
                "Reference marker is not currently visible.\n"
                "Please make sure:\n"
                "1. Target mode is set to 'ArUco Marker'.\n"
                "2. Reference mode is set to 'Live Marker'.\n"
                "3. The origin marker (with correct Origin Marker ID) is in the camera's view."
            )

    @QtCore.Slot()
    def on_clear_world_calibration(self):
        settings = QtCore.QSettings("Antigravity", "RealSenseViewerTracker")
        settings.remove("static_world_rvec")
        settings.remove("static_world_tvec")
        
        self.worker.update_static_ref(None, None)
        self.lbl_world_calib_status.setText("Status: Not Calibrated")
        self.lbl_world_calib_status.setStyleSheet("color: #8b949e; font-size: 10px; font-style: italic; margin-top: 2px;")
        
        if self.cmb_ref_mode.currentIndex() == 2:
            self.cmb_ref_mode.setCurrentIndex(0) # Switch to camera absolute
            
        self.status_bar.showMessage("Static World Calibration cleared.", 4000)

    def load_persistent_world_calibration(self):
        settings = QtCore.QSettings("Antigravity", "RealSenseViewerTracker")
        import json
        rvec_json = settings.value("static_world_rvec", None)
        tvec_json = settings.value("static_world_tvec", None)
        if rvec_json and tvec_json:
            try:
                rvec = json.loads(rvec_json)
                tvec = json.loads(tvec_json)
                self.worker.update_static_ref(rvec, tvec)
                self.lbl_world_calib_status.setText("Status: Calibrated (Locked)")
                self.lbl_world_calib_status.setStyleSheet("color: #2ea043; font-weight: bold; font-size: 10px; margin-top: 2px;")
            except Exception:
                self.worker.update_static_ref(None, None)
                self.lbl_world_calib_status.setText("Status: Not Calibrated")
                self.lbl_world_calib_status.setStyleSheet("color: #8b949e; font-size: 10px; font-style: italic; margin-top: 2px;")
        else:
            self.worker.update_static_ref(None, None)
            self.lbl_world_calib_status.setText("Status: Not Calibrated")
            self.lbl_world_calib_status.setStyleSheet("color: #8b949e; font-size: 10px; font-style: italic; margin-top: 2px;")

    def refresh_robot_ports(self):
        current_port = self.cmb_robot_port.currentText()
        self.cmb_robot_port.clear()
        ports = RobotCommunicator.get_available_ports()
        self.cmb_robot_port.addItems(ports)
        if current_port in ports:
            self.cmb_robot_port.setCurrentText(current_port)
        else:
            self.cmb_robot_port.setCurrentIndex(0)

    @QtCore.Slot()
    def on_robot_connect_clicked(self):
        if self.robot_comm.is_connected() and self.robot_comm.port != "Mock/Simulated":
            self.robot_comm.disconnect()
            self.btn_robot_connect.setText("⚡ Connect Robot")
            self.lbl_robot_status.setText("Status: Disconnected")
            self.lbl_robot_status.setStyleSheet("color: #8b949e; font-size: 10px; font-style: italic;")
            self.status_bar.showMessage("Robot disconnected.", 3000)
        else:
            port = self.cmb_robot_port.currentText()
            baud = int(self.cmb_robot_baud.currentText())
            protocol = self.cmb_robot_protocol.currentText()
            
            self.robot_comm.port = port
            self.robot_comm.baudrate = baud
            self.robot_comm.protocol = protocol
            
            success, msg = self.robot_comm.connect()
            if success:
                self.btn_robot_connect.setText("🔌 Disconnect Robot" if port != "Mock/Simulated" else "⚡ Reset Connection")
                self.lbl_robot_status.setText(f"Status: Connected ({port})")
                self.lbl_robot_status.setStyleSheet("color: #2ea043; font-weight: bold; font-size: 10px;")
                self.status_bar.showMessage(msg, 4000)
            else:
                self.lbl_robot_status.setText("Status: Connection Failed")
                self.lbl_robot_status.setStyleSheet("color: #f85149; font-weight: bold; font-size: 10px;")
                QtWidgets.QMessageBox.warning(self, "Robot Connection", f"Failed to connect: {msg}")

    @QtCore.Slot()
    def on_filter_settings_changed(self):
        f_type = self.cmb_filter_type.currentText().lower()
        if f_type == "none":
            self.coord_filter.set_filter_type("none")
            self.sld_filter_smoothing.setEnabled(False)
        elif f_type == "moving average":
            self.coord_filter.set_filter_type("moving_average")
            self.sld_filter_smoothing.setEnabled(True)
            self.sld_filter_smoothing.name_label.setText("Window Size")
            self.sld_filter_smoothing.slider.setRange(1, 30)
            self.coord_filter.set_ma_window(self.sld_filter_smoothing.value())
        elif f_type == "kalman filter":
            self.coord_filter.set_filter_type("kalman")
            self.sld_filter_smoothing.setEnabled(True)
            self.sld_filter_smoothing.name_label.setText("Measurement Noise")
            self.sld_filter_smoothing.slider.setRange(1, 100)
            r_val = self.sld_filter_smoothing.value() * 0.001
            self.coord_filter.set_kf_parameters(process_noise=1e-4, measurement_noise=r_val)

    def closeEvent(self, event):
        if hasattr(self, 'robot_comm'):
            self.robot_comm.disconnect()
        if hasattr(self, 'log_file') and self.log_file:
            try:
                self.log_file.close()
            except Exception:
                pass
        self.worker.running = False
        self.worker.wait()
        event.accept()


def main():
    app = QtWidgets.QApplication(sys.argv)
    # Set global application style for consistency
    app.setStyle("Fusion")
    
    # Set global dark palette for standard PyQt dialogs if any
    dark_palette = QtGui.QPalette()
    dark_palette.setColor(QtGui.QPalette.Window, QtGui.QColor("#0c1117"))
    dark_palette.setColor(QtGui.QPalette.WindowText, QtGui.QColor("#c9d1d9"))
    dark_palette.setColor(QtGui.QPalette.Base, QtGui.QColor("#161b22"))
    dark_palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor("#0c1117"))
    dark_palette.setColor(QtGui.QPalette.ToolTipBase, QtGui.QColor("#0c1117"))
    dark_palette.setColor(QtGui.QPalette.ToolTipText, QtGui.QColor("#c9d1d9"))
    dark_palette.setColor(QtGui.QPalette.Text, QtGui.QColor("#c9d1d9"))
    dark_palette.setColor(QtGui.QPalette.Button, QtGui.QColor("#21262d"))
    dark_palette.setColor(QtGui.QPalette.ButtonText, QtGui.QColor("#c9d1d9"))
    dark_palette.setColor(QtGui.QPalette.BrightText, QtGui.QColor("#58a6ff"))
    dark_palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor("#58a6ff"))
    dark_palette.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor("#0c1117"))
    app.setPalette(dark_palette)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
