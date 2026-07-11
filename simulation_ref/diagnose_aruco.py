"""
ArUco Marker Diagnostic Tool.
Scans the camera feed against all standard OpenCV ArUco dictionaries to detect IDs.
"""

import sys
import os
import cv2
import numpy as np

# List of all standard OpenCV ArUco dictionary IDs and names
ARUCO_DICTS = {
    "DICT_4X4_50": cv2.aruco.DICT_4X4_50,
    "DICT_4X4_100": cv2.aruco.DICT_4X4_100,
    "DICT_4X4_250": cv2.aruco.DICT_4X4_250,
    "DICT_4X4_1000": cv2.aruco.DICT_4X4_1000,
    "DICT_5X5_50": cv2.aruco.DICT_5X5_50,
    "DICT_5X5_100": cv2.aruco.DICT_5X5_100,
    "DICT_5X5_250": cv2.aruco.DICT_5X5_250,
    "DICT_5X5_1000": cv2.aruco.DICT_5X5_1000,
    "DICT_6X6_50": cv2.aruco.DICT_6X6_50,
    "DICT_6X6_100": cv2.aruco.DICT_6X6_100,
    "DICT_6X6_250": cv2.aruco.DICT_6X6_250,
    "DICT_6X6_1000": cv2.aruco.DICT_6X6_1000,
    "DICT_7X7_50": cv2.aruco.DICT_7X7_50,
    "DICT_7X7_100": cv2.aruco.DICT_7X7_100,
    "DICT_7X7_250": cv2.aruco.DICT_7X7_250,
    "DICT_7X7_1000": cv2.aruco.DICT_7X7_1000,
    "DICT_ARUCO_ORIGINAL": cv2.aruco.DICT_ARUCO_ORIGINAL,
}

def try_realsense():
    try:
        import pyrealsense2 as rs
        pipeline = rs.pipeline()
        config = rs.config()
        config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
        profile = pipeline.start(config)
        print("[DIAGNOSTIC] Successfully initialized Intel RealSense camera.")
        return pipeline, True
    except Exception as e:
        print(f"[DIAGNOSTIC] Intel RealSense init failed/not connected: {e}")
        return None, False

def main():
    print("=" * 80)
    print("                 ARUCO DICTIONARY DIAGNOSTIC TOOL")
    print("=" * 80)
    
    # 1. Try to open RealSense first
    pipeline, is_rs = try_realsense()
    cap = None
    
    if not is_rs:
        print("[DIAGNOSTIC] Falling back to standard webcam index 0...")
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("[DIAGNOSTIC] ERROR: No camera index available. Verify connection.")
            return

    print("[DIAGNOSTIC] Camera stream live. Show your printed markers to the lens.")
    print("[DIAGNOSTIC] Scanning frame for markers against all standard dictionaries...")
    
    try:
        for frame_idx in range(30):
            # Capture frame
            if is_rs:
                frames = pipeline.wait_for_frames(timeout_ms=1000)
                color_frame = frames.get_color_frame()
                if not color_frame:
                    continue
                frame = np.asanyarray(color_frame.get_data())
            else:
                ret, frame = cap.read()
                if not ret:
                    continue
            
            # Convert to gray
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            detections_found = []
            
            # Loop through all dictionaries
            for dict_name, dict_id in ARUCO_DICTS.items():
                try:
                    # Version-agnostic detector call
                    try:
                        aruco_dict = cv2.aruco.getPredefinedDictionary(dict_id)
                        aruco_params = cv2.aruco.DetectorParameters()
                        detector = cv2.aruco.ArucoDetector(aruco_dict, aruco_params)
                        corners, ids, rejected = detector.detectMarkers(gray)
                    except AttributeError:
                        aruco_dict = cv2.aruco.Dictionary_get(dict_id)
                        aruco_params = cv2.aruco.DetectorParameters_create()
                        corners, ids, rejected = cv2.aruco.detectMarkers(gray, aruco_dict, parameters=aruco_params)
                    
                    if ids is not None and len(ids) > 0:
                        detections_found.append((dict_name, ids.flatten().tolist()))
                except Exception as e:
                    pass
            
            if detections_found:
                print(f"\n[FRAME {frame_idx}] DETECTIONS FOUND:")
                for dict_name, ids in detections_found:
                    print(f"  ● Dictionary '{dict_name}' -> Detected IDs: {ids}")
                print("-" * 50)
            else:
                sys.stdout.write(".")
                sys.stdout.flush()
                
            cv2.waitKey(100)
            
    except KeyboardInterrupt:
        print("\n[DIAGNOSTIC] Stopped by user.")
    finally:
        if is_rs:
            pipeline.stop()
        if cap:
            cap.release()
            
    print("\n" + "=" * 80)
    print("                           SCANNING COMPLETE")
    print("=" * 80)
    print("Instructions:")
    print("1. If detections were found, verify which dictionary has BOTH IDs [0, 1].")
    print("2. If the printed markers are DICT_6X6_250 or another type, print markers from DICT_4X4_50 instead,")
    print("   or update realsense_vision.py constructor parameter (DICT_4X4_50) to match your dictionary.")
    print("=" * 80)

if __name__ == "__main__":
    main()
