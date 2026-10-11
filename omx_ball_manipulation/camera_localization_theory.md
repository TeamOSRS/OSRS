# Computer Vision and Kinematics: Multi-Camera Pose Calibration and 3D Ball Triangulation

This document provides a research-level mathematical and physical analysis of the multi-camera system implemented in the MuJoCo workspace. It outlines the coordinate convention differences (OpenGL vs. OpenCV), the Perspective-n-Point (PnP) calibration algorithm, the ray-plane intersection formulation, and the mathematical derivations of all error metrics.

---

## 1. Coordinate Conventions: OpenGL vs. OpenCV

MuJoCo's visualizer and renderer utilize the **OpenGL** coordinate convention, whereas OpenCV's calibration and geometry tools utilize the **OpenCV (standard pinhole)** coordinate convention. Resolving this mismatch is critical for correct projection and back-projection.

```
       OpenGL Camera Convention (MuJoCo)         OpenCV Camera Convention (Pinhole)
       
                     ▲ Y_c                                      │ Z_c (Forward)
                     │                                          ▼
                     │                                     ┌─────────┐
                     │                                     │         │
      X_c ◄──────────┘ (Right)                             │  Image  │
                    /                                      │  Plane  │
                   /                                       └─────────┘
                  ▼ Z_c (Backward)                              │
                                                                ▼ Y_c (Down)
                                                                
                                                   X_c ─────────► (Right)
```

The differences between the axes are:
1.  **$X$-axis**: Points to the right in both conventions.
2.  **$Y$-axis**: Points **up** in OpenGL, but **down** in OpenCV (matching pixel coordinates down-direction).
3.  **$Z$-axis**: Points **backward** (away from the scene) in OpenGL, but **forward** (into the scene along the optical axis) in OpenCV.

We define the transformation matrix $\mathbf{R}_{\text{conv}} \in SO(3)$ representing a $180^\circ$ rotation around the camera's $X$-axis:
$$\mathbf{R}_{\text{conv}} = \begin{bmatrix} 1 & 0 & 0 \\ 0 & -1 & 0 \\ 0 & 0 & -1 \end{bmatrix}$$

### Conversion Formulas
Let $\mathbf{C}$ represent the camera center in the World frame, and let $\mathbf{R}_{c,\text{OpenGL}}$ represent the Camera-to-World rotation matrix in OpenGL convention (as returned by MuJoCo's `data.cam_xmat`).

The Camera-to-World rotation matrix in OpenCV convention $\mathbf{R}_{c,\text{OpenCV}}$ is:
$$\mathbf{R}_{c,\text{OpenCV}} = \mathbf{R}_{c,\text{OpenGL}} \mathbf{R}_{\text{conv}}$$

The world point $\mathbf{X}_w$ is transformed into OpenCV camera coordinates $\mathbf{X}_{c,\text{OpenCV}}$ via:
$$\mathbf{X}_{c,\text{OpenCV}} = \mathbf{R}_{c,\text{OpenCV}}^T (\mathbf{X}_w - \mathbf{C}) = \mathbf{R}_{\text{conv}}^T \mathbf{R}_{c,\text{OpenGL}}^T (\mathbf{X}_w - \mathbf{C})$$

Since $Z_{c,\text{OpenCV}} > 0$ for points in front of the camera, we project the point onto the 2D image plane using the intrinsic matrix $\mathbf{K}$:
$$\mathbf{x}_{\text{img}} = \mathbf{K} \mathbf{X}_{c,\text{OpenCV}} \implies \begin{bmatrix} u \\ v \\ 1 \end{bmatrix} = \frac{1}{Z_{c,\text{OpenCV}}} \mathbf{K} \mathbf{X}_{c,\text{OpenCV}}$$

---

## 2. Extrinsic Calibration via Perspective-n-Point (PnP)

For Camera 2 (Front Camera), the world position $\mathbf{C}_2$ and orientation $\mathbf{R}_{2}$ are unknown. We estimate them using $N=6$ landmark points of known 3D world coordinates (the base and joint hinges of the left and right manipulators).

### PnP Formulation
For each landmark $i \in \{1, \dots, 6\}$, we know:
*   Its 3D position in the World frame: $\mathbf{X}_{w, i} \in \mathbb{R}^3$.
*   Its corresponding 2D pixel coordinate in Camera 2: $\mathbf{x}_i = [u_i, v_i]^T \in \mathbb{R}^2$.

OpenCV's `solvePnP` minimizes the projection error:
$$\min_{\mathbf{r}, \mathbf{t}} \sum_{i=1}^{N} \left\| \mathbf{x}_i - \pi\left(\mathbf{K}, \mathbf{R}(\mathbf{r}) \mathbf{X}_{w, i} + \mathbf{t}\right) \right\|^2$$
where $\mathbf{R}(\mathbf{r})$ is the rotation matrix obtained from rotation vector $\mathbf{r}$ via Rodrigues' formula.

The resulting extrinsics represent the World-to-Camera transformation:
$$\mathbf{X}_{c,\text{OpenCV}} = \mathbf{R}_{\text{w}\to\text{c}} \mathbf{X}_w + \mathbf{t}_{\text{w}\to\text{c}}$$
where $\mathbf{R}_{\text{w}\to\text{c}} = \mathbf{R}(\mathbf{r})$.

We invert this transformation to find the camera's pose in World coordinates:
1.  **Estimated Position**:
    $$\mathbf{C}_2 = -\mathbf{R}_{\text{w}\to\text{c}}^T \mathbf{t}_{\text{w}\to\text{c}}$$
2.  **Estimated OpenCV Orientation**:
    $$\mathbf{R}_{2,\text{OpenCV}} = \mathbf{R}_{\text{w}\to\text{c}}^T$$
3.  **Estimated OpenGL Orientation (for validation against MuJoCo)**:
    $$\mathbf{R}_{2,\text{OpenGL}} = \mathbf{R}_{2,\text{OpenCV}} \mathbf{R}_{\text{conv}}$$

---

## 3. 2D Ball Centroid Extraction and Occlusion Modeling

We locate the red ball in the rendered image using HSV thresholding:
1.  Convert RGB to HSV. Red wraps around $0^\circ$ and $180^\circ$ Hue, so we threshold two ranges and compute their union:
    $$\text{Mask} = \text{Threshold}(0 \le H \le 10) \cup \text{Threshold}(170 \le H \le 180)$$
2.  Compute the image moments of the binary mask:
    $$m_{pq} = \sum_{u, v} u^p v^q \text{Mask}(u, v)$$
3.  The centroid is:
    $$u = \frac{m_{10}}{m_{00}}, \quad v = \frac{m_{01}}{m_{00}}$$

### Physical Occlusion Analysis (Grazing Angle Jitter)
In Camera 2 (Front Camera), the ball sits inside the $23\text{ mm}$ deep U-channel of the plate. Because the camera is looking almost horizontally ($Z_{\text{camera}} \approx 0.30\text{ m}$), the front wall of the channel occludes the bottom part of the ball.

Only the top slice of the sphere is visible, shifting the detected HSV centroid in the front camera upwards ($v_{\text{hsv}} < v_{\text{true}}$) by about **$8.7$ pixels**. At a grazing angle, this shifts the plane intersection point by **$92\text{ mm}$**. This highlights a classic computer vision challenge: visual centroids do not match physical centroids under occlusion.

---

## 4. 3D Ball Localization via Ray-Plane Intersection

Given a camera's intrinsic matrix $\mathbf{K}$, center $\mathbf{C}$, and OpenCV rotation matrix $\mathbf{R}_{c,\text{OpenCV}}$, we back-project a pixel coordinate $(u, v)$ to a 3D ray.

1.  **Ray direction in Camera frame**:
    $$\mathbf{v}_c = \begin{bmatrix} (u - c_x)/f_x \\ (v - c_y)/f_y \\ 1.0 \end{bmatrix}$$
2.  **Ray direction in World frame**:
    $$\mathbf{v}_w = \mathbf{R}_{c,\text{OpenCV}} \mathbf{v}_c$$
    Normalized ray vector: $\hat{\mathbf{v}}_w = \frac{\mathbf{v}_w}{\|\mathbf{v}_w\|}$.
3.  **Ray Equation**:
    $$\mathbf{p}(t) = \mathbf{C} + t \hat{\mathbf{v}}_w$$
4.  **Plate Plane Equation**:
    The plate normal vector in the World frame is the local $Z$-axis of the plate:
    $$\hat{\mathbf{n}}_p = \mathbf{R}_{\text{plate}} \begin{bmatrix} 0 \\ 0 \\ 1 \end{bmatrix} = \mathbf{R}_{\text{plate}}[:, 2]$$
    Let $h_{\text{center}}$ be the height of the ball center relative to the plate center (including MuJoCo solver contact penetration: $h_{\text{center}} \approx 4.13\text{ mm}$). A point $\mathbf{p}_0$ on the plane of the ball center is:
    $$\mathbf{p}_0 = \mathbf{p}_{\text{plate}} + h_{\text{center}} \hat{\mathbf{n}}_p$$
    The plane equation is:
    $$\hat{\mathbf{n}}_p \cdot (\mathbf{p} - \mathbf{p}_0) = 0$$
5.  **Ray-Plane Intersection Solution**:
    Substituting the ray equation into the plane equation:
    $$\hat{\mathbf{n}}_p \cdot (\mathbf{C} + t \hat{\mathbf{v}}_w - \mathbf{p}_0) = 0 \implies t = \frac{\hat{\mathbf{n}}_p \cdot (\mathbf{p}_0 - \mathbf{C})}{\hat{\mathbf{n}}_p \cdot \hat{\mathbf{v}}_w}$$
6.  **3D Ball Position**:
    $$\mathbf{p}_{\text{ball}} = \mathbf{C} + t \hat{\mathbf{v}}_w$$

---

## 5. Mathematical Formulations of Errors

This section details the exact mathematical formulas used to quantify the system errors.

### A. Camera Extrinsic Position Error
The position error $e_{\text{pos}}$ measures the Euclidean distance between the estimated camera center $\mathbf{C}_{\text{est}}$ (from solvePnP) and the true camera center $\mathbf{C}_{\text{true}}$ (from MuJoCo physics data):
$$e_{\text{pos}} = \|\mathbf{C}_{\text{est}} - \mathbf{C}_{\text{true}}\|_2 = \sqrt{\sum_{i=1}^{3} (C_{\text{est}, i} - C_{\text{true}, i})^2}$$

### B. Camera Extrinsic Rotation Angle Error
The rotation error evaluates the angular difference (geodesic distance on the $SO(3)$ manifold) between the estimated camera orientation matrix $\mathbf{R}_{\text{est}}$ and the true camera orientation matrix $\mathbf{R}_{\text{true}}$.
We compute the rotation difference matrix $\mathbf{R}_{\text{diff}} \in SO(3)$:
$$\mathbf{R}_{\text{diff}} = \mathbf{R}_{\text{true}}^T \mathbf{R}_{\text{est}}$$

For any rotation matrix, the trace is related to the rotation angle $\theta_{\text{err}}$ by:
$$\text{Tr}(\mathbf{R}_{\text{diff}}) = 1 + 2\cos(\theta_{\text{err}})$$

Solving for the orientation error in degrees:
$$\theta_{\text{err}} = \arccos\left(\frac{\text{Tr}(\mathbf{R}_{\text{diff}}) - 1.0}{2}\right) \cdot \frac{180^\circ}{\pi}$$
where the $\arccos$ input is clipped to $[-1, 1]$ to avoid numerical out-of-range errors due to floating-point precision.

### C. Ball 3D Localization Error
The localization error $e_{\text{loc}}$ represents the Euclidean distance between the triangulated 3D ball coordinate $\mathbf{p}_{\text{est}}$ and the ground-truth ball center coordinate $\mathbf{p}_{\text{true}}$ from MuJoCo:
$$e_{\text{loc}} = \|\mathbf{p}_{\text{est}} - \mathbf{p}_{\text{true}}\|_2 = \sqrt{\sum_{i=1}^{3} (p_{\text{est}, i} - p_{\text{true}, i})^2}$$

### D. Inter-Camera Discrepancy (Cross-Validation Error)
To verify that both cameras are aligned and coordinate systems are consistent without relying on ground-truth, we compute the Euclidean distance between the independent 3D estimates from Camera 1 ($\mathbf{p}_1$) and Camera 2 ($\mathbf{p}_2$):
$$e_{\text{discrepancy}} = \|\mathbf{p}_1 - \mathbf{p}_2\|_2$$

### E. Error Sensitivity Propagation at Grazing Angles (Geometric Amplification)
We mathematically derive why shallow viewing angles dramatically amplify keypoint detection noise.
Let $h$ represent the perpendicular distance of the camera from the plate plane:
$$h = \hat{\mathbf{n}}_p \cdot (\mathbf{p}_0 - \mathbf{C})$$

Let $\phi$ be the angle of incidence between the camera ray $\hat{\mathbf{v}}_w$ and the plate plane. The dot product is:
$$\hat{\mathbf{n}}_p \cdot \hat{\mathbf{v}}_w = -\sin\phi$$

Substituting this into the ray-plane intersection equation for the scalar $t$:
$$t = -\frac{h}{\sin\phi}$$

Let there be a small angular error $\delta \phi$ in the projected ray (due to keypoint detection noise or camera pose calibration error). The derivative of $t$ with respect to $\phi$ is:
$$\frac{dt}{d\phi} = \frac{d}{d\phi}\left(-\frac{h}{\sin\phi}\right) = \frac{h \cos\phi}{\sin^2\phi}$$

The spatial error along the ray $\delta t$ propagates as:
$$\delta t \approx \left(\frac{h \cos\phi}{\sin^2\phi}\right) \delta\phi$$

As the viewing angle becomes shallow ($\phi \to 0$):
*   The denominator $\sin^2\phi$ approaches zero quadratically.
*   This causes the sensitivity ratio $\frac{dt}{d\phi}$ to blow up to infinity.
*   For Camera 2, the angle is $\phi \approx 7.5^\circ$ ($0.13\text{ rad}$), giving:
    $$\frac{\cos\phi}{\sin^2\phi} \approx \frac{0.99}{0.017} \approx 58.2$$
    This mathematical sensitivity explains why an $8.7\text{ pixel}$ centroid shift propagates into a large $92.7\text{ mm}$ triangulation shift for Camera 2, while the top camera (steep angle, $\phi \approx 45^\circ$, amplification ratio $\approx 1.4$) remains highly robust (error $< 3\text{ mm}$).
