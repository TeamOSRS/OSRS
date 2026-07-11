# OSRS Robotics: Intel RealSense D415 Vision System Manual

This document details the configuration, calibration, tuning, and architecture of the real-time computer vision system built for the humanoid robot's plate-balancing task.

---

## 1. Installation Commands

To run this vision system, install the required python packages on your host machine.

### Python Packages
```bash
pip install numpy opencv-python pyrealsense2
```

> [!NOTE]
> - **Platform Compatibility**: The `pyrealsense2` library is supported on Windows and Linux (Ubuntu 18.04/20.04/22.04) on x86_64 architectures.
> - **OpenCV Version**: The codebase is designed to support both modern (OpenCV 4.7+) and legacy versions of the OpenCV ArUco module automatically.

---

## 2. Intel RealSense D415 Calibration & Configuration

Since the D415 utilizes stereoscopic infrared sensors alongside a separate RGB camera sensor, spatial calibration and alignment are critical for accurate 3D coordinate deprojection.

### Optical Alignment
- **Hardware Offset**: The RGB sensor and depth sensor are physically separated on the camera bezel. 
- **Software Alignment**: To map depth readings directly onto RGB pixels, the system uses the `rs.align(rs.stream.color)` processing block. This projects the depth frame's viewport to match the color frame's focal center and field of view (FOV).
- **Intrinsics Retrieval**: The system dynamically extracts the camera focal length ($f_x, f_y$), principal point ($p_{px}, p_{py}$), and distortion coefficients directly from the active color stream profile.

### Calibration Procedure
If coordinate projection errors occur or depth reads as `0.0` continuously:
1. Download and run the **Intel RealSense Viewer** or the **Intel RealSense Dynamic Calibration Tool**.
2. Mount the camera securely on the robot's head mount.
3. Aim the camera at a flat, highly textured target (or the official Intel calibration target).
4. Run the calibration wizard to update the camera's internal EEPROM calibration parameters.

---

## 3. Real-Time HSV Tuning Instructions

The ball detection relies on color segmentation in the HSV (Hue, Saturation, Value) space. To adapt to varying lighting conditions and different ball colors, follow this tuning procedure:

1. Connect the Intel RealSense camera and execute the tuning utility:
   ```bash
   python run_realsense_vision.py
   ```
   *(If no camera is connected, the script will launch in **Mock Simulation Mode** to demonstrate functionality).*

2. Place the ball on the plate between the two ArUco markers.
3. Two GUI windows will open:
   - **RealSense Vision System**: The live RGB camera stream showing annotations.
   - **HSV Tuning Controls**: Sliders to set lower and upper thresholds.
4. **Tune Hue (H)**: Set `Low H` and `High H` to enclose the target ball color.
   - *Red Ball*: Red color wraps around the HSV boundary. The default configuration uses $H \in [0, 10]$. If your ball is dark red, try $H \in [170, 180]$ or adjust sliders to isolate it.
5. **Tune Saturation (S)**: Raise `Low S` (e.g., to $100$–$150$) to filter out background greys, whites, or metal parts.
6. **Tune Value (V)**: Adjust `Low V` (e.g., to $50$–$100$) to ignore shadow areas or dark reflections on the plate.
7. **Verify**: Ensure the yellow outline wraps the ball tightly and the red center dot remains stable as the ball rolls.

---

## 4. Explanation of Processing Stages

### Stage 1: Alignment and Stream Retrieval
```
+------------------+     +-------------------+
|  RGB Color Frame |     |    Depth Frame    |
+--------+---------+     +---------+---------+
         |                         |
         +------------+------------+
                      |
                      v
            [ rs.align(color) ]
                      |
                      v
             Aligned Data Arrays
```
RealSense retrieves synchronized color and depth frames. The depth frame is mathematically warped so that pixel $(x, y)$ in depth maps to pixel $(x, y)$ in the color frame.

### Stage 2: ArUco Marker Detection
The image is scanned for Marker 0 (left) and Marker 1 (right). 
- Let $P_0 = (x_0, y_0)$ be the center of Marker 0.
- Let $P_1 = (x_1, y_1)$ be the center of Marker 1.
- **Plate Center**:
  $$C_{plate} = \frac{P_0 + P_1}{2}$$
- **Plate Axis Unit Vector**:
  $$\vec{u}_{plate} = \frac{P_1 - P_0}{\|P_1 - P_0\|_2}$$
- **Plate Width (px)**:
  $$W_{plate} = \|P_1 - P_0\|_2$$

This geometric coordinate system rotates and translates dynamically as the camera or plate moves, ensuring invariant tracking.

### Stage 3: Ball Segmentation
- The color image is converted to HSV.
- Thresholding generates a binary mask based on user-configured sliders.
- A circularity shape filter selects the largest contour matching a sphere:
  $$\text{circularity} = \frac{4 \pi \times \text{Area}}{\text{Perimeter}^2}$$
- The center coordinates of the ball $B = (x_b, y_b)$ are calculated using a minimum enclosing circle algorithm.

### Stage 4: Coordinate Projection & Error Normalization
The vector representing the ball position relative to the plate center is projected onto the plate unit axis vector:
$$\text{offset\_pixels} = (B - C_{plate}) \cdot \vec{u}_{plate}$$

The normalized error is computed as:
$$\text{normalized\_error} = \frac{\text{offset\_pixels}}{W_{plate} / 2}$$

This value is clamped to $[-1.0, 1.0]$. 
- $-1.0$: Far left (ball is at Marker 0)
- $0.0$: Plate center
- $+1.0$: Far right (ball is at Marker 1)

Based on a configurable threshold, the state is classified as `LEFT`, `CENTER`, or `RIGHT`.

### Stage 5: 3D Depth Deprojection
To obtain the ball's real-world coordinates relative to the camera:
1. A $3\times3$ grid around the ball center pixel $(x_b, y_b)$ is queried.
2. Zeros are discarded, and the **median** value is calculated (providing high immunity to single-pixel depth dropouts).
3. Using the pinhole camera camera model, the pixel coordinates and depth $Z$ are mapped to 3D space:
   $$X = \frac{(x_b - p_{px}) \cdot Z}{f_x}$$
   $$Y = \frac{(y_b - p_{py}) \cdot Z}{f_y}$$
4. The coordinates are scaled by $1000.0$ to return `[X, Y, Z]` in millimeters.

---

## 5. Error Handling & Robustness

The system is designed to handle hardware and occlusion faults gracefully without raising fatal exceptions:

| Condition | Internal Action | API Output State | Error & Offset Outputs |
| :--- | :--- | :--- | :--- |
| **Marker 0 or 1 missing** | Plate coordinate system cannot be calculated. | `"LOST_MARKERS"` | `ball_error = 0.0`, `ball_offset_pixels = 0.0`. Returns ball pixel center if ball is visible. |
| **Ball missing** | Ball center and depth cannot be computed. | `"LOST_BALL"` | `ball_error = 0.0`, `ball_offset_pixels = 0.0`, `ball_xyz_mm = [0,0,0]`. Returns plate center coordinate. |
| **Depth dropout** | Depth is zero at the ball center. | Runs normally, uses last valid depth or fallback. | Returns `ball_depth_m = 0.0`, `ball_xyz_mm = [0,0,0]`. |
