import sys
import os
import traceback

print("Python version:", sys.version)

model_path = "hand_landmarker.task"
if not os.path.exists(model_path):
    print("[-] Model file hand_landmarker.task not found in current directory.")
    sys.exit(1)
else:
    print("[+] Found model file hand_landmarker.task (size:", os.path.getsize(model_path), "bytes)")

try:
    import mediapipe as mp
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision
    print("[+] MediaPipe Tasks modules imported successfully!")
except ImportError as e:
    print("[-] MediaPipe Tasks import failed:", e)
    sys.exit(1)

try:
    print("[*] Initializing MediaPipe Tasks HandLandmarker...")
    base_options = python.BaseOptions(model_asset_path=model_path)
    
    # We test with different combinations of parameters to see which one succeeds
    options = vision.HandLandmarkerOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.VIDEO,
        num_hands=1,
        min_hand_detection_confidence=0.5,
        min_hand_presence_confidence=0.5,
        min_tracking_confidence=0.5
    )
    
    print("[*] Creating landmarker from options...")
    landmarker = vision.HandLandmarker.create_from_options(options)
    print("[+] MediaPipe Tasks HandLandmarker initialized successfully!")
    landmarker.close()
except Exception as e:
    print("[-] MediaPipe Tasks HandLandmarker initialization failed:")
    traceback.print_exc()
