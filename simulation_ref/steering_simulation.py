import mujoco
import mujoco.viewer
import numpy as np
import time
import threading
import sys
import os
import argparse

def rx_matrix(phi):
    cos_phi = np.cos(phi)
    sin_phi = np.sin(phi)
    return np.array([
        [1.0, 0.0, 0.0],
        [0.0, cos_phi, -sin_phi],
        [0.0, sin_phi, cos_phi]
    ], dtype=np.float64)

def ry_matrix(theta):
    cos_theta = np.cos(theta)
    sin_theta = np.sin(theta)
    return np.array([
        [cos_theta, 0.0, sin_theta],
        [0.0, 1.0, 0.0],
        [-sin_theta, 0.0, cos_theta]
    ], dtype=np.float64)

def rz_matrix(psi):
    cos_psi = np.cos(psi)
    sin_psi = np.sin(psi)
    return np.array([
        [cos_psi, -sin_psi, 0.0],
        [sin_psi, cos_psi, 0.0],
        [0.0, 0.0, 1.0]
    ], dtype=np.float64)

# Path to the custom robot scene XML
XML_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "steering_plate_scene.xml")

# Check if file exists
if not os.path.exists(XML_PATH):
    print(f"Error: XML scene file not found at: {XML_PATH}")
    sys.exit(1)

# Parse command line arguments
parser = argparse.ArgumentParser(description="Bimanual MuJoCo Plate Steering Simulation")
parser.add_argument("--headless", action="store_true", help="Run in headless validation mode without opening viewer")
args = parser.parse_args()

# Control State
exit_simulation = False
elapsed_time = 0.0
fps = 0.0
ball_y_pos = 0.0
plate_roll_deg = 0.0
plate_pitch_deg = 0.0

# Load model & data
try:
    model = mujoco.MjModel.from_xml_path(XML_PATH)
    data = mujoco.MjData(model)
    kin_data = mujoco.MjData(model)  # Virtual kinematics state
except Exception as e:
    print(f"Failed to load MuJoCo model: {e}")
    sys.exit(1)

# Get joint/actuator indices mapping
actuator_indices = {model.actuator(i).name: i for i in range(model.nu)}
cam_id = model.camera('head_camera').id

# Joint Lists
LEFT_ARM_JOINTS = ['l_sho_pitch', 'l_sho_roll', 'l_sho_yaw', 'l_el_pitch', 'l_forearm_yaw', 'l_wrist_pitch', 'l_wrist_yaw']
RIGHT_ARM_JOINTS = ['r_sho_pitch', 'r_sho_roll', 'r_sho_yaw', 'r_el_pitch', 'r_forearm_yaw', 'r_wrist_pitch', 'r_wrist_yaw']
MOTOR_JOINTS = LEFT_ARM_JOINTS + RIGHT_ARM_JOINTS

# Map joint names to their velocity/configuration addresses
joint_qpos_adr = {name: model.joint(name).qposadr[0] for name in MOTOR_JOINTS}
joint_qvel_adr = {name: model.joint(name).dofadr[0] for name in MOTOR_JOINTS}

# Active joints for IK (J3, J4, J5, J6)
LEFT_ACTIVE_JOINTS = ['l_sho_yaw', 'l_el_pitch', 'l_forearm_yaw', 'l_wrist_pitch']
RIGHT_ACTIVE_JOINTS = ['r_sho_yaw', 'r_el_pitch', 'r_forearm_yaw', 'r_wrist_pitch']

# Joint PID Controller
class PIDController:
    def __init__(self, kp, ki, kd, limit=25.0, windup=6.0):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.limit = limit
        self.windup = windup
        self.integral = 0.0
        self.last_p = 0.0
        self.last_i = 0.0
        self.last_d = 0.0
        
    def update(self, error, vel, dt):
        self.integral += error * dt
        self.integral = np.clip(self.integral, -self.windup, self.windup)
        
        self.last_p = self.kp * error
        self.last_i = self.ki * self.integral
        self.last_d = -self.kd * vel
        
        output = self.last_p + self.last_i + self.last_d
        return np.clip(output, -self.limit, self.limit)

    def reset(self):
        self.integral = 0.0
        self.last_p = 0.0
        self.last_i = 0.0
        self.last_d = 0.0

# Ball Balancing PID Controller (Controls plate roll tilt to balance ball along Y-axis)
class BallBalancingPID:
    def __init__(self, kp=0.8, kd=0.3, ki=0.05, max_delta_z=0.035):
        self.kp = kp
        self.kd = kd
        self.ki = ki
        self.max_delta_z = max_delta_z
        self.integral = 0.0
        self.prev_error = 0.0
        
    def update(self, error, dy, dt):
        self.integral += error * dt
        self.integral = np.clip(self.integral, -0.1, 0.1)
        
        # Proportional + Integral + Derivative action
        raw_delta_z = self.kp * error + self.ki * self.integral + self.kd * dy
        
        # Smoothly saturate to maximum physical displacement
        return self.max_delta_z * np.tanh(raw_delta_z / self.max_delta_z)

    def reset(self):
        self.integral = 0.0
        self.prev_error = 0.0

# Initialize PID controllers for J1-J7 of both arms (Torque controlled)
pids = {name: PIDController(kp=120.0, ki=6.0, kd=5.0, limit=25.0, windup=6.0) for name in MOTOR_JOINTS}
bal_pid = BallBalancingPID(kp=0.4, kd=0.25, ki=0.01, max_delta_z=0.08)

# Default locked configuration
# Rest position of J1 and J2 = 0.0
# Rest position of J7 = -1.5708 for both to achieve mirrored symmetric grasp
q_locked = {name: 0.0 for name in MOTOR_JOINTS}
q_locked['l_wrist_yaw'] = -1.5708
q_locked['r_wrist_yaw'] = -1.5708

# Seed values for active joints in IK (J3, J4, J5, J6)
q_seed = {
    'l_sho_yaw': -1.5708,
    'l_el_pitch': -1.0,
    'l_forearm_yaw': 1.5708,
    'l_wrist_pitch': 1.5708,
    'r_sho_yaw': -1.5708,
    'r_el_pitch': 1.0,
    'r_forearm_yaw': 1.5708,
    'r_wrist_pitch': -1.5708
}

q_targets = {}
for name in MOTOR_JOINTS:
    if name in q_seed:
        q_targets[name] = q_seed[name]
    else:
        q_targets[name] = q_locked[name]

# Nominal plate position (raised to 0.90m to clear the stand)
x_plate_nominal = 0.22
y_plate_nominal = 0.0
z_plate_nominal = 0.90
pos_left_local = np.array([0.0, 0.19, 0.03])
pos_right_local = np.array([0.0, -0.19, 0.03])

# Hand target home orientations (grippers face each other and fingers clamp along X axis)
R_left_home_target = np.array([
    [0.0, 1.0, 0.0],
    [0.0, 0.0, 1.0],
    [1.0, 0.0, 0.0]
])
R_right_home_target = np.array([
    [0.0, -1.0, 0.0],
    [0.0, 0.0, -1.0],
    [1.0, 0.0, 0.0]
])

# Helper for quaternion multiplication
def quat_mul(q1, q2):
    w1, x1, y1, z1 = q1
    w2, x2, y2, z2 = q2
    return np.array([
        w1*w2 - x1*x2 - y1*y2 - z1*z2,
        w1*x2 + x1*w2 + y1*z2 - z1*y2,
        w1*y2 - x1*z2 + y1*w2 + z1*x2,
        w1*z2 + x1*y2 - y1*x2 + z1*w2
    ])

def quat_inv(q):
    return np.array([q[0], -q[1], -q[2], -q[3]])

# Solve 4-DOF Damped Least Squares IK for one arm on kin_data (tracking position and orientation with lower weight)
def solve_arm_ik(site_name, target_pos, target_quat, arm_joints, active_joints, damping=0.03, step_scale=0.2, k_posture=0.001):
    site_id = model.site(site_name).id
    
    # 1. Update kin_data.qpos with the current q_targets
    for name in arm_joints:
        qpos_adr = model.joint(name).qposadr[0]
        kin_data.qpos[qpos_adr] = q_targets[name]
        
    # 2. Update virtual kinematics
    mujoco.mj_fwdPosition(model, kin_data)
    
    # 3. Compute Cartesian error relative to virtual end-effector position
    current_pos = kin_data.site_xpos[site_id].copy()
    current_rot_mat = kin_data.site_xmat[site_id].copy().reshape(3, 3)
    current_quat = np.zeros(4)
    mujoco.mju_mat2Quat(current_quat, current_rot_mat.flatten())
    
    pos_err = target_pos - current_pos
    q_err = quat_mul(target_quat, quat_inv(current_quat))
    rot_err = 2.0 * q_err[1:4] * np.sign(q_err[0])
    
    # Weight orientation error lower so position tracking is strictly prioritized
    # and joint saturation is avoided
    rot_err *= 0.10
    dx = np.concatenate([pos_err, rot_err])
    
    # 4. Get 6D Jacobian on virtual kinematics state
    jacp = np.zeros((3, model.nv))
    jacr = np.zeros((3, model.nv))
    mujoco.mj_jacSite(model, kin_data, jacp, jacr, site_id)
    J = np.vstack([jacp, jacr])
    
    # Extract columns corresponding to the active arm joints (J3, J4, J5, J6)
    dof_indices = [model.joint(name).dofadr[0] for name in active_joints]
    J_arm = J[:, dof_indices]
    
    # 5. Damped Least Squares (DLS) Pseudo-inverse
    A = J_arm @ J_arm.T + (damping ** 2) * np.eye(6)
    try:
        dq = J_arm.T @ np.linalg.solve(A, dx)
    except np.linalg.LinAlgError:
        dq = J_arm.T @ dx * 0.1
        
    # 6. Apply step update to target active joint positions (clamped to limits)
    for i, name in enumerate(active_joints):
        # Apply slight posture regularizer towards seed to stay in a nice configuration space
        pull = (q_seed[name] - q_targets[name]) * k_posture
        q_targets[name] += dq[i] * step_scale + pull
        joint_range = model.joint(name).range
        q_targets[name] = np.clip(q_targets[name], joint_range[0], joint_range[1])

# Reset state
def reset_simulation():
    global R_left_home_target, R_right_home_target
    
    # 1. Reset joints to the home target posture
    for name in MOTOR_JOINTS:
        if name in q_seed:
            q_targets[name] = q_seed[name]
        else:
            q_targets[name] = q_locked[name]
        
    # 2. Set kin_data.qpos to the seed targets to start virtual kinematics
    for name in MOTOR_JOINTS:
        kin_data.qpos[joint_qpos_adr[name]] = q_targets[name]
        data.qvel[joint_qvel_adr[name]] = 0.0
        
    # 3. Pre-run virtual IK solver for 150 steps to let joint targets converge
    # to perfectly grasp the level plate at [0.22, 0.0, 0.65]
    pos_plate_des = np.array([x_plate_nominal, y_plate_nominal, z_plate_nominal])
    pos_left_target = pos_plate_des + pos_left_local
    pos_right_target = pos_plate_des + pos_right_local
    
    q_left_target = np.zeros(4)
    mujoco.mju_mat2Quat(q_left_target, R_left_home_target.flatten())
    q_right_target = np.zeros(4)
    mujoco.mju_mat2Quat(q_right_target, R_right_home_target.flatten())
    
    for _ in range(150):
        solve_arm_ik('l_eef', pos_left_target, q_left_target, LEFT_ARM_JOINTS, LEFT_ACTIVE_JOINTS)
        solve_arm_ik('r_eef', pos_right_target, q_right_target, RIGHT_ARM_JOINTS, RIGHT_ACTIVE_JOINTS)
        
    # 4. Now q_targets contains the parallel joint angles. Copy them to physical data and kin_data.
    for name in MOTOR_JOINTS:
        data.qpos[joint_qpos_adr[name]] = q_targets[name]
        data.qvel[joint_qvel_adr[name]] = 0.0
        kin_data.qpos[joint_qpos_adr[name]] = q_targets[name]
        kin_data.qvel[joint_qvel_adr[name]] = 0.0
        
    # Reset Grippers to open position
    for g_joint in ['l_finger_l_joint', 'l_finger_r_joint', 'r_finger_l_joint', 'r_finger_r_joint']:
        qpos_adr = model.joint(g_joint).qposadr[0]
        data.qpos[qpos_adr] = 0.0
        kin_data.qpos[qpos_adr] = 0.0
        
    # Reset Plate Assembly pos (stands at home location)
    plate_joint_id = model.joint('plate_joint').id
    plate_qposadr = model.jnt_qposadr[plate_joint_id]
    plate_pos = np.array([x_plate_nominal, y_plate_nominal, z_plate_nominal])
    data.qpos[plate_qposadr:plate_qposadr+3] = plate_pos
    data.qpos[plate_qposadr+3:plate_qposadr+7] = np.array([1.0, 0.0, 0.0, 0.0])
    data.qvel[model.joint('plate_joint').dofadr[0]:model.joint('plate_joint').dofadr[0]+6] = 0.0

    kin_data.qpos[plate_qposadr:plate_qposadr+3] = plate_pos
    kin_data.qpos[plate_qposadr+3:plate_qposadr+7] = np.array([1.0, 0.0, 0.0, 0.0])
    kin_data.qvel[model.joint('plate_joint').dofadr[0]:model.joint('plate_joint').dofadr[0]+6] = 0.0

    # Reset Ball pos (starts offset by 5cm along Y plate channel)
    ball_joint_id = model.joint('ball_joint').id
    ball_qposadr = model.jnt_qposadr[ball_joint_id]
    data.qpos[ball_qposadr:ball_qposadr+3] = np.array([x_plate_nominal, 0.05, z_plate_nominal + 0.02])
    data.qpos[ball_qposadr+3:ball_qposadr+7] = np.array([1.0, 0.0, 0.0, 0.0])
    data.qvel[model.joint('ball_joint').dofadr[0]:model.joint('ball_joint').dofadr[0]+6] = 0.0
    
    # Reset PIDs
    for pid in pids.values():
        pid.reset()
    bal_pid.reset()
    
    # Run a kinematics forward pass on virtual data to update body frames
    mujoco.mj_forward(model, kin_data)
    
    # Compute relative poses for the weld constraints
    l_wrist_id = model.body('l_wrist_yaw_link').id
    pos_l_wrist = kin_data.xpos[l_wrist_id].copy()
    R_l_wrist = kin_data.xmat[l_wrist_id].reshape(3, 3).copy()

    r_wrist_id = model.body('r_wrist_yaw_link').id
    pos_r_wrist = kin_data.xpos[r_wrist_id].copy()
    R_r_wrist = kin_data.xmat[r_wrist_id].reshape(3, 3).copy()

    plate_id = model.body('plate_assembly').id
    pos_plate = kin_data.xpos[plate_id].copy()
    R_plate = kin_data.xmat[plate_id].reshape(3, 3).copy()

    # Left weld relative pose (position and orientation)
    dp_l = R_l_wrist.T @ (pos_plate - pos_l_wrist)
    R_rel_l = R_l_wrist.T @ R_plate
    q_rel_l = np.zeros(4)
    mujoco.mju_mat2Quat(q_rel_l, R_rel_l.flatten())

    # Right weld relative pose (position and orientation)
    dp_r = R_r_wrist.T @ (pos_plate - pos_r_wrist)
    R_rel_r = R_r_wrist.T @ R_plate
    q_rel_r = np.zeros(4)
    mujoco.mju_mat2Quat(q_rel_r, R_rel_r.flatten())

    # Update model.eq_data with computed relative offsets
    left_weld_id = model.equality('left_hand_weld').id
    model.eq_data[left_weld_id, 3:6] = dp_l
    model.eq_data[left_weld_id, 6:10] = q_rel_l

    right_weld_id = model.equality('right_hand_weld').id
    model.eq_data[right_weld_id, 3:6] = dp_r
    model.eq_data[right_weld_id, 6:10] = q_rel_r

    # Trigger a physics forward pass on real data to initialize constraints
    mujoco.mj_forward(model, data)

# Command listener thread for interactive CLI
def input_listener():
    global exit_simulation
    print_menu()
    while not exit_simulation:
        try:
            val = input().strip()
            if not val:
                continue
            if val.lower() in ['q', 'quit', 'exit']:
                exit_simulation = True
                break
            elif val.lower() in ['r', 'reset']:
                reset_simulation()
                print("\n[RESET] Re-initialized simulation state.")
                print("Enter command: ", end="", flush=True)
            elif val.lower() in ['t', 'telemetry', 'status']:
                print_status()
            elif val.lower() in ['h', 'help', 'menu']:
                print_menu()
            else:
                print(f"Unknown command '{val}'. Type 'r' to reset, 'q' to quit.")
                print("Enter command: ", end="", flush=True)
        except EOFError:
            print("\nNon-interactive environment (EOF) detected. CLI inputs disabled.")
            break
        except KeyboardInterrupt:
            exit_simulation = True
            break

def print_menu():
    print("\n" + "="*60)
    print(" Bimanual Plate Steering Simulation (MuJoCo)")
    print("="*60)
    print(" Commands:")
    print("   r / reset : Reset simulation")
    print("   t / status: Print steering telemetry")
    print("   h / menu  : Show this menu")
    print("   q / quit  : Exit simulation")
    print("="*60)
    print("Enter command: ", end="", flush=True)

def print_status():
    print("\n" + "-"*50)
    print(f" [SIM TIME]    {elapsed_time:.2f} s")
    print(f" [BALL POSE]   Local Y = {ball_y_pos * 1000:.1f} mm")
    print(f" [PLATE ROLL]  {plate_roll_deg:.2f}°")
    print(f" [PLATE PITCH] {plate_pitch_deg:.2f}°")
    print(f" [REAL-TIME]   Control Rate = {fps:.1f} Hz")
    print("-"*50)
    print("Enter command: ", end="", flush=True)

def main():
    global elapsed_time, fps, ball_y_pos, plate_roll_deg, plate_pitch_deg, exit_simulation
    
    # Initialize positions and weld alignment
    reset_simulation()
    
    # Low-pass filter targets initialization
    left_qpos_filt = np.array([q_targets[n] for n in LEFT_ARM_JOINTS])
    right_qpos_filt = np.array([q_targets[n] for n in RIGHT_ARM_JOINTS])

    # Variables for RealSense camera simulation and finite difference velocity estimation
    prev_ball_y_pos_headless = 0.05
    dy_ball_filt_headless = 0.0
    
    prev_ball_y_pos_gui = 0.05
    dy_ball_filt_gui = 0.0
    
    if args.headless:
        # Headless validation loop (run 2500 steps, which is 5.0 seconds of simulation)
        dt = model.opt.timestep
        sim_steps = 2500
        print(f"Running headless simulation for {sim_steps} steps...")
        
        for step in range(sim_steps):
            t_curr = dt * step
            
            # --- REAL-WORLD REALSENSE PERCEPTION SIMULATION ---
            # 1. Sense camera's global frame from neck forward kinematics
            pos_cam = data.cam_xpos[cam_id].copy()
            R_cam = data.cam_xmat[cam_id].reshape(3, 3).copy()
            
            # 2. Get true global ball position and transform to Camera coordinate frame
            pos_ball_true = data.body('ball').xpos.copy()
            pos_ball_cam = R_cam.T @ (pos_ball_true - pos_cam)
            
            # 3. Add simulated RealSense depth/sensing noise (e.g. standard deviation of 2mm)
            noise = np.random.normal(0, 0.002, size=3)
            pos_ball_cam_noisy = pos_ball_cam + noise
            
            # 4. Reconstruct ball position in global base frame using camera forward kinematics
            pos_ball_reconstructed = pos_cam + R_cam @ pos_ball_cam_noisy
            
            # 5. Project reconstructed position relative to plate center into plate's local frame
            pos_plate = data.body('plate_assembly').xpos.copy()
            R_plate = data.body('plate_assembly').xmat.reshape(3, 3).copy()
            
            pos_ball_local = R_plate.T @ (pos_ball_reconstructed - pos_plate)
            ball_y_pos = pos_ball_local[1]
            
            # 6. Estimate ball velocity using low-pass filtered finite difference (no direct velocity sensor)
            dy_ball_raw = (ball_y_pos - prev_ball_y_pos_headless) / dt
            prev_ball_y_pos_headless = ball_y_pos
            dy_ball_filt_headless = 0.05 * dy_ball_raw + 0.95 * dy_ball_filt_headless
            dy_ball_local = dy_ball_filt_headless
            
            # 1. Run plate balancing PID
            error = ball_y_pos - 0.0  # target ball target_y = 0.0 (center)
            delta_z = bal_pid.update(error, dy_ball_local, dt)
            
            # Compute desired plate rotation matrix (phi is controlled by the balancer)
            phi = np.arctan2(2.0 * delta_z, 0.38)
            
            # Steering trajectory: oscillates pitch and translates inwards/outwards
            pitch_amp = 0.10
            x_amp = 0.02
            omega = 2.0 * np.pi * 0.2  # 0.2 Hz steering cycle
            
            theta = pitch_amp * np.cos(omega * t_curr)
            dx = x_amp * np.sin(2.0 * omega * t_curr)
            
            plate_roll_deg = np.degrees(phi)
            plate_pitch_deg = np.degrees(theta)
            
            R_plate_des = rx_matrix(phi) @ ry_matrix(theta)
            pos_plate_des = np.array([x_plate_nominal + dx, y_plate_nominal, z_plate_nominal])
            
            # Left and Right workspace targets
            pos_left_target = pos_plate_des + R_plate_des @ pos_left_local
            R_left_target = R_plate_des @ R_left_home_target
            
            pos_right_target = pos_plate_des + R_plate_des @ pos_right_local
            R_right_target = R_plate_des @ R_right_home_target
            
            # Convert to target quaternions
            q_left_target = np.zeros(4)
            mujoco.mju_mat2Quat(q_left_target, R_left_target.flatten())
            q_right_target = np.zeros(4)
            mujoco.mju_mat2Quat(q_right_target, R_right_target.flatten())
            
            # 2. Numerical 4-DOF DLS IK
            for _ in range(2):
                solve_arm_ik('l_eef', pos_left_target, q_left_target, LEFT_ARM_JOINTS, LEFT_ACTIVE_JOINTS)
                solve_arm_ik('r_eef', pos_right_target, q_right_target, RIGHT_ARM_JOINTS, RIGHT_ACTIVE_JOINTS)
                
            # 3. Low-pass filter active joint targets to eliminate chatter
            alpha = 0.25
            left_curr = np.array([q_targets[n] for n in LEFT_ARM_JOINTS])
            right_curr = np.array([q_targets[n] for n in RIGHT_ARM_JOINTS])
            left_qpos_filt = alpha * left_curr + (1.0 - alpha) * left_qpos_filt
            right_qpos_filt = alpha * right_curr + (1.0 - alpha) * right_qpos_filt
            
            for i, name in enumerate(LEFT_ARM_JOINTS):
                if name in LEFT_ACTIVE_JOINTS:
                    q_targets[name] = left_qpos_filt[i]
            for i, name in enumerate(RIGHT_ARM_JOINTS):
                if name in RIGHT_ACTIVE_JOINTS:
                    q_targets[name] = right_qpos_filt[i]
                
            # 4. Apply joint-space PID torque control with Gravity Compensation
            for name in MOTOR_JOINTS:
                error_joint = q_targets[name] - data.qpos[joint_qpos_adr[name]]
                vel_joint = data.qvel[joint_qvel_adr[name]]
                torque = pids[name].update(error_joint, vel_joint, dt)
                bias_torque = data.qfrc_bias[joint_qvel_adr[name]]
                data.ctrl[actuator_indices[name + "_act"]] = torque + bias_torque
                
            # Clamping gripper slides to grasp couplers (0.015m slide)
            data.ctrl[actuator_indices['l_gripper_l_act']] = 0.015
            data.ctrl[actuator_indices['l_gripper_r_act']] = 0.015
            data.ctrl[actuator_indices['r_gripper_l_act']] = 0.015
            data.ctrl[actuator_indices['r_gripper_r_act']] = 0.015
            
            # Head camera tracks ball
            pos_ball = data.body('ball').xpos.copy()
            head_pos = data.body('head_tilt_link').xpos.copy()
            dx_head = pos_ball[0] - head_pos[0]
            dy_head = pos_ball[1] - head_pos[1]
            dz_head = pos_ball[2] - head_pos[2]
            head_yaw_target = np.clip(np.arctan2(dy_head, dx_head), -1.57, 1.57)
            head_tilt_target = np.clip(np.arctan2(-dz_head, np.sqrt(dx_head**2 + dy_head**2)), -0.8, 0.8)
            data.ctrl[actuator_indices['head_yaw_act']] = head_yaw_target
            data.ctrl[actuator_indices['head_tilt_act']] = head_tilt_target
            
            # Step physics
            mujoco.mj_step(model, data)
            
            # Calculate local ball translation along plate Y axis
            pos_plate = data.body('plate_assembly').xpos.copy()
            R_plate = data.body('plate_assembly').xmat.reshape(3, 3).copy()
            pos_ball_local = R_plate.T @ (pos_ball - pos_plate)
            ball_y_pos = pos_ball_local[1]
            
            if (step + 1) % 250 == 0:
                print(f"Step {step+1:4d} | Sim Time: {dt*(step+1):.2f}s | Ball Local Y: {ball_y_pos * 1000:.2f} mm | Roll: {plate_roll_deg:.1f}° | Pitch: {plate_pitch_deg:.1f}° | Left Arm Yaw (J3): {q_targets['l_sho_yaw']:.3f} rad | Left Elbow (J4): {q_targets['l_el_pitch']:.3f} rad")
                
        print("\nHeadless simulation validation finished.")
        sys.exit(0)
            
    # Interactive GUI View Mode
    listener_thread = threading.Thread(target=input_listener, daemon=True)
    listener_thread.start()
    
    print("Launching MuJoCo passive viewer window...")
    with mujoco.viewer.launch_passive(model, data) as viewer:
        sim_start_time = data.time
        last_fps_time = time.time()
        fps_counter = 0
        
        while viewer.is_running() and not exit_simulation:
            step_start = time.time()
            dt = model.opt.timestep
            
            elapsed_time = data.time - sim_start_time
            
            # --- REAL-WORLD REALSENSE PERCEPTION SIMULATION ---
            # 1. Sense camera's global frame from neck forward kinematics
            pos_cam = data.cam_xpos[cam_id].copy()
            R_cam = data.cam_xmat[cam_id].reshape(3, 3).copy()
            
            # 2. Get true global ball position and transform to Camera coordinate frame
            pos_ball_true = data.body('ball').xpos.copy()
            pos_ball_cam = R_cam.T @ (pos_ball_true - pos_cam)
            
            # 3. Add simulated RealSense depth/sensing noise (e.g. standard deviation of 2mm)
            noise = np.random.normal(0, 0.002, size=3)
            pos_ball_cam_noisy = pos_ball_cam + noise
            
            # 4. Reconstruct ball position in global base frame using camera forward kinematics
            pos_ball_reconstructed = pos_cam + R_cam @ pos_ball_cam_noisy
            
            # 5. Project reconstructed position relative to plate center into plate's local frame
            pos_plate = data.body('plate_assembly').xpos.copy()
            R_plate = data.body('plate_assembly').xmat.reshape(3, 3).copy()
            
            pos_ball_local = R_plate.T @ (pos_ball_reconstructed - pos_plate)
            ball_y_pos = pos_ball_local[1]
            
            # 6. Estimate ball velocity using low-pass filtered finite difference (no direct velocity sensor)
            dy_ball_raw = (ball_y_pos - prev_ball_y_pos_gui) / dt
            prev_ball_y_pos_gui = ball_y_pos
            dy_ball_filt_gui = 0.05 * dy_ball_raw + 0.95 * dy_ball_filt_gui
            dy_ball_local = dy_ball_filt_gui
            
            # 1. Run plate balancing PID
            error = ball_y_pos - 0.0  # target ball target_y = 0.0 (center)
            delta_z = bal_pid.update(error, dy_ball_local, dt)
            
            # Compute desired plate rotation matrix (phi is controlled by the balancer)
            phi = np.arctan2(2.0 * delta_z, 0.38)
            
            # Steering trajectory: oscillates pitch and translates inwards/outwards
            pitch_amp = 0.10
            x_amp = 0.02
            omega = 2.0 * np.pi * 0.2  # 0.2 Hz steering cycle
            
            theta = pitch_amp * np.cos(omega * elapsed_time)
            dx = x_amp * np.sin(2.0 * omega * elapsed_time)
            
            plate_roll_deg = np.degrees(phi)
            plate_pitch_deg = np.degrees(theta)
            
            R_plate_des = rx_matrix(phi) @ ry_matrix(theta)
            pos_plate_des = np.array([x_plate_nominal + dx, y_plate_nominal, z_plate_nominal])
            
            # Left and Right workspace targets
            pos_left_target = pos_plate_des + R_plate_des @ pos_left_local
            R_left_target = R_plate_des @ R_left_home_target
            
            pos_right_target = pos_plate_des + R_plate_des @ pos_right_local
            R_right_target = R_plate_des @ R_right_home_target
            
            # Convert to target quaternions
            q_left_target = np.zeros(4)
            mujoco.mju_mat2Quat(q_left_target, R_left_target.flatten())
            q_right_target = np.zeros(4)
            mujoco.mju_mat2Quat(q_right_target, R_right_target.flatten())
            
            # 2. Numerical 4-DOF DLS IK
            for _ in range(2):
                solve_arm_ik('l_eef', pos_left_target, q_left_target, LEFT_ARM_JOINTS, LEFT_ACTIVE_JOINTS)
                solve_arm_ik('r_eef', pos_right_target, q_right_target, RIGHT_ARM_JOINTS, RIGHT_ACTIVE_JOINTS)
                
            # 3. Low-pass filter active joint targets to eliminate chatter
            alpha = 0.25
            left_curr = np.array([q_targets[n] for n in LEFT_ARM_JOINTS])
            right_curr = np.array([q_targets[n] for n in RIGHT_ARM_JOINTS])
            left_qpos_filt = alpha * left_curr + (1.0 - alpha) * left_qpos_filt
            right_qpos_filt = alpha * right_curr + (1.0 - alpha) * right_qpos_filt
            
            for i, name in enumerate(LEFT_ARM_JOINTS):
                if name in LEFT_ACTIVE_JOINTS:
                    q_targets[name] = left_qpos_filt[i]
            for i, name in enumerate(RIGHT_ARM_JOINTS):
                if name in RIGHT_ACTIVE_JOINTS:
                    q_targets[name] = right_qpos_filt[i]
                
            # 4. Apply joint-space PID torque control with Gravity Compensation
            for name in MOTOR_JOINTS:
                error_joint = q_targets[name] - data.qpos[joint_qpos_adr[name]]
                vel_joint = data.qvel[joint_qvel_adr[name]]
                torque = pids[name].update(error_joint, vel_joint, dt)
                bias_torque = data.qfrc_bias[joint_qvel_adr[name]]
                data.ctrl[actuator_indices[name + "_act"]] = torque + bias_torque
                
            # Clamping gripper slides to grasp couplers (0.015m slide)
            data.ctrl[actuator_indices['l_gripper_l_act']] = 0.015
            data.ctrl[actuator_indices['l_gripper_r_act']] = 0.015
            data.ctrl[actuator_indices['r_gripper_l_act']] = 0.015
            data.ctrl[actuator_indices['r_gripper_r_act']] = 0.015
            
            # Head camera tracks ball
            pos_ball = data.body('ball').xpos.copy()
            head_pos = data.body('head_tilt_link').xpos.copy()
            dx_head = pos_ball[0] - head_pos[0]
            dy_head = pos_ball[1] - head_pos[1]
            dz_head = pos_ball[2] - head_pos[2]
            head_yaw_target = np.clip(np.arctan2(dy_head, dx_head), -1.57, 1.57)
            head_tilt_target = np.clip(np.arctan2(-dz_head, np.sqrt(dx_head**2 + dy_head**2)), -0.8, 0.8)
            data.ctrl[actuator_indices['head_yaw_act']] = head_yaw_target
            data.ctrl[actuator_indices['head_tilt_act']] = head_tilt_target
            
            # Step physics
            mujoco.mj_step(model, data)
            
            # Calculate local ball translation along plate Y axis
            pos_plate = data.body('plate_assembly').xpos.copy()
            R_plate = data.body('plate_assembly').xmat.reshape(3, 3).copy()
            pos_ball_local = R_plate.T @ (pos_ball - pos_plate)
            ball_y_pos = pos_ball_local[1]
            
            # Sync passive viewer
            viewer.sync()
            
            # Calculate FPS
            fps_counter += 1
            now = time.time()
            if now - last_fps_time >= 1.0:
                fps = fps_counter / (now - last_fps_time)
                fps_counter = 0
                last_fps_time = now
            
            # Real-time sleep matching
            time_to_sleep = dt - (time.time() - step_start)
            if time_to_sleep > 0:
                time.sleep(time_to_sleep)
                
    exit_simulation = True
    print("\nSimulation ended. Goodbye!")

if __name__ == "__main__":
    main()
