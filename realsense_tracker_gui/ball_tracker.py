# pyrefly: ignore [missing-import]
import cv2
import numpy as np

class BallTracker:
    def __init__(self, hsv_lower=None, hsv_upper=None):
        # Default green/yellow tennis ball HSV bounds
        self.hsv_lower = np.array([29, 86, 6]) if hsv_lower is None else hsv_lower
        self.hsv_upper = np.array([64, 255, 255]) if hsv_upper is None else hsv_upper

    def process_frame(self, color_image, hsv_lower=None, hsv_upper=None):
        """
        Detects the ball based on HSV thresholds.
        Returns:
            mask: Binary threshold mask
            center: (x, y) coordinates of the ball center, or None
            radius: Float radius of the tracked ball, or 0
        """
        lower = self.hsv_lower if hsv_lower is None else hsv_lower
        upper = self.hsv_upper if hsv_upper is None else hsv_upper
        
        # Convert color image to HSV space
        hsv = cv2.cvtColor(color_image, cv2.COLOR_BGR2HSV)
        
        # Threshold the HSV image to get only color bounds
        mask = cv2.inRange(hsv, lower, upper)
        
        # Perform morphological cleaning
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)
        
        # Find contours
        contours, _ = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        center = None
        radius = 0
        
        if len(contours) > 0:
            # Select the largest contour
            c = max(contours, key=cv2.contourArea)
            ((x, y), radius) = cv2.minEnclosingCircle(c)
            if radius > 10:  # Minimum radius threshold to filter out noise
                center = (int(x), int(y))
                
        return mask, center, radius

    def process_frame_centroid(self, color_image, hsv_lower=None, hsv_upper=None):
        """
        Detects an object based on HSV thresholds and returns its centroid and bounding box.
        Returns:
            mask: Binary threshold mask
            center: (x, y) centroid coordinates, or None
            bbox: (x, y, w, h) bounding box coordinates, or None
        """
        lower = self.hsv_lower if hsv_lower is None else hsv_lower
        upper = self.hsv_upper if hsv_upper is None else hsv_upper
        
        # Convert color image to HSV space
        hsv = cv2.cvtColor(color_image, cv2.COLOR_BGR2HSV)
        
        # Threshold the HSV image
        mask = cv2.inRange(hsv, lower, upper)
        
        # Perform morphological cleaning
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)
        
        # Find contours
        contours, _ = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        center = None
        bbox = None
        
        if len(contours) > 0:
            # Select the largest contour
            c = max(contours, key=cv2.contourArea)
            if cv2.contourArea(c) > 50:  # Minimum contour area to filter out noise (reduced from 200 for distance detection)
                M = cv2.moments(c)
                if M["m00"] > 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    center = (cx, cy)
                    bbox = cv2.boundingRect(c)
                    
        return mask, center, bbox

