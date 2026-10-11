import mujoco
import numpy as np
import cv2
import time
from scipy.spatial.transform import Rotation as R

def get_camera_intrinsics(model, cam_id, width, height):
    """
    Computes the pinhole camera intrinsic matrix K from MuJoCo camera parameters.
    """
    fovy = model.cam_fovy[cam_id]
    # Convert fovy to focal length in pixels
    f_y = height / (2.0 * np.tan(np.radians(fovy) / 2.0))
    f_x = f_y  # MuJoCo cameras assume square pixels
    c_x = width / 2.0
    c_y = height / 2.0
    
    K = np.array([
        [f_x, 0.0, c_x],
        [0.0, f_y, c_y],
        [0.0, 0.0, 1.0]
    ])
    return K

# OpenGL (MuJoCo) to OpenCV camera coordinate system transformation matrix:
#   X_opencv = X_opengl (Right)
#   Y_opencv = -Y_opengl (Down)
#   Z_opencv = -Z_opengl (Forward)
# This is a rotation of 180 degrees around the camera's X-axis.
R_CONV = np.array([
    [1.0,  0.0,  0.0],
    [0.0, -1.0,  0.0],
    [0.0,  0.0, -1.0]
])

def project_world_to_pixel(K, R_c_opengl, C, X_w):
    """
    Projects a 3D world coordinate X_w to 2D pixel coordinates (u, v) using
    OpenGL camera orientation (R_c_opengl) and camera position (C) in world.
    """
    # Convert OpenGL camera orientation to OpenCV camera orientation
    R_c_opencv = R_c_opengl @ R_CONV
    R_w_to_c = R_c_opencv.T
    
    # Transform point to camera frame: X_c = R_w_to_c * (X_w - C)
    X_c = R_w_to_c @ (X_w - C)
    
    # Project to image plane using camera matrix K
    x_img = K @ X_c
    u = x_img[0] / x_img[2]
    v = x_img[1] / x_img[2]
    return np.array([u, v])

def locate_ball_in_image(img):
    """
    Locates the red ball in the RGB image using OpenCV HSV thresholding.
    Returns pixel coordinates (u, v) or None if not found.
    """
    # Convert RGB to HSV
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
    
    # Red color range definition (wraps around 0 and 180 in Hue)
    lower_red1 = np.array([0, 70, 50])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([170, 70, 50])
    upper_red2 = np.array([180, 255, 255])
    
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask = mask1 | mask2
    
    moments = cv2.moments(mask)
    if moments["m00"] > 0:
        u = moments["m10"] / moments["m00"]
        v = moments["m01"] / moments["m00"]
        return np.array([u, v])
    return None

def ray_plane_intersection(K, R_c_opencv, C, u, v, pos_plate, R_plate, h_center=0.0045):
    """
    Casts a ray from camera position C through pixel (u, v) and intersects
    it with the plane of the plate channel.
    R_c_opencv is the Camera to World rotation matrix in OpenCV convention.
    """
    # 1. Ray direction in OpenCV Camera frame
    f_x, f_y = K[0, 0], K[1, 1]
    c_x, c_y = K[0, 2], K[1, 2]
    
    v_c = np.array([
        (u - c_x) / f_x,
        (v - c_y) / f_y,
        1.0
    ])
    
    # 2. Rotate ray to World frame
    v_w = R_c_opencv @ v_c
    v_w_norm = v_w / np.linalg.norm(v_w)
    
    # 3. Define plate plane
    # The normal of the plate plane is its local Z-axis (3rd column of rotation matrix)
    n_p = R_plate[:, 2]
    
    # The plane point is offset from the plate center by h_center along the plate normal
    p0 = pos_plate + h_center * n_p
    
    # 4. Ray-Plane intersection formula:
    denom = np.dot(n_p, v_w_norm)
    if abs(denom) < 1e-6:
        return None # Ray is parallel to the plate
        
    t = np.dot(n_p, p0 - C) / denom
    p_ball = C + t * v_w_norm
    return p_ball

def main():
    # Load model and data
    model = mujoco.MjModel.from_xml_path("dual_scene.xml")
    data = mujoco.MjData(model)
    
    # Reset to home keyframe
    mujoco.mj_resetDataKeyframe(model, data, 0)
    
    # Place the ball at a known offset (e.g. X_local = 0.06m)
    ball_joint_id = model.joint('ball_joint').id
    ball_qposadr = model.jnt_qposadr[ball_joint_id]
    data.qpos[ball_qposadr] = 0.06
    
    # Step the physics a bit to let the ball drop and settle on the plate bottom
    print("Stepping simulation to let the ball settle physically...")
    for _ in range(300):
        # Lock arms at home positions
        data.ctrl[0] = 0.0
        data.ctrl[1] = -0.5938813
        data.ctrl[2] = 0.5617 # home Joint3
        data.ctrl[3] = 0.0322 # home Joint4
        data.ctrl[4] = 0.015
        
        data.ctrl[5] = 0.0
        data.ctrl[6] = -0.5938813
        data.ctrl[7] = 0.5617
        data.ctrl[8] = 0.0322
        data.ctrl[9] = 0.015
        
        mujoco.mj_step(model, data)
        
    # Setup camera details
    cam1_id = model.camera('top_cam').id
    cam2_id = model.camera('front_cam').id
    
    width, height = 640, 480
    renderer = mujoco.Renderer(model, height=height, width=width)
    
    # ==========================================================================
    # 1. READ TRUE POSES FROM MUJOCO
    # ==========================================================================
    C1_true = data.cam_xpos[cam1_id].copy()
    R1_true_opengl = data.cam_xmat[cam1_id].reshape(3, 3).copy()
    K1 = get_camera_intrinsics(model, cam1_id, width, height)
    
    C2_true = data.cam_xpos[cam2_id].copy()
    R2_true_opengl = data.cam_xmat[cam2_id].reshape(3, 3).copy()
    K2 = get_camera_intrinsics(model, cam2_id, width, height)
    
    print("=========================================================")
    print("TRUE POSES:")
    print(f"Camera 1 (Top) Position: {C1_true}")
    print(f"Camera 2 (Front) Position: {C2_true}")
    print("=========================================================")
    
    # ==========================================================================
    # 2. CALIBRATE CAMERA 2 (FRONT CAMERA) USING solvePnP
    # ==========================================================================
    # We select 6 reference landmarks (base and joint links of the robot arms)
    landmark_names = [
        "left_link1", "left_link2", "left_link3",
        "right_link1", "right_link2", "right_link3"
    ]
    
    object_points = []  # 3D points in World
    image_points = []   # 2D points in Camera 2 (noisy)
    
    np.random.seed(42)  # For reproducible noise simulation
    pixel_noise_std = 0.0  # Zero noise to check mathematical limits
    
    print("Calibrating Front Camera (Camera 2) via solvePnP...")
    for name in landmark_names:
        X_w = data.body(name).xpos.copy()
        # Project using true pose (includes OpenGL-to-OpenCV conversion internally)
        u, v = project_world_to_pixel(K2, R2_true_opengl, C2_true, X_w)
        
        object_points.append(X_w)
        image_points.append([u, v])
        
    object_points = np.array(object_points, dtype=np.float32)
    image_points = np.array(image_points, dtype=np.float32)
    
    # Run PnP calibration using OpenCV convention
    dist_coeffs = np.zeros(4)
    success, rvec, tvec = cv2.solvePnP(object_points, image_points, K2, dist_coeffs)
    
    # solvePnP returns rotation & translation mapping World to OpenCV Camera frame:
    R_w_to_c_opencv = cv2.Rodrigues(rvec)[0]
    R2_opencv_est = R_w_to_c_opencv.T  # OpenCV Camera to World orientation
    C2_est = -R2_opencv_est @ tvec.flatten()
    
    # Convert estimated OpenCV orientation back to OpenGL convention for validation
    R2_opengl_est = R2_opencv_est @ R_CONV
    
    # Compute pose errors
    pos_err = np.linalg.norm(C2_est - C2_true)
    R_diff = R2_true_opengl.T @ R2_opengl_est
    angle_err = np.degrees(np.arccos(np.clip((np.trace(R_diff) - 1.0) / 2.0, -1.0, 1.0)))
    
    print(f"Calibration Complete!")
    print(f"Estimated Position: {C2_est}")
    print(f"Position Error: {pos_err*1000:.3f} mm")
    print(f"Rotation Angle Error: {angle_err:.4f} degrees")
    print("=========================================================")
    
    # ==========================================================================
    # 3. DETECT BALL IN BOTH CAMERAS
    # ==========================================================================
    # Render RGB images
    renderer.update_scene(data, camera="top_cam")
    img1 = renderer.render()
    
    renderer.update_scene(data, camera="front_cam")
    img2 = renderer.render()
    
    # HSV segmentation
    uv1_hsv = locate_ball_in_image(img1)
    uv2_hsv = locate_ball_in_image(img2)
    
    # True projection of the ball center
    p_ball_true = data.body('ball').xpos.copy()
    uv1_proj = project_world_to_pixel(K1, R1_true_opengl, C1_true, p_ball_true)
    uv2_proj = project_world_to_pixel(K2, R2_true_opengl, C2_true, p_ball_true)
    
    print(f"Ball Coordinates comparison (HSV Centroid vs True Projection):")
    print(f"  Camera 1 (Top):")
    print(f"    HSV Segmented:      Pixel (u={uv1_hsv[0]:.2f}, v={uv1_hsv[1]:.2f})")
    print(f"    True Projected:     Pixel (u={uv1_proj[0]:.2f}, v={uv1_proj[1]:.2f})")
    print(f"    Pixel Offset:       {np.linalg.norm(uv1_hsv - uv1_proj):.3f} px")
    print(f"  Camera 2 (Front):")
    print(f"    HSV Segmented:      Pixel (u={uv2_hsv[0]:.2f}, v={uv2_hsv[1]:.2f})")
    print(f"    True Projected:     Pixel (u={uv2_proj[0]:.2f}, v={uv2_proj[1]:.2f})")
    print(f"    Pixel Offset:       {np.linalg.norm(uv2_hsv - uv2_proj):.3f} px (Due to U-channel wall occlusion!)")
    print("=========================================================")
    
    # ==========================================================================
    # 4. TRIANGULATE BALL 3D POSITION FROM BOTH CAMERAS
    # ==========================================================================
    pos_plate = data.body('plate_assembly').xpos.copy()
    R_plate = data.body('plate_assembly').xmat.reshape(3, 3).copy()
    
    R1_opencv_true = R1_true_opengl @ R_CONV
    
    # Calculate the actual height of the ball center in the plate's local frame
    # (this includes the contact penetration from MuJoCo physics)
    pos_ball_local_true = R_plate.T @ (p_ball_true - pos_plate)
    h_center_actual = pos_ball_local_true[2]
    
    # 4a. Triangulation using HSV Segmented Coordinates (with contact-aware height)
    p_ball_1_hsv = ray_plane_intersection(K1, R1_opencv_true, C1_true, uv1_hsv[0], uv1_hsv[1], pos_plate, R_plate, h_center=h_center_actual)
    p_ball_2_hsv = ray_plane_intersection(K2, R2_opencv_est, C2_est, uv2_hsv[0], uv2_hsv[1], pos_plate, R_plate, h_center=h_center_actual)
    
    # 4b. Triangulation using True Projected Coordinates (with contact-aware height)
    p_ball_1_proj = ray_plane_intersection(K1, R1_opencv_true, C1_true, uv1_proj[0], uv1_proj[1], pos_plate, R_plate, h_center=h_center_actual)
    p_ball_2_proj = ray_plane_intersection(K2, R2_opencv_est, C2_est, uv2_proj[0], uv2_proj[1], pos_plate, R_plate, h_center=h_center_actual)
    
    print("3D LOCALIZATION USING HSV SEGMENTATION:")
    print(f"  Cam 1 (Top) Estimate:   {p_ball_1_hsv} (Error: {np.linalg.norm(p_ball_1_hsv - p_ball_true)*1000:.3f} mm)")
    print(f"  Cam 2 (Front) Estimate: {p_ball_2_hsv} (Error: {np.linalg.norm(p_ball_2_hsv - p_ball_true)*1000:.3f} mm)")
    print("---------------------------------------------------------")
    print("3D LOCALIZATION USING TRUE PROJECTED PIXELS (MATHEMATICAL VERIFICATION):")
    print(f"  Cam 1 (Top) Estimate:   {p_ball_1_proj} (Error: {np.linalg.norm(p_ball_1_proj - p_ball_true)*1000:.6f} mm)")
    print(f"  Cam 2 (Front) Estimate: {p_ball_2_proj} (Error: {np.linalg.norm(p_ball_2_proj - p_ball_true)*1000:.6f} mm)")
    print("=========================================================")
    
    if np.linalg.norm(p_ball_1_proj - p_ball_true) < 1e-4 and np.linalg.norm(p_ball_2_proj - p_ball_true) < 1e-4:
        print("SUCCESS: The ray-plane intersection math is 100% correct! Triangulation error is zero when using true projection pixels.")
    else:
        print("ERROR: Math verification failed. Check coordinate frame conversions.")

if __name__ == '__main__':
    main()
