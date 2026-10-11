#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import sys

class FrameGrabber(Node):
    def __init__(self):
        super().__init__('frame_grabber')
        self.bridge = CvBridge()
        self.sub = self.create_subscription(Image, '/top_camera/image_raw', self.image_cb, 10)
        self.get_logger().info("Waiting for image on /top_camera/image_raw...")

    def image_cb(self, msg):
        try:
            # Convert to BGR (OpenCV format)
            cv_img = self.bridge.imgmsg_to_cv2(msg, "bgr8")
            filename = "camera_frame.png"
            cv2.imwrite(filename, cv_img)
            self.get_logger().info(f"Successfully saved frame to {filename}!")
            sys.exit(0)
        except Exception as e:
            self.get_logger().error(f"Failed to save image: {e}")
            sys.exit(1)

def main():
    rclpy.init()
    node = FrameGrabber()
    try:
        rclpy.spin(node)
    except SystemExit:
        pass
    except KeyboardInterrupt:
        pass
    finally:
        rclpy.shutdown()

if __name__ == '__main__':
    main()
