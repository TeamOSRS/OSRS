# pyrefly: ignore [missing-import]
import pyrealsense2 as rs
import numpy as np
# pyrefly: ignore [missing-import]
import cv2

def main():
    print("=========================================")
    print("Intel RealSense SDK Test Script")
    try:
        version = rs.__version__
    except AttributeError:
        try:
            import importlib.metadata
            version = importlib.metadata.version("pyrealsense2")
        except Exception:
            version = "unknown"
    print(f"pyrealsense2 version: {version}")
    print("=========================================")

    # Create a context to manage devices
    try:
        context = rs.context()
        devices = context.query_devices()
        print(f"Detected {len(devices)} RealSense device(s).")
        
        if len(devices) == 0:
            print("\n[WARNING] No RealSense devices detected. Please make sure:")
            print("  1. The D435i camera is connected to a USB 3.0 port (typically blue).")
            print("  2. The drivers are installed correctly (run the SDK Installer).")
            print("  3. Windows Device Manager shows 'Intel RealSense Depth Camera SR300/D400'.")
            return

        for i, dev in enumerate(devices):
            print(f"\nDevice {i+1}:")
            print(f"  Name: {dev.get_info(rs.camera_info.name)}")
            print(f"  Serial Number: {dev.get_info(rs.camera_info.serial_number)}")
            print(f"  Firmware Version: {dev.get_info(rs.camera_info.firmware_version)}")
            print(f"  USB Type: {dev.get_info(rs.camera_info.usb_type_descriptor)}")

    except Exception as e:
        print(f"Error querying devices: {e}")
        return

    # Attempt to stream frames
    print("\nAttempting to stream depth and color frames...")
    try:
        pipeline = rs.pipeline()
        config = rs.config()

        # Enable both depth and color streams
        config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
        config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

        # Start streaming
        profile = pipeline.start(config)
        print("Pipeline started successfully! Press 'q' in the window to stop.")

        # Getting the depth sensor's depth scale
        depth_sensor = profile.get_device().first_depth_sensor()
        depth_scale = depth_sensor.get_depth_scale()
        print(f"Depth Scale is: {depth_scale}")

        try:
            while True:
                # Wait for a coherent pair of frames: depth and color
                frames = pipeline.wait_for_frames()
                depth_frame = frames.get_depth_frame()
                color_frame = frames.get_color_frame()
                if not depth_frame or not color_frame:
                    continue

                # Convert images to numpy arrays
                depth_image = np.asanyarray(depth_frame.get_data())
                color_image = np.asanyarray(color_frame.get_data())

                # Apply colormap on image; image must be converted to 8-bit per pixel first
                depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)

                # Stack both images horizontally
                images = np.hstack((color_image, depth_colormap))

                # Show images
                cv2.imshow('RealSense Stream (Color | Depth)', images)
                
                # Press 'q' or ESC to exit the stream loop
                key = cv2.waitKey(1)
                if key & 0xFF == ord('q') or key == 27:
                    break

        finally:
            # Stop streaming
            pipeline.stop()
            cv2.destroyAllWindows()
            print("Pipeline stopped.")

    except Exception as e:
        print(f"Error during streaming check: {e}")
        print("This could be because the camera is already in use by another app (e.g. RealSense Viewer),")
        print("or the camera connection is unstable.")

if __name__ == "__main__":
    main()
