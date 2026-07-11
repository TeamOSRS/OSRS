import mujoco
import mujoco.viewer
import numpy as np
import time
from scipy.spatial.transform import Rotation as R

# Import OpenCV for interactive trackbar GUI if available
try:
    import cv2
    cv2_available = True
except ImportError:
    cv2_available = False

# ======================================================================
# CONFIGURATION & PID TUNING PARAMETERS
# ======================================================================
# Edit these values to change the controller behavior and initial setup:
KP = 0.41               # Proportional gain (scaled for height-based control)
KD = 0.22               # Derivative gain (scaled for height-based control)
KI = 0.0                # Integral gain
MAX_DELTA_Z = 0.033     # Maximum vertical offset in meters (~3.3cm) corresponding to ~6.8 degrees of tilt
INITIAL_BALL_X = 0.05   # Initial displacement of the ball along the plate channel in meters (e.g. 5cm)
# ======================================================================


# ----------------------------------------------------------------------
# 1. BALL TACTILE BALANCING PID CONTROLLER
# ----------------------------------------------------------------------
class BallBalancingPID:
    def __init__(self, kp=2.2, kd=0.8, ki=0.08, max_delta_z=0.033):
        self.kp = kp
        self.kd = kd
        self.ki = ki
        self.max_delta_z = max_delta_z
        
        self.integral = 0.0
        self.prev_error = 0.0
        
    def update(self, error, d_error, dt):
        # Smooth quadratic deadzone to eliminate hunting / micro-oscillations (servo play)
        deadzone_width = 0.002  # 2 mm
        if abs(error) < deadzone_width:
            error = error * (abs(error) / deadzone_width)
            
        self.integral += error * dt
        # Clip integral to avoid windup
        self.integral = np.clip(self.integral, -0.5, 0.5)
        
        # Compute vertical arm height offset
        # Note: if ball is at +x, error = (target_x - ball_x) is negative.
        # We want to raise the right arm (Z decreases relative to nominal height offset)
        # and lower the left arm (Z increases relative to nominal height offset).
        # Therefore, delta_z should be negative: delta_z = Kp * error + ...
        raw_delta_z = (self.kp * error + self.ki * self.integral - self.kd * d_error)
        
        # Smoothly saturate to safety range using tanh (avoids slope discontinuities / jitter)
        return self.max_delta_z * np.tanh(raw_delta_z / self.max_delta_z)


# ----------------------------------------------------------------------
# 2. NUMERICAL INVERSE KINEMATICS SOLVER STEP
# ----------------------------------------------------------------------
def solve_ik_for_step(model, data, site_id, dof_indices, qpos_indices, limits, target_pos, target_mat, current_qpos, damping=0.015, step_size=0.8):
    """
    Solves one step of numerical Damped Least Squares Inverse Kinematics for a single arm,
    operating on current_qpos to track target_pos (position) and target_mat (rotation matrix) of the grasp site.
    """
    # Temporarily set qpos to current tracking state to evaluate forward kinematics
    orig_qpos = data.qpos.copy()
    for idx, q_idx in enumerate(qpos_indices):
        data.qpos[q_idx] = current_qpos[idx]
    
    mujoco.mj_forward(model, data)
    
    # Get current grasp site pose in world coordinates
    curr_pos = data.site(site_id).xpos
    curr_mat = data.site(site_id).xmat.reshape(3, 3)
    
    # Position error: only track Z position vertically.
    # Relax X and Y tracking to prevent the arm from fighting the rigid plate horizontal constraint
    pos_err = np.zeros(3)
    pos_err[2] = target_pos[2] - curr_pos[2]
    
    # Rotational error (axis-angle representation)
    rot_err = 0.5 * (np.cross(curr_mat[:, 0], target_mat[:, 0]) +
                     np.cross(curr_mat[:, 1], target_mat[:, 1]) +
                     np.cross(curr_mat[:, 2], target_mat[:, 2]))
    
    # Combined 6D error vector
    err = np.hstack([pos_err, rot_err])
    
    # Compute the full analytical Jacobians from MuJoCo for the site
    jacp = np.zeros((3, model.nv))
    jacr = np.zeros((3, model.nv))
    mujoco.mj_jacSite(model, data, jacp, jacr, site_id)
    jac = np.vstack([jacp, jacr])
    
    # Slice the columns corresponding to this arm's joints
    jac_arm = jac[:, dof_indices]
    
    # Damped Least Squares: dq = (J^T J + k^2 I)^-1 J^T err
    J_T = jac_arm.T
    dq = np.linalg.solve(J_T @ jac_arm + (damping**2) * np.eye(len(dof_indices)), J_T @ err)
    
    # Integrate update and apply joint limits
    updated_qpos = []
    for idx, q_idx in enumerate(qpos_indices):
        val = current_qpos[idx] + step_size * dq[idx]
        val = np.clip(val, limits[idx][0], limits[idx][1])
        updated_qpos.append(val)
        
    # Restore the original data.qpos state so we don't pollute the physics step
    data.qpos[:] = orig_qpos
    return np.array(updated_qpos), np.linalg.norm(err)


# ----------------------------------------------------------------------
# 3. MAIN SIMULATION PIPELINE
# ----------------------------------------------------------------------
def main():
    # Load model and data
    model = mujoco.MjModel.from_xml_path("dual_scene.xml")
    data = mujoco.MjData(model)
    
    # Reset to home keyframe (which starts with our optimized initial joint positions)
    mujoco.mj_resetDataKeyframe(model, data, 0)
    
    # Move the ball slightly to the side to trigger control action
    ball_joint_id = model.joint('ball_joint').id
    ball_qposadr = model.jnt_qposadr[ball_joint_id]
    data.qpos[ball_qposadr] = INITIAL_BALL_X
    
    # Arm joint names definition: Joint 1 (yaw) and Joint 2 (shoulder pitch) are kept locked
    # at their home keyframe values. Only Joint 3 (elbow pitch) and Joint 4 (wrist pitch)
    # are actively updated to tilt the plate.
    left_joint_names = ["left_Joint3", "left_Joint4"]
    right_joint_names = ["right_Joint3", "right_Joint4"]
    
    # Find joint limit ranges
    def get_joint_limits(model, names):
        ranges = []
        for name in names:
            j_id = model.joint(name).id
            ranges.append(model.jnt_range[j_id])
        return ranges

    left_limits = get_joint_limits(model, left_joint_names)
    right_limits = get_joint_limits(model, right_joint_names)
    
    # Helper to retrieve DoF and qpos indices for both arms
    def get_indices(names):
        dofs = [model.joint(n).dofadr[0] for n in names]
        qpos = [model.joint(n).qposadr[0] for n in names]
        return dofs, qpos

    left_dof_idx, left_qpos_idx = get_indices(left_joint_names)
    right_dof_idx, right_qpos_idx = get_indices(right_joint_names)
    
    # End effector site IDs (for true grasp frames)
    left_site_id = model.site("left_grasp_frame").id
    right_site_id = model.site("right_grasp_frame").id

    # Track target joint angles initialized from current qpos
    left_qpos_curr = np.array([data.qpos[idx] for idx in left_qpos_idx])
    right_qpos_curr = np.array([data.qpos[idx] for idx in right_qpos_idx])
    
    # PID controller for dynamic balancing (controls arm height offset delta_z directly)
    pid = BallBalancingPID(kp=KP, kd=KD, ki=KI, max_delta_z=MAX_DELTA_Z)
    
    # Cooperative Manipulation Plate Geometries (centered on the grasp slots)
    z_plate_nominal = 0.20
    pos_left_local = np.array([-0.2758, 0, 0.0])
    pos_right_local = np.array([0.2758, 0, 0.0])
    
    R_left_local = np.eye(3)
    R_right_local = np.diag([-1.0, -1.0, 1.0]) # 180 deg around Z
    
    # Simulation step time
    dt = model.opt.timestep
    sim_time = 0.0
    
    print("Launching passive MuJoCo visualizer...")
    try:
        viewer = mujoco.viewer.launch_passive(model, data)
        use_gui = True
    except Exception as e:
        print(f"Could not launch GUI viewer ({e}). Running in headless validation mode...")
        use_gui = False

    # Initialize OpenCV controls if GUI, CV2, and screen display are active
    cv2_active = False
    if use_gui and cv2_available:
        try:
            cv2.namedWindow("PID Controls")
            cv2.createTrackbar("Kp x100", "PID Controls", int(KP * 100), 500, lambda x: None)
            cv2.createTrackbar("Ki x1000", "PID Controls", int(KI * 1000), 500, lambda x: None)
            cv2.createTrackbar("Kd x100", "PID Controls", int(KD * 100), 500, lambda x: None)
            cv2.createTrackbar("Target", "PID Controls", 100, 200, lambda x: None)
            # Test-read to confirm window was successfully created (fails in headless)
            _ = cv2.getTrackbarPos("Kp x100", "PID Controls")
            cv2_active = True
            frame_counter = 0
        except Exception as e:
            print(f"OpenCV GUI window failed to initialize ({e}). Running without trackbars.")
            cv2_active = False

    # Initial forward pass to align weld constraints at keyframe home
    mujoco.mj_forward(model, data)
    
    if use_gui:
        # Initialize filtered joint positions for exponential smoothing
        left_qpos_filt = left_qpos_curr.copy()
        right_qpos_filt = right_qpos_curr.copy()
        
        with viewer:
            while viewer.is_running():
                step_start = time.time()
                
                # --- 1. READ SLIDER VALUES (IF CV2 ACTIVE) ---
                if cv2_active:
                    Kp = cv2.getTrackbarPos("Kp x100", "PID Controls") / 100.0
                    Ki = cv2.getTrackbarPos("Ki x1000", "PID Controls") / 1000.0
                    Kd = cv2.getTrackbarPos("Kd x100", "PID Controls") / 100.0
                    target_position = (cv2.getTrackbarPos("Target", "PID Controls") - 100) / 100.0
                    pid.kp = Kp
                    pid.ki = Ki
                    pid.kd = Kd
                else:
                    target_position = 0.0
                
                # --- 1a. DETECT ACTIVE BALL DRAGGING ---
                # Check if mouse perturbation is active on the ball
                ball_body_id = model.body('ball').id
                is_dragging = (viewer.perturb.active > 0) and (viewer.perturb.select == ball_body_id)
                
                # --- 2. SENSE BALL STATE IN PLATE FRAME ---
                pos_plate = data.body('plate_assembly').xpos
                R_plate = data.body('plate_assembly').xmat.reshape(3, 3)
                pos_ball = data.body('ball').xpos
                
                pos_ball_local = R_plate.T @ (pos_ball - pos_plate)
                x_ball_local = pos_ball_local[0]
                
                ball_joint_id = model.joint('ball_joint').id
                ball_dofadr = model.jnt_dofadr[ball_joint_id]
                vel_ball_world = data.qvel[ball_dofadr:ball_dofadr+3]
                
                plate_joint_id = model.joint('plate_joint').id
                plate_dofadr = model.jnt_dofadr[plate_joint_id]
                vel_plate_world = data.qvel[plate_dofadr:plate_dofadr+3]
                
                vel_rel_world = vel_ball_world - vel_plate_world
                vel_ball_local = R_plate.T @ vel_rel_world
                dx_ball_local = vel_ball_local[0]
                
                # --- 3. CONTROLLER (PID IN ARMS) ---
                if is_dragging:
                    pid.integral = 0.0  # Reset integral to prevent windup
                    pid.prev_error = 0.0
                    delta_z = 0.0       # Keep the plate level during drag
                else:
                    # Error is computed relative to the target slider position
                    error = target_position - x_ball_local
                    delta_z = pid.update(error, dx_ball_local, dt)
                
                # --- 4. DUAL-ARM COOPERATIVE TARGET POSE GENERATION ---
                # Command the arms vertically: left arm Z goes up by delta_z, right arm Z goes down by delta_z.
                # The plate reacts dynamically/physically due to the weld connection.
                # Compute equivalent pitch tilt theta corresponding to the height displacement:
                theta = np.arctan2(2.0 * delta_z, 0.5516)
                R_plate_des = R.from_euler('y', theta).as_matrix()
                
                pos_plate_des = np.array([0.0, 0.0, z_plate_nominal])
                pos_left_target = pos_plate_des + R_plate_des @ pos_left_local
                R_left_target = R_plate_des @ R_left_local
                
                pos_right_target = pos_plate_des + R_plate_des @ pos_right_local
                R_right_target = R_plate_des @ R_right_local
                
                # --- 5. NUMERICAL IK SOLVING ---
                for _ in range(5):
                    left_qpos_curr, left_err = solve_ik_for_step(
                        model, data, left_site_id, left_dof_idx, left_qpos_idx, left_limits,
                        pos_left_target, R_left_target, left_qpos_curr
                    )
                    right_qpos_curr, right_err = solve_ik_for_step(
                        model, data, right_site_id, right_dof_idx, right_qpos_idx, right_limits,
                        pos_right_target, R_right_target, right_qpos_curr
                    )
                
                # --- 5a. JOINT COMMAND SMOOTHING (LOW-PASS FILTER) ---
                # alpha = 0.25 (time constant of ~8ms at 500Hz) filters out IK chatter/jitter
                alpha = 0.25
                left_qpos_filt = alpha * left_qpos_curr + (1.0 - alpha) * left_qpos_filt
                right_qpos_filt = alpha * right_qpos_curr + (1.0 - alpha) * right_qpos_filt
                    
                # --- 6. MOTOR CONTROL OUTPUT ---
                # Joint 1 (yaw) and Joint 2 (shoulder pitch) remain locked at home keyframe positions (0 and -0.5938813)
                data.ctrl[0] = 0.0
                data.ctrl[1] = -0.5938813
                data.ctrl[2] = left_qpos_filt[0]
                data.ctrl[3] = left_qpos_filt[1]
                data.ctrl[4] = 0.015 # gripper
                
                data.ctrl[5] = 0.0
                data.ctrl[6] = -0.5938813
                data.ctrl[7] = right_qpos_filt[0]
                data.ctrl[8] = right_qpos_filt[1]
                data.ctrl[9] = 0.015 # gripper
                
                # --- 7. PHYSICS STEP WITH VIEWER PERTURBATION FORCES ---
                with viewer.lock():
                    data.xfrc_applied[:] = 0
                    mujoco.mjv_applyPerturbForce(model, data, viewer.perturb)
                    mujoco.mjv_applyPerturbPose(model, data, viewer.perturb, 0)
                mujoco.mj_step(model, data)
                sim_time += dt
                
                # --- 8. UPDATE OpenCV SLIDER INFO WINDOW OCCASIONALLY ---
                if cv2_active:
                    frame_counter += 1
                    if frame_counter % 8 == 0:
                        img = np.zeros((180, 560, 3), dtype=np.uint8)
                        cv2.putText(
                            img,
                            f"Kp={pid.kp:.2f}  Ki={pid.ki:.3f}  Kd={pid.kd:.2f}",
                            (20, 40),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.7,
                            (255, 255, 255),
                            2
                        )
                        cv2.putText(
                            img,
                            f"Target={target_position:.3f} m",
                            (20, 80),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.7,
                            (255, 255, 255),
                            2
                        )
                        cv2.putText(
                            img,
                            f"Ball X={x_ball_local:.3f} m",
                            (20, 120),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.7,
                            (255, 255, 255),
                            2
                        )
                        cv2.putText(
                            img,
                            f"Delta Z={delta_z*1000:.2f} mm | Tilt={np.degrees(theta):.2f} deg",
                            (20, 160),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6,
                            (255, 255, 255),
                            2
                        )
                        cv2.imshow("PID Controls", img)
                        cv2.waitKey(1)
                
                # Sync with passive viewer
                viewer.sync()
                
                # Maintain real-time speed
                elapsed = time.time() - step_start
                if elapsed < dt:
                    time.sleep(dt - elapsed)
    else:
        # Headless simulation loop (runs for 5.0 seconds of simulation time)
        max_steps = int(5.0 / dt)
        print(f"Headless simulation starting for {max_steps} steps (dt = {dt}s)...")
        
        # Initialize filtered joint positions for exponential smoothing
        left_qpos_filt = left_qpos_curr.copy()
        right_qpos_filt = right_qpos_curr.copy()
        
        for step in range(max_steps):
            # --- 1. SENSE BALL STATE IN PLATE FRAME ---
            pos_plate = data.body('plate_assembly').xpos
            R_plate = data.body('plate_assembly').xmat.reshape(3, 3)
            pos_ball = data.body('ball').xpos
            
            pos_ball_local = R_plate.T @ (pos_ball - pos_plate)
            x_ball_local = pos_ball_local[0]
            
            ball_joint_id = model.joint('ball_joint').id
            ball_dofadr = model.jnt_dofadr[ball_joint_id]
            vel_ball_world = data.qvel[ball_dofadr:ball_dofadr+3]
            
            plate_joint_id = model.joint('plate_joint').id
            plate_dofadr = model.jnt_dofadr[plate_joint_id]
            vel_plate_world = data.qvel[plate_dofadr:plate_dofadr+3]
            
            vel_rel_world = vel_ball_world - vel_plate_world
            vel_ball_local = R_plate.T @ vel_rel_world
            dx_ball_local = vel_ball_local[0]
            
            # --- 2. CONTROLLER (PID) ---
            # Default target in headless is 0.0
            error = 0.0 - x_ball_local
            delta_z = pid.update(error, dx_ball_local, dt)
            
            # --- 3. DUAL-ARM COOPERATIVE TRAJECTORY GENERATION ---
            theta = np.arctan2(2.0 * delta_z, 0.5516)
            R_plate_des = R.from_euler('y', theta).as_matrix()
            
            pos_plate_des = np.array([0.0, 0.0, z_plate_nominal])
            pos_left_target = pos_plate_des + R_plate_des @ pos_left_local
            R_left_target = R_plate_des @ R_left_local
            
            pos_right_target = pos_plate_des + R_plate_des @ pos_right_local
            R_right_target = R_plate_des @ R_right_local
            
            # --- 4. NUMERICAL IK SOLVING ---
            for _ in range(5):
                left_qpos_curr, left_err = solve_ik_for_step(
                    model, data, left_site_id, left_dof_idx, left_qpos_idx, left_limits,
                    pos_left_target, R_left_target, left_qpos_curr
                )
                right_qpos_curr, right_err = solve_ik_for_step(
                    model, data, right_site_id, right_dof_idx, right_qpos_idx, right_limits,
                    pos_right_target, R_right_target, right_qpos_curr
                )
                
            # --- 4a. JOINT COMMAND SMOOTHING (LOW-PASS FILTER) ---
            alpha = 0.25
            left_qpos_filt = alpha * left_qpos_curr + (1.0 - alpha) * left_qpos_filt
            right_qpos_filt = alpha * right_qpos_curr + (1.0 - alpha) * right_qpos_filt
            
            # --- 5. MOTOR CONTROL OUTPUT ---
            # Joint 1 (yaw) and Joint 2 (shoulder pitch) remain locked at home keyframe positions (0 and -0.5938813)
            data.ctrl[0] = 0.0
            data.ctrl[1] = -0.5938813
            data.ctrl[2] = left_qpos_filt[0]
            data.ctrl[3] = left_qpos_filt[1]
            data.ctrl[4] = 0.015 # gripper
            
            data.ctrl[5] = 0.0
            data.ctrl[6] = -0.5938813
            data.ctrl[7] = right_qpos_filt[0]
            data.ctrl[8] = right_qpos_filt[1]
            data.ctrl[9] = 0.015 # gripper
            
            # --- 6. PHYSICS STEP ---
            mujoco.mj_step(model, data)
            sim_time += dt
            
            # Print state every 0.5s of simulation time
            if step % int(0.5 / dt) == 0:
                print(f"Sim Time: {sim_time:.2f}s | Ball Local X: {x_ball_local * 1000:.2f} mm | Delta Z: {delta_z * 1000:.2f} mm | Plate Tilt: {np.degrees(theta):.2f}°")
                
        print("Headless validation completed successfully!")
                
    if cv2_active:
        cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
