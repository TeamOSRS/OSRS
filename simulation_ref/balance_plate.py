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

# Path to the custom robot scene XML
XML_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "my_bot_plate_scene.xml")

# Check if file exists
if not os.path.exists(XML_PATH):
    print(f"Error: XML scene file not found at: {XML_PATH}")
    sys.exit(1)

# Parse command line arguments
parser = argparse.ArgumentParser(description="Custom Humanoid Bimanual Ball-on-Plate Balancing Simulation")
parser.add_argument("--headless", action="store_true", help="Run in headless validation mode without opening viewer")
args = parser.parse_args()

# Control State
exit_simulation = False
elapsed_time = 0.0
fps = 0.0
ball_y_pos = 0.0
plate_tilt_deg = 0.0
target_ball_y = 0.0

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

# Joint Lists
LEFT_ARM_JOINTS = ['l_sho_pitch', 'l_sho_roll', 'l_sho_yaw', 'l_el_pitch', 'l_forearm_yaw', 'l_wrist_pitch', 'l_wrist_yaw']
RIGHT_ARM_JOINTS = ['r_sho_pitch', 'r_sho_roll', 'r_sho_yaw', 'r_el_pitch', 'r_forearm_yaw', 'r_wrist_pitch', 'r_wrist_yaw']
MOTOR_JOINTS = LEFT_ARM_JOINTS + RIGHT_ARM_JOINTS

# Map joint names to their velocity/configuration addresses
joint_qpos_adr = {name: model.joint(name).qposadr[0] for name in MOTOR_JOINTS}
joint_qvel_adr = {name: model.joint(name).dofadr[0] for name in MOTOR_JOINTS}

# Joint PID Controller with Derivative on Measurement
class PIDController:
    def __init__(self, kp, ki, kd, limit=12.0, windup=6.0):
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

# Initialize PID controllers for J1-J7 of both arms (Torque controlled)
pids = {name: PIDController(kp=120.0, ki=6.0, kd=5.0, limit=25.0, windup=6.0) for name in MOTOR_JOINTS}

# Ball Balancing PID Controller (Controls plate roll tilt to balance ball along Y-axis)
class BallBalancingPID:
    def __init__(self, kp=1.6, kd=0.7, ki=0.15, max_delta_z=0.03):
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
        # If ball is at +Y, error is positive. We want a positive delta_z to raise the left hand
        # and lower the right hand, causing a positive roll tilt (R_x) which rolls the ball back to -Y.
        raw_delta_z = self.kp * error + self.ki * self.integral + self.kd * dy
        
        # Smoothly saturate to maximum physical displacement
        return self.max_delta_z * np.tanh(raw_delta_z / self.max_delta_z)

    def reset(self):
        self.integral = 0.0
        self.prev_error = 0.0

# Instantiate balancing controller
bal_pid = BallBalancingPID(kp=0.8, kd=0.3, ki=0.05, max_delta_z=0.035)

# Default joint posture targets (Home pose - physically symmetric across X-Z plane with palm-up pre-rotation)
q_home = {name: 0.0 for name in MOTOR_JOINTS}
q_home['l_sho_pitch'] = -0.18
q_home['r_sho_pitch'] = 0.18
q_home['l_sho_roll'] = 0.15
q_home['r_sho_roll'] = 0.15
q_home['l_sho_yaw'] = -0.03
q_home['r_sho_yaw'] = -0.03
q_home['l_el_pitch'] = -1.4
q_home['r_el_pitch'] = 1.4
q_home['l_forearm_yaw'] = 1.94
q_home['r_forearm_yaw'] = 1.94
q_home['l_wrist_pitch'] = 1.57
q_home['r_wrist_pitch'] = -1.57
q_home['l_wrist_yaw'] = -1.35
q_home['r_wrist_yaw'] = -1.35

q_targets = q_home.copy()

# Plate coordinates and grasp offsets
z_plate_nominal = 0.98
x_plate_nominal = 0.22
pos_left_local = np.array([0.0, 0.25, 0.0])
pos_right_local = np.array([0.0, -0.25, 0.0])

R_left_local = rx_matrix(np.pi)
R_right_local = rx_matrix(np.pi)

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

# Solve 7-DOF Damped Least Squares IK for one arm on kin_data
def solve_arm_ik(site_name, target_pos, target_quat, arm_joints, damping=0.03, step_scale=0.5, k_posture=0.001):
    site_id = model.site(site_name).id
    
    # 1. Update kin_data.qpos with the current q_targets for the arm joints
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
    dx = np.concatenate([pos_err, rot_err])
    
    # 4. Get Jacobian on virtual kinematics state
    jacp = np.zeros((3, model.nv))
    jacr = np.zeros((3, model.nv))
    mujoco.mj_jacSite(model, kin_data, jacp, jacr, site_id)
    J = np.vstack([jacp, jacr])
    
    # Extract columns corresponding to the active arm joints
    dof_indices = [model.joint(name).dofadr[0] for name in arm_joints]
    J_arm = J[:, dof_indices]
    
    # 5. Damped Least Squares (DLS) Pseudo-inverse
    A = J_arm @ J_arm.T + (damping ** 2) * np.eye(6)
    try:
        dq = J_arm.T @ np.linalg.solve(A, dx)
    except np.linalg.LinAlgError:
        dq = J_arm.T @ dx * 0.1
        
    # 6. Apply step update to target joint positions (clamped to limits) with posture regularization
    for i, name in enumerate(arm_joints):
        pull = (q_home[name] - q_targets[name]) * k_posture
        q_targets[name] += dq[i] * step_scale + pull
        joint_range = model.joint(name).range
        q_targets[name] = np.clip(q_targets[name], joint_range[0], joint_range[1])

# Reset state
def reset_simulation():
    global target_ball_y
    target_ball_y = 0.0
    
    # 1. Reset joints to the home target posture
    for name in MOTOR_JOINTS:
        q_targets[name] = q_home[name]
        
    # 2. Set kin_data.qpos to the seed targets to start virtual kinematics
    for name in MOTOR_JOINTS:
        kin_data.qpos[joint_qpos_adr[name]] = q_targets[name]
        kin_data.qvel[joint_qvel_adr[name]] = 0.0
        
    # 3. Pre-run virtual IK solver for 100 steps to let joint targets converge
    # to perfectly parallel poses matching the level plate position [0.15, 0.0, 0.75]
    pos_plate_des = np.array([x_plate_nominal, 0.0, z_plate_nominal])
    pos_left_target = pos_plate_des + pos_left_local
    pos_right_target = pos_plate_des + pos_right_local
    
    q_left_target = np.zeros(4)
    mujoco.mju_mat2Quat(q_left_target, R_left_local.flatten())
    q_right_target = np.zeros(4)
    mujoco.mju_mat2Quat(q_right_target, R_right_local.flatten())
    
    for _ in range(100):
        solve_arm_ik('l_eef', pos_left_target, q_left_target, LEFT_ARM_JOINTS)
        solve_arm_ik('r_eef', pos_right_target, q_right_target, RIGHT_ARM_JOINTS)
        
    # 4. Now q_targets contains the parallel joint angles. Copy them to physical data and kin_data.
    for name in MOTOR_JOINTS:
        data.qpos[joint_qpos_adr[name]] = q_targets[name]
        data.qvel[joint_qvel_adr[name]] = 0.0
        kin_data.qpos[joint_qpos_adr[name]] = q_targets[name]
        kin_data.qvel[joint_qvel_adr[name]] = 0.0
        
    # Reset Grippers
    for g_joint in ['l_finger_l_joint', 'l_finger_r_joint', 'r_finger_l_joint', 'r_finger_r_joint']:
        qpos_adr = model.joint(g_joint).qposadr[0]
        data.qpos[qpos_adr] = 0.0
        kin_data.qpos[qpos_adr] = 0.0
        
    # Reset Plate Assembly pos (stands at home location)
    plate_joint_id = model.joint('plate_joint').id
    plate_qposadr = model.jnt_qposadr[plate_joint_id]
    data.qpos[plate_qposadr:plate_qposadr+3] = np.array([x_plate_nominal, 0.0, z_plate_nominal])
    data.qpos[plate_qposadr+3:plate_qposadr+7] = np.array([1.0, 0.0, 0.0, 0.0])
    data.qvel[model.joint('plate_joint').dofadr[0]:model.joint('plate_joint').dofadr[0]+6] = 0.0

    # Reset Ball pos (starts offset by 5cm along Y plate channel at home height)
    ball_joint_id = model.joint('ball_joint').id
    ball_qposadr = model.jnt_qposadr[ball_joint_id]
    data.qpos[ball_qposadr:ball_qposadr+3] = np.array([x_plate_nominal, 0.05, z_plate_nominal + 0.02])
    data.qpos[ball_qposadr+3:ball_qposadr+7] = np.array([1.0, 0.0, 0.0, 0.0])
    data.qvel[model.joint('ball_joint').dofadr[0]:model.joint('ball_joint').dofadr[0]+6] = 0.0
    
    # Reset PIDs
    for pid in pids.values():
        pid.reset()
    bal_pid.reset()
    
    # Trigger a kinematics forward pass to align weld constraints
    mujoco.mj_forward(model, data)
    mujoco.mj_forward(model, kin_data)

# Command listener thread for interactive CLI
def input_listener():
    global target_ball_y, exit_simulation
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
                print("\n[RESET] Re-initialized ball position to +5cm offset.")
                print("Enter command: ", end="", flush=True)
            elif val.lower() in ['t', 'telemetry', 'status']:
                print_status()
            elif val.lower() in ['h', 'help', 'menu']:
                print_menu()
            else:
                try:
                    target_y = float(val)
                    if -0.22 <= target_y <= 0.22:
                        target_ball_y = target_y
                        print(f"\n[TARGET] Set ball target position to Y = {target_ball_y:.3f} m")
                    else:
                        print("Target must be between -0.22m and +0.22m (within the plate channel bounds).")
                except ValueError:
                    print(f"Unknown command '{val}'. Type a number to set target, 'r' to reset, 'q' to quit.")
                print("Enter command: ", end="", flush=True)
        except EOFError:
            print("\nNon-interactive environment (EOF) detected. CLI inputs disabled.")
            print("Simulation is running continuously. Close the MuJoCo window to exit.")
            break
        except KeyboardInterrupt:
            exit_simulation = True
            break

def print_menu():
    print("\n" + "="*60)
    print(" CUSTOM Humanoid Robot Ball-on-Plate Balancing Task")
    print(" (COOPERATIVE DUAL-ARM TACTILE BALANCING CONTROL)")
    print("="*60)
    print(" Commands:")
    print("   [number]  : Set ball target Y coordinate (e.g. 0.0 for center, -0.1 to +0.1)")
    print("   r / reset : Reset simulation (re-centers plate, offsets ball by +5cm)")
    print("   t / status: Print balancing telemetry")
    print("   h / menu  : Show this menu")
    print("   q / quit  : Exit simulation")
    print("="*60)
    print("Control Tips:")
    print("  - Drag the ball (Hold CTRL and Right-Click & Drag) in the MuJoCo GUI to perturb it.")
    print("  - The robot's eyes (head tracking) will automatically follow the red ball in real-time.")
    print("="*60)
    print("Enter command: ", end="", flush=True)

def print_status():
    print("\n" + "-"*50)
    print(f" [SIM TIME]    {elapsed_time:.2f} s")
    print(f" [BALL POSE]   Local Y = {ball_y_pos * 1000:.1f} mm  (Target: {target_ball_y * 1000:.1f} mm)")
    print(f" [PLATE TILT]  Roll = {plate_tilt_deg:.2f}°")
    print(f" [REAL-TIME]   Control Rate = {fps:.1f} Hz (timestep: {model.opt.timestep:.4f} s)")
    print("-"*50)
    print("Enter command: ", end="", flush=True)

def main():
    global elapsed_time, fps, ball_y_pos, plate_tilt_deg, exit_simulation
    
    # Initialize positions and weld alignment
    reset_simulation()
    
    # Filter targets initialization
    left_qpos_filt = np.array([q_targets[n] for n in LEFT_ARM_JOINTS])
    right_qpos_filt = np.array([q_targets[n] for n in RIGHT_ARM_JOINTS])
    
    if args.headless:
        # Headless validation loop (run 2500 steps, which is 5.0 seconds of simulation)
        dt = model.opt.timestep
        sim_steps = 2500
        print(f"Running headless simulation for {sim_steps} steps...")
        
        for step in range(sim_steps):
            # 1. Sense Ball state relative to plate assembly
            pos_plate = data.body('plate_assembly').xpos.copy()
            R_plate = data.body('plate_assembly').xmat.reshape(3, 3).copy()
            pos_ball = data.body('ball').xpos.copy()
            
            # Local coordinates of ball
            pos_ball_local = R_plate.T @ (pos_ball - pos_plate)
            ball_y_pos = pos_ball_local[1]
            
            # Local relative velocity of ball
            ball_joint_id = model.joint('ball_joint').id
            ball_dof = model.jnt_dofadr[ball_joint_id]
            vel_ball = data.qvel[ball_dof:ball_dof+3]
            
            plate_joint_id = model.joint('plate_joint').id
            plate_dof = model.jnt_dofadr[plate_joint_id]
            vel_plate = data.qvel[plate_dof:plate_dof+3]
            
            vel_rel_local = R_plate.T @ (vel_ball - vel_plate)
            dy_ball_local = vel_rel_local[1]
            
            # 2. Run plate balancing PID
            error = ball_y_pos - target_ball_y
            delta_z = bal_pid.update(error, dy_ball_local, dt)
            
            # 3. Compute desired plate rotation matrix
            phi = np.arctan2(2.0 * delta_z, 0.44)
            plate_tilt_deg = np.degrees(phi)
            R_plate_des = rx_matrix(phi)
            
            # Left and Right workspace targets
            pos_plate_des = np.array([x_plate_nominal, 0.0, z_plate_nominal])
            pos_left_target = pos_plate_des + R_plate_des @ pos_left_local
            R_left_target = R_plate_des @ R_left_local
            
            pos_right_target = pos_plate_des + R_plate_des @ pos_right_local
            R_right_target = R_plate_des @ R_right_local
            
            # Convert to target quaternions
            q_left_target = np.zeros(4)
            mujoco.mju_mat2Quat(q_left_target, R_left_target.flatten())
            q_right_target = np.zeros(4)
            mujoco.mju_mat2Quat(q_right_target, R_right_target.flatten())
            
            # 4. Numerical DLS IK
            for _ in range(2):
                solve_arm_ik('l_eef', pos_left_target, q_left_target, LEFT_ARM_JOINTS)
                solve_arm_ik('r_eef', pos_right_target, q_right_target, RIGHT_ARM_JOINTS)
                
            # 5. Low-pass filter joint targets to eliminate chatter
            alpha = 0.25
            left_curr = np.array([q_targets[n] for n in LEFT_ARM_JOINTS])
            right_curr = np.array([q_targets[n] for n in RIGHT_ARM_JOINTS])
            left_qpos_filt = alpha * left_curr + (1.0 - alpha) * left_qpos_filt
            right_qpos_filt = alpha * right_curr + (1.0 - alpha) * right_qpos_filt
            
            for i, name in enumerate(LEFT_ARM_JOINTS):
                q_targets[name] = left_qpos_filt[i]
            for i, name in enumerate(RIGHT_ARM_JOINTS):
                q_targets[name] = right_qpos_filt[i]
                
            # 6. Apply Python joint-space PID torque control with Active Gravity Compensation
            for name in MOTOR_JOINTS:
                error_joint = q_targets[name] - data.qpos[joint_qpos_adr[name]]
                vel_joint = data.qvel[joint_qvel_adr[name]]
                torque = pids[name].update(error_joint, vel_joint, dt)
                bias_torque = data.qfrc_bias[joint_qvel_adr[name]]
                data.ctrl[actuator_indices[name + "_act"]] = torque + bias_torque
                
            # Grippers holding plate (0.80 rad open position for palm-up support)
            data.ctrl[actuator_indices['l_gripper_l_act']] = 0.80
            data.ctrl[actuator_indices['l_gripper_r_act']] = 0.80
            data.ctrl[actuator_indices['r_gripper_l_act']] = 0.80
            data.ctrl[actuator_indices['r_gripper_r_act']] = 0.80
            
            # Ball tracking head control
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
            
            if (step + 1) % 250 == 0:
                actual_tilt_deg = np.degrees(np.arctan2(R_plate[2, 1], R_plate[2, 2]))
                l_err = np.linalg.norm(pos_left_target - data.site_xpos[model.site('l_eef').id])
                l_kin_err = np.linalg.norm(pos_left_target - kin_data.site_xpos[model.site('l_eef').id])
                # Get max control torque for the left arm actuators
                l_ctrl = [data.ctrl[actuator_indices[name + "_act"]] for name in LEFT_ARM_JOINTS]
                print(f"Step {step+1:4d} | Sim Time: {dt*(step+1):.2f}s | Ball Local Y: {ball_y_pos * 1000:.2f} mm | Desired Tilt: {plate_tilt_deg:.2f}° | Actual Tilt: {actual_tilt_deg:.2f}° | L Phys Err: {l_err*1000:.1f}mm | Max Torque: {max(np.abs(l_ctrl)):.2f} Nm")
                
        print("\nHeadless simulation validation finished.")
        print(f"Final Ball position relative to center: {ball_y_pos * 1000:.3f} mm")
        if abs(ball_y_pos) < 0.01:
            print("SUCCESS: Ball balanced within 1 cm from the center!")
            sys.exit(0)
        else:
            print("FAILURE: Ball not balanced.")
            sys.exit(1)
            
    # Interactive GUI View Mode
    # Start the CLI input listener in a separate thread
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
            
            # 1. Sense Ball state relative to plate assembly
            pos_plate = data.body('plate_assembly').xpos.copy()
            R_plate = data.body('plate_assembly').xmat.reshape(3, 3).copy()
            pos_ball = data.body('ball').xpos.copy()
            
            # Local coordinates of ball
            pos_ball_local = R_plate.T @ (pos_ball - pos_plate)
            ball_y_pos = pos_ball_local[1]
            
            # Local relative velocity of ball
            ball_joint_id = model.joint('ball_joint').id
            ball_dof = model.jnt_dofadr[ball_joint_id]
            vel_ball = data.qvel[ball_dof:ball_dof+3]
            
            plate_joint_id = model.joint('plate_joint').id
            plate_dof = model.jnt_dofadr[plate_joint_id]
            vel_plate = data.qvel[plate_dof:plate_dof+3]
            
            vel_rel_local = R_plate.T @ (vel_ball - vel_plate)
            dy_ball_local = vel_rel_local[1]
            
            # 1a. Detect active ball dragging
            ball_body_id = model.body('ball').id
            is_dragging = (viewer.perturb.active > 0) and (viewer.perturb.select == ball_body_id)
            
            # 2. Run plate balancing PID
            if is_dragging:
                bal_pid.reset()
                delta_z = 0.0  # Keep the plate level during drag
            else:
                error = ball_y_pos - target_ball_y
                delta_z = bal_pid.update(error, dy_ball_local, dt)
            
            # 3. Compute desired plate rotation matrix (roll tilt around X)
            phi = np.arctan2(2.0 * delta_z, 0.44)
            plate_tilt_deg = np.degrees(phi)
            R_plate_des = rx_matrix(phi)
            
            # Left and Right workspace targets
            pos_plate_des = np.array([x_plate_nominal, 0.0, z_plate_nominal])
            pos_left_target = pos_plate_des + R_plate_des @ pos_left_local
            R_left_target = R_plate_des @ R_left_local
            
            pos_right_target = pos_plate_des + R_plate_des @ pos_right_local
            R_right_target = R_plate_des @ R_right_local
            
            # Convert to target quaternions
            q_left_target = np.zeros(4)
            mujoco.mju_mat2Quat(q_left_target, R_left_target.flatten())
            q_right_target = np.zeros(4)
            mujoco.mju_mat2Quat(q_right_target, R_right_target.flatten())
            
            # 4. Numerical DLS IK
            for _ in range(2):
                solve_arm_ik('l_eef', pos_left_target, q_left_target, LEFT_ARM_JOINTS)
                solve_arm_ik('r_eef', pos_right_target, q_right_target, RIGHT_ARM_JOINTS)
                
            # 5. Low-pass filter joint targets to eliminate chatter
            alpha = 0.25
            left_curr = np.array([q_targets[n] for n in LEFT_ARM_JOINTS])
            right_curr = np.array([q_targets[n] for n in RIGHT_ARM_JOINTS])
            left_qpos_filt = alpha * left_curr + (1.0 - alpha) * left_qpos_filt
            right_qpos_filt = alpha * right_curr + (1.0 - alpha) * right_qpos_filt
            
            for i, name in enumerate(LEFT_ARM_JOINTS):
                q_targets[name] = left_qpos_filt[i]
            for i, name in enumerate(RIGHT_ARM_JOINTS):
                q_targets[name] = right_qpos_filt[i]
                
            # 6. Apply Python joint-space PID torque control with Active Gravity Compensation
            for name in MOTOR_JOINTS:
                error_joint = q_targets[name] - data.qpos[joint_qpos_adr[name]]
                vel_joint = data.qvel[joint_qvel_adr[name]]
                torque = pids[name].update(error_joint, vel_joint, dt)
                bias_torque = data.qfrc_bias[joint_qvel_adr[name]]
                data.ctrl[actuator_indices[name + "_act"]] = torque + bias_torque
                
            # Grippers holding plate (0.80 rad open position for palm-up support)
            data.ctrl[actuator_indices['l_gripper_l_act']] = 0.80
            data.ctrl[actuator_indices['l_gripper_r_act']] = 0.80
            data.ctrl[actuator_indices['r_gripper_l_act']] = 0.80
            data.ctrl[actuator_indices['r_gripper_r_act']] = 0.80
            
            # Ball tracking head control (Eyes look at the ball in real time!)
            head_pos = data.body('head_tilt_link').xpos.copy()
            dx_head = pos_ball[0] - head_pos[0]
            dy_head = pos_ball[1] - head_pos[1]
            dz_head = pos_ball[2] - head_pos[2]
            head_yaw_target = np.clip(np.arctan2(dy_head, dx_head), -1.57, 1.57)
            head_tilt_target = np.clip(np.arctan2(-dz_head, np.sqrt(dx_head**2 + dy_head**2)), -0.8, 0.8)
            data.ctrl[actuator_indices['head_yaw_act']] = head_yaw_target
            data.ctrl[actuator_indices['head_tilt_act']] = head_tilt_target
            
            # Step physics applying perturb forces if user is dragging objects in GUI
            with viewer.lock():
                data.xfrc_applied[:] = 0
                mujoco.mjv_applyPerturbForce(model, data, viewer.perturb)
                mujoco.mjv_applyPerturbPose(model, data, viewer.perturb, 0)
            mujoco.mj_step(model, data)
            
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
