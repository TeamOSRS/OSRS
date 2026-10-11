import cv2
import mediapipe as mp
import threading
import time
import logging
import urllib.request
import os
import base64
from typing import Optional

class HandTracker:
    """
    Captures video from a webcam and uses MediaPipe Tasks HandLandmarker
    to track hand landmarks in real time. Works on Python 3.13 without 
    requiring the legacy mp.solutions API.
    """
    def __init__(self, camera_index=0, max_hands=2, detection_confidence=0.7, tracking_confidence=0.7):
        self.camera_index = camera_index
        self.max_hands = max_hands
        self.detection_confidence = detection_confidence
        self.tracking_confidence = tracking_confidence
        
        # Thread control
        self.running = False
        self.thread = None
        self.lock = threading.Lock()
        
        # Capture and Frame states
        self.cap = None
        self.latest_frame = None
        self.latest_base64_frame = None
        self.latest_landmarks = None
        self.latest_world_landmarks = None
        self.fps = 0
        
        # Model path settings
        self.model_path = "hand_landmarker.task"
        self.landmarker = None

        # Custom Hand skeleton connection list
        self.HAND_CONNECTIONS = [
            (0, 1), (1, 2), (2, 3), (3, 4),      # Thumb
            (0, 5), (5, 6), (6, 7), (7, 8),      # Index
            (9, 10), (10, 11), (11, 12),         # Middle
            (13, 14), (14, 15), (15, 16),         # Ring
            (0, 17), (17, 18), (18, 19), (19, 20),# Pinky
            (5, 9), (9, 13), (13, 17)            # Palm joints
        ]

    def _ensure_model_exists(self):
        """Downloads the pre-trained hand landmarker task file if it's missing."""
        if not os.path.exists(self.model_path):
            logging.info(f"Model file '{self.model_path}' not found. Downloading from Google Storage (10.4 MB)...")
            url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
            try:
                urllib.request.urlretrieve(url, self.model_path)
                logging.info("[+] Model download complete!")
            except Exception as e:
                logging.error(f"[-] Failed to download model: {e}")
                return False
        return True

    def start(self):
        """Starts the camera capture and tracking thread."""
        if self.running:
            return True
            
        # Ensure the model task file is available
        if not self._ensure_model_exists():
            return False
            
        # Try to open the camera first (DirectShow CAP_DSHOW on Windows is more stable)
        self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            # Fallback to default backend
            self.cap = cv2.VideoCapture(self.camera_index)
            if not self.cap.isOpened():
                logging.error(f"Cannot open camera index {self.camera_index}")
                return False

        # Configure camera properties for lower latency
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        # Initialize the HandLandmarker using the Tasks API
        try:
            from mediapipe.tasks import python
            from mediapipe.tasks.python import vision

            base_options = python.BaseOptions(model_asset_path=self.model_path)
            options = vision.HandLandmarkerOptions(
                base_options=base_options,
                running_mode=vision.RunningMode.VIDEO,
                num_hands=self.max_hands,
                min_hand_detection_confidence=self.detection_confidence,
                min_hand_presence_confidence=self.tracking_confidence,
            )
            self.landmarker = vision.HandLandmarker.create_from_options(options)
        except Exception as e:
            logging.error(f"Failed to initialize MediaPipe Tasks HandLandmarker: {e}")
            if self.cap is not None:
                self.cap.release()
                self.cap = None
            return False

        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logging.info("HandTracker thread started using MediaPipe Tasks.")
        return True

    def stop(self):
        """Stops the camera capture and tracking thread."""
        self.running = False
        if self.thread is not None:
            self.thread.join(timeout=1.0)
            
        with self.lock:
            if self.cap is not None:
                self.cap.release()
                self.cap = None
            if self.landmarker is not None:
                self.landmarker.close()
                self.landmarker = None
                
        logging.info("HandTracker thread stopped.")

    def _run_loop(self):
        prev_time = time.time()
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                time.sleep(0.01)
                continue
                
            # Flip image horizontally for natural mirroring
            frame = cv2.flip(frame, 1)
            
            # Convert to RGB for MediaPipe processing
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Convert to MediaPipe Image object
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
            
            # Process landmarks (timestamp must be strictly increasing)
            timestamp_ms = int(time.time() * 1000)
            result = self.landmarker.detect_for_video(mp_image, timestamp_ms)
            
            # Draw overlay on annotated image
            frame_annotated = frame_rgb.copy()
            latest_lms_result = None
            latest_world_result = None
            
            if result and result.hand_landmarks:
                all_hands_data = []
                h, w = frame_rgb.shape[:2]
                
                for hand_idx in range(len(result.hand_landmarks)):
                    hand_lms = result.hand_landmarks[hand_idx]
                    hand_world_lms = result.hand_world_landmarks[hand_idx]
                    
                    # Extract handedness safely
                    handedness = "Right"
                    if result.handedness and hand_idx < len(result.handedness):
                        h_obj = result.handedness[hand_idx]
                        if hasattr(h_obj, 'classifications'):
                            handedness = h_obj.classifications[0].label
                        elif hasattr(h_obj, 'categories'):
                            handedness = h_obj.categories[0].category_name
                        else:
                            try:
                                handedness = h_obj[0].category_name
                            except:
                                handedness = "Right"
                                
                    all_hands_data.append({
                        "landmarks": hand_lms,
                        "world_landmarks": hand_world_lms,
                        "handedness": handedness
                    })
                    
                    # Draw connections (skeleton lines)
                    for conn in self.HAND_CONNECTIONS:
                        pt1 = hand_lms[conn[0]]
                        pt2 = hand_lms[conn[1]]
                        x1, y1 = int(pt1.x * w), int(pt1.y * h)
                        x2, y2 = int(pt2.x * w), int(pt2.y * h)
                        cv2.line(frame_annotated, (x1, y1), (x2, y2), (200, 200, 200), 2)
                    
                    # Draw landmark points
                    for lm in hand_lms:
                        x, y = int(lm.x * w), int(lm.y * h)
                        cv2.circle(frame_annotated, (x, y), 6, (0, 100, 0), 1)
                        cv2.circle(frame_annotated, (x, y), 5, (0, 255, 0), -1)
                        
                latest_lms_result = all_hands_data
                latest_world_result = [h["world_landmarks"] for h in all_hands_data]

            # Calculate FPS
            curr_time = time.time()
            dt = curr_time - prev_time
            prev_time = curr_time
            if dt > 0:
                calculated_fps = 1.0 / dt
                self.fps = 0.9 * self.fps + 0.1 * calculated_fps

            # Pre-compress and base64-encode the frame in background thread to optimize main async loop
            base64_encoded = None
            if frame_annotated is not None:
                try:
                    h, w = frame_annotated.shape[:2]
                    scale = 640.0 / w
                    resized = cv2.resize(frame_annotated, (640, int(h * scale)))
                    # cv2.imencode expects BGR, so convert color space from RGB to BGR
                    resized_bgr = cv2.cvtColor(resized, cv2.COLOR_RGB2BGR)
                    ret, buffer = cv2.imencode('.jpg', resized_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
                    if ret:
                        base64_encoded = base64.b64encode(buffer).decode('utf-8')
                except Exception as e:
                    logging.error(f"Failed to encode background frame: {e}")

            # Thread-safe update of latest outputs
            with self.lock:
                self.latest_frame = frame_annotated
                self.latest_base64_frame = base64_encoded
                self.latest_landmarks = latest_lms_result
                self.latest_world_landmarks = latest_world_result

    def get_latest_data(self):
        """Returns the latest frame, raw landmarks, and world landmarks."""
        with self.lock:
            return self.latest_frame, self.latest_landmarks, self.latest_world_landmarks, self.fps

    def get_latest_base64_frame(self) -> Optional[str]:
        """Returns the pre-encoded base64 JPEG string of the latest frame."""
        with self.lock:
            return self.latest_base64_frame
            
    def is_camera_active(self):
        return self.cap is not None and self.cap.isOpened()
