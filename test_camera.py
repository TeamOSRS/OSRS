import cv2
import sys

def scan_cameras():
    print("====================================================")
    print("         WEBCAM INDEX DIAGNOSTIC UTILITY            ")
    print("====================================================")
    print("Scanning indices 0 to 5 using default and DirectShow backends...\n")
    
    working_cameras = []
    
    # Test common indices
    for index in range(6):
        # 1. Test Default Backend
        print(f"Testing index {index} (Default backend)... ", end="", flush=True)
        cap = cv2.VideoCapture(index)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                h, w = frame.shape[:2]
                print(f"SUCCESS! Frame Captured: {w}x{h}")
                working_cameras.append((index, "Default", (w, h)))
            else:
                print("Opened, but failed to read frame.")
            cap.release()
        else:
            print("Failed")
            
        # 2. Test DirectShow (CAP_DSHOW) Backend (Often required/more stable on Windows)
        print(f"Testing index {index} (DirectShow backend)... ", end="", flush=True)
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                h, w = frame.shape[:2]
                print(f"SUCCESS! Frame Captured: {w}x{h}")
                working_cameras.append((index, "DirectShow (cv2.CAP_DSHOW)", (w, h)))
            else:
                print("Opened, but failed to read frame.")
            cap.release()
        else:
            print("Failed")
            
    print("\n====================================================")
    if working_cameras:
        print("[+] WORKING CAMERA DETECTED:")
        for cam in working_cameras:
            print(f"  -> Index: {cam[0]} | Backend: {cam[1]} | Resolution: {cam[2]}")
        print("====================================================")
        print("\nSuggestions:")
        print("1. If the working camera is index 1 or 2, select that index in the GUI's 'Camera Configuration' dropdown, then click 'Open Webcam'.")
        print("2. If the camera only works with DirectShow backend, we will add cv2.CAP_DSHOW to our code.")
    else:
        print("[-] No working cameras found.")
        print("====================================================")
        print("\nTroubleshooting Checklists:")
        print("1. Verify your webcam is physically connected to the computer.")
        print("2. Check Windows Settings -> Privacy & security -> Camera, and verify 'Camera access' is turned ON.")
        print("3. Check if another program (Zoom, Teams, Skype, Browser, Discord, etc.) is currently using your webcam, which locks it from other processes.")

if __name__ == "__main__":
    scan_cameras()
