#!/usr/bin/env python3
"""
Standalone execution and tuning script for the Intel RealSense D415 Vision System.
Author: Senior Robotics and Computer Vision Engineer
"""

import os
import sys
import time
import json
import numpy as np
import cv2

# Add src to python path for ease of import
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from modules.perception.realsense_vision import RealSenseVisionSystem

# Default HSV tuning values (targets a green ball on a red plate)
DEFAULT_HSV = {
    "h_low": 35,
    "s_low": 40,
    "v_low": 40,
    "h_high": 85,
    "s_high": 255,
    "v_high": 255
}

def nothing(x):
    """Empty callback for OpenCV trackbars."""
    pass

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
        # simulates depth distance in meters
        return self.base_depth_m + np.random.normal(0, 0.001)

def run_vision_system():
    print("====================================================")
    print("      OSRS ROBOTICS REALSENSE D415 VISION SYSTEM     ")
    print("====================================================")
    
    # 1. Initialize vision system
    vision_system = RealSenseVisionSystem(center_threshold=0.15)
    
    # 2. Try initializing physical camera
    camera_active = vision_system.initialize_camera(width=1280, height=720, fps=30)
    
    mock_mode = not camera_active
    mock_depth = None
    if mock_mode:
        print("[!] Intel RealSense D415 not found or failed to initialize.")
        print("[+] Starting in MOCK SIMULATION MODE.")
        print("    (Generating synthetic plate and ball target...)")
        mock_depth = MockDepthFrame(1280, 720)
    else:
        print("[+] RealSense camera successfully initialized.")
        
    # 3. Create CV2 tuning windows
    window_name = "RealSense Vision System"
    trackbar_window = "HSV Tuning Controls"
    cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)
    cv2.namedWindow(trackbar_window, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(trackbar_window, 400, 300)
    
    # Create Trackbars
    cv2.createTrackbar("Low H", trackbar_window, DEFAULT_HSV["h_low"], 180, nothing)
    cv2.createTrackbar("High H", trackbar_window, DEFAULT_HSV["h_high"], 180, nothing)
    cv2.createTrackbar("Low S", trackbar_window, DEFAULT_HSV["s_low"], 255, nothing)
    cv2.createTrackbar("High S", trackbar_window, DEFAULT_HSV["s_high"], 255, nothing)
    cv2.createTrackbar("Low V", trackbar_window, DEFAULT_HSV["v_low"], 255, nothing)
    cv2.createTrackbar("High V", trackbar_window, DEFAULT_HSV["v_high"], 255, nothing)
    
    # Simulation variables for mock mode
    sim_time = 0.0
    ball_pos_factor = 0.0  # -1.0 to 1.0
    direction = 1
    
    print("\nPress 'q' or 'ESC' in the frame window to exit.")
    print("HSV parameters can be tuned in real-time in the 'HSV Tuning Controls' window.\n")
    
    last_print_time = time.time()
    frame_count = 0
    fps = 30.0
    
    try:
        while True:
            loop_start = time.time()
            
            # Read current trackbar values
            hsv_bounds = {
                "h_low": cv2.getTrackbarPos("Low H", trackbar_window),
                "h_high": cv2.getTrackbarPos("High H", trackbar_window),
                "s_low": cv2.getTrackbarPos("Low S", trackbar_window),
                "s_high": cv2.getTrackbarPos("High S", trackbar_window),
                "v_low": cv2.getTrackbarPos("Low V", trackbar_window),
                "v_high": cv2.getTrackbarPos("High V", trackbar_window)
            }
            
            color_image = None
            depth_frame = None
            
            if not mock_mode:
                # Retrieve frames from RealSense pipeline
                frames = vision_system.pipeline.wait_for_frames()
                aligned_frames = vision_system.align.process(frames)
                
                color_frame = aligned_frames.get_color_frame()
                depth_frame = aligned_frames.get_depth_frame()
                
                if not color_frame or not depth_frame:
                    continue
                    
                color_image = np.asanyarray(color_frame.get_data())
            else:
                # --- MOCK SIMULATION MODE ---
                # Create a black frame
                width, height = 1280, 720
                color_image = np.zeros((height, width, 3), dtype=np.uint8) + 40 # Grey background
                
                # Draw mock plate bounds (Green Line) between left (0) and right (1) markers
                # Marker 0 (left): center at scaled pt0
                # Marker 1 (right): center at scaled pt1
                pt0 = (int(width * 0.23), int(height * 0.5))
                pt1 = (int(width * 0.77), int(height * 0.5))
                
                # Draw simulated ArUco markers (white squares with black inner square)
                cv2.rectangle(color_image, (pt0[0]-25, pt0[1]-25), (pt0[0]+25, pt0[1]+25), (255, 255, 255), -1)
                cv2.rectangle(color_image, (pt0[0]-15, pt0[1]-15), (pt0[0]+15, pt0[1]+15), (0, 0, 0), -1)
                # Text ID 0
                cv2.putText(color_image, "0", (pt0[0]-5, pt0[1]+5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                
                cv2.rectangle(color_image, (pt1[0]-25, pt1[1]-25), (pt1[0]+25, pt1[1]+25), (255, 255, 255), -1)
                cv2.rectangle(color_image, (pt1[0]-15, pt1[1]-15), (pt1[0]+15, pt1[1]+15), (0, 0, 0), -1)
                # Text ID 1
                cv2.putText(color_image, "1", (pt1[0]-5, pt1[1]+5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                
                # Draw a thick red plate suspended between the markers (BGR: 50, 50, 220)
                cv2.rectangle(color_image, (pt0[0]+25, pt0[1]-6), (pt1[0]-25, pt1[1]+6), (50, 50, 220), -1)
                
                # Draw plate axis
                cv2.line(color_image, pt0, pt1, (80, 80, 80), 1)
                
                # Simulate ball rolling back and forth (sine wave simulation)
                sim_time += 0.03
                ball_pos_factor = np.sin(sim_time)
                
                # Compute ball center pixel coordinate
                plate_center_x = (pt0[0] + pt1[0]) / 2.0
                plate_half_width = (pt1[0] - pt0[0]) / 2.0
                
                # Offset in pixels along axis
                ball_x = int(plate_center_x + ball_pos_factor * plate_half_width * 0.7)
                ball_y = int(height * 0.5) # stable vertical center
                
                # Draw a green ball on the plate (BGR: 0, 200, 0)
                ball_radius = int(18 * height / 480)
                cv2.circle(color_image, (ball_x, ball_y), ball_radius, (0, 200, 0), -1)
                
                # Set mock depth frame
                depth_frame = mock_depth
                
                # Provide mock intrinsics for deprojection
                if vision_system.intrinsics is None:
                    # Creating a dummy struct that mirrors rs2_intrinsics
                    class MockIntrinsics:
                        def __init__(self):
                            self.width = 1280
                            self.height = 720
                            self.ppx = 640.0
                            self.ppy = 360.0
                            self.fx = 900.0
                            self.fy = 900.0
                            self.model = None
                            self.coeffs = [0.0, 0.0, 0.0, 0.0, 0.0]
                    
                    mock_intr = MockIntrinsics()
                    mock_intr.width = width
                    mock_intr.height = height
                    mock_intr.ppx = width / 2.0
                    mock_intr.ppy = height / 2.0
                    mock_intr.fx = width * 615.0 / 640.0
                    mock_intr.fy = height * 615.0 / 480.0
                    vision_system.intrinsics = mock_intr
                    
                    # Define deprojection function if mock pyrealsense2 is missing
                    if rs is None:
                        class MockRS:
                            @staticmethod
                            def rs2_deproject_pixel_to_point(intrinsics, pixel, depth):
                                # Simple pinhole model deprojection
                                x = (pixel[0] - intrinsics.ppx) * depth / intrinsics.fx
                                y = (pixel[1] - intrinsics.ppy) * depth / intrinsics.fy
                                z = depth
                                return [x, y, z]
                        sys.modules['pyrealsense2'] = MockRS
                        globals()['rs'] = MockRS
            
            # 4. Run perception step
            api_data, annotated_image = vision_system.run_step(color_image, depth_frame, hsv_bounds)
            
            # Print API dictionary output periodically
            now = time.time()
            if now - last_print_time >= 0.5:
                print(f"[API OUTPUT] (FPS: {fps:.1f})")
                print(json.dumps(api_data, indent=2))
                print("-" * 50)
                last_print_time = now
                
            # Show display windows
            cv2.imshow(window_name, annotated_image)
            
            # Check key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:  # 'q' or ESC
                break
                
            # Sleep to match target FPS (30 FPS -> ~33ms loop duration)
            elapsed = time.time() - loop_start
            sleep_time = max(0.001, (1.0 / 30.0) - elapsed)
            time.sleep(sleep_time)
            
            # FPS Calculation
            frame_count += 1
            loop_end = time.time()
            actual_fps = 1.0 / (loop_end - loop_start)
            fps = 0.9 * fps + 0.1 * actual_fps
            
    except KeyboardInterrupt:
        print("\nStopping vision system...")
        
    finally:
        # Cleanup
        vision_system.stop()
        print("Vision system shut down successfully.")

if __name__ == "__main__":
    run_vision_system()
