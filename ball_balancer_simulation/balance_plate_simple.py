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

# Control State
exit_simulation = False
elapsed_time = 0.0
fps = 0.0
ball_y_pos = 0.0
prev_ball_y = 0.05
plate_tilt_deg = 0.0
target_ball_y = 0.0
feedback_gain = 3.0  # Proportional feedback gain mapping ball Y coordinate to elbow pitch

# Load model & data
try:
    model = mujoco.MjModel.from_xml_path(XML_PATH)
    data = mujoco.MjData(model)
    kin_data = mujoco.MjData(model)  # Virtual kinematics state for pre-run
except Exception as e:
    print(f"Failed to load MuJoCo model: {e}")
    sys.exit(1)

# Get joint/actuator indices mapping
actuator_indices = {model.actuator(i).name: i for i in range(model.nu)}

# Joint Lists
LEFT_ARM_JOINTS = ['l_sho_pitch', 'l_sho_roll', 'l_sho_yaw', 'l_el_pitch', 'l_forearm_yaw', 'l_wrist_pitch', 'l_wrist_yaw']
RIGHT_ARM_JOINTS = ['r_sho_pitch', 'r_sho_roll', 'r_sho_yaw', 'r_el_pitch', 'r_forearm_yaw', 'r_wrist_pitch', 'r_wrist_yaw']
MOTOR_JOINTS = LEFT_ARM_JOINTS + RIGHT_ARM_JOINTS

# Active joints for 6D pre-run alignment solver
LEFT_ACTIVE_JOINTS_PRERUN = LEFT_ARM_JOINTS
RIGHT_ACTIVE_JOINTS_PRERUN = RIGHT_ARM_JOINTS

# Posture-space stiffness weights to pull joints gently to q_home during pre-run
K_POSTURE = {name: 0.02 for name in MOTOR_JOINTS}

# Map joint names to their velocity/configuration addresses
joint_qpos_adr = {name: model.joint(name).qposadr[0] for name in MOTOR_JOINTS}
joint_qvel_adr = {name: model.joint(name).dofadr[0] for name in MOTOR_JOINTS}

# Joint PID Controller
class PIDController:
    def __init__(self, kp, ki, kd, limit=25.0, windup=6.0):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.limit = limit
        self.windup = windup
        self.integral = 0.0
        
    def update(self, error, vel, dt):
        self.integral += error * dt
        self.integral = np.clip(self.integral, -self.windup, self.windup)
        output = self.kp * error + self.ki * self.integral - self.kd * vel
        return np.clip(output, -self.limit, self.limit)

    def reset(self):
        self.integral = 0.0

# Initialize PID controllers for J1-J7 of both arms (Extremely high stiffness for locked joints)
pids = {}
for name in MOTOR_JOINTS:
    if 'sho' in name or 'forearm_yaw' in name:
        pids[name] = PIDController(kp=3500.0, ki=100.0, kd=150.0, limit=1000.0, windup=50.0)
    else:
        pids[name] = PIDController(kp=350.0, ki=10.0, kd=12.0, limit=200.0, windup=10.0)

# Default symmetric joint posture targets (Home pose)
q_home = {name: 0.0 for name in MOTOR_JOINTS}
q_home['l_sho_pitch'] = -0.60
q_home['r_sho_pitch'] = 0.60
q_home['l_sho_roll'] = 0.35
q_home['r_sho_roll'] = 0.35
q_home['l_sho_yaw'] = -0.03
q_home['r_sho_yaw'] = -0.03
q_home['l_el_pitch'] = -1.10
q_home['r_el_pitch'] = 1.10
q_home['l_forearm_yaw'] = 1.94
q_home['r_forearm_yaw'] = 1.94
q_home['l_wrist_pitch'] = 1.57
q_home['r_wrist_pitch'] = -1.57
q_home['l_wrist_yaw'] = -1.35
q_home['r_wrist_yaw'] = -1.35

q_targets = q_home.copy()
q_prerun = {}

# Plate coordinates and grasp offsets
z_plate_nominal = 1.02
x_plate_nominal = 0.22
pos_plate_nominal = np.array([x_plate_nominal, 0.0, z_plate_nominal])
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

# Solve 6-DOF Damped Least Squares IK for pre-run alignment
def solve_arm_ik(site_name, target_pos, target_quat, arm_joints, active_joints, damping=0.03, step_scale=0.5):
    site_id = model.site(site_name).id
    q_actual = np.array([kin_data.qpos[model.joint(name).qposadr[0]] for name in active_joints])
    current_pos = kin_data.site_xpos[site_id].copy()
    current_rot_mat = kin_data.site_xmat[site_id].copy().reshape(3, 3)
    current_quat = np.zeros(4)
    mujoco.mju_mat2Quat(current_quat, current_rot_mat.flatten())
    
    pos_err = target_pos - current_pos
    q_err = quat_mul(target_quat, quat_inv(current_quat))
    rot_err = 2.0 * q_err[1:4] * np.sign(q_err[0])
    total_error = np.concatenate([pos_err, rot_err])
    
    jacp = np.zeros((3, model.nv))
    jacr = np.zeros((3, model.nv))
    mujoco.mj_jacSite(model, kin_data, jacp, jacr, site_id)
    J = np.vstack([jacp, jacr])
    
    dof_indices = [model.joint(name).dofadr[0] for name in active_joints]
    J_arm = J[:, dof_indices]
    
    A = J_arm @ J_arm.T + (damping ** 2) * np.eye(6)
    try:
        dq = J_arm.T @ np.linalg.solve(A, total_error)
    except np.linalg.LinAlgError:
        dq = J_arm.T @ total_error * 0.1
        
    q_commanded = q_actual.copy()
    for i, name in enumerate(active_joints):
        pull = (q_home[name] - q_targets[name]) * K_POSTURE.get(name, 0.001)
        q_commanded[i] += dq[i] * step_scale + pull
        
    for i, name in enumerate(active_joints):
        joint_range = model.joint(name).range
        q_targets[name] = np.clip(q_commanded[i], joint_range[0], joint_range[1])
        kin_data.qpos[model.joint(name).qposadr[0]] = q_targets[name]
        
    mujoco.mj_fwdPosition(model, kin_data)

# Reset state
def reset_simulation():
    global target_ball_y, prev_ball_y, R_left_local, R_right_local, q_prerun, pos_plate_nominal, pos_left_local, pos_right_local
    target_ball_y = 0.0
    prev_ball_y = 0.05
    
    # Configure posture weights to gently pull all joints to home during pre-run
    for name in MOTOR_JOINTS:
        K_POSTURE[name] = 0.02
    
    # 1. Reset joints to the home target posture
    for name in MOTOR_JOINTS:
        q_targets[name] = q_home[name]
        
    # 2. Set kin_data.qpos to the seed targets to start virtual kinematics
    for name in MOTOR_JOINTS:
        kin_data.qpos[joint_qpos_adr[name]] = q_targets[name]
        kin_data.qvel[joint_qvel_adr[name]] = 0.0
        
    # 3. Pre-run virtual IK solver for 150 steps to let joint targets converge
    pos_plate_des = np.array([x_plate_nominal, 0.0, z_plate_nominal])
    pos_left_target = pos_plate_des + pos_left_local
    pos_right_target = pos_plate_des + pos_right_local
    
    q_left_target = np.zeros(4)
    mujoco.mju_mat2Quat(q_left_target, R_left_local.flatten())
    q_right_target = np.zeros(4)
    mujoco.mju_mat2Quat(q_right_target, R_right_local.flatten())
    
    for _ in range(150):
        # Solve 6-DOF IK (position and orientation) during pre-run
        solve_arm_ik('l_eef', pos_left_target, q_left_target, LEFT_ARM_JOINTS, LEFT_ACTIVE_JOINTS_PRERUN, damping=0.03, step_scale=0.5)
        solve_arm_ik('r_eef', pos_right_target, q_right_target, RIGHT_ARM_JOINTS, RIGHT_ACTIVE_JOINTS_PRERUN, damping=0.03, step_scale=0.5)
        
    # 4. Copy converged targets to physical data and kin_data
    for name in MOTOR_JOINTS:
        data.qpos[joint_qpos_adr[name]] = q_targets[name]
        data.qvel[joint_qvel_adr[name]] = 0.0
        kin_data.qpos[joint_qpos_adr[name]] = q_targets[name]
        kin_data.qvel[joint_qvel_adr[name]] = 0.0
        
    global q_prerun
    q_prerun = q_targets.copy()

    # Measure resolved local positions
    pos_left_actual = kin_data.site_xpos[model.site('l_eef').id].copy()
    pos_right_actual = kin_data.site_xpos[model.site('r_eef').id].copy()
    print(f"[DEBUG] Pre-run resolved hand distance: {np.linalg.norm(pos_left_actual - pos_right_actual):.5f} m")
    print("[DEBUG] q_prerun angles:")
    for name in sorted(q_targets.keys()):
        print(f"  {name}: {q_targets[name]:.4f}")
    pos_plate_nominal = (pos_left_actual + pos_right_actual) / 2.0
    pos_left_local = pos_left_actual - pos_plate_nominal
    pos_right_local = pos_right_actual - pos_plate_nominal

    R_left_local = kin_data.site_xmat[model.site('l_eef').id].copy().reshape(3, 3)
    R_right_local = kin_data.site_xmat[model.site('r_eef').id].copy().reshape(3, 3)

    # Restore locking weights
    for name in MOTOR_JOINTS:
        K_POSTURE[name] = 0.8

    # Reset Grippers
    for g_joint in ['l_finger_l_joint', 'l_finger_r_joint', 'r_finger_l_joint', 'r_finger_r_joint']:
        qpos_adr = model.joint(g_joint).qposadr[0]
        data.qpos[qpos_adr] = 0.0
        kin_data.qpos[qpos_adr] = 0.0
        
    # Reset Plate Assembly to match the resolved pose exactly (with 2.0 cm Z-offset for weld alignment)
    plate_joint_id = model.joint('plate_joint').id
    plate_qposadr = model.jnt_qposadr[plate_joint_id]
    pos_plate_start = pos_plate_nominal - np.array([0.0, 0.0, 0.02])
    data.qpos[plate_qposadr:plate_qposadr+3] = pos_plate_start
    data.qpos[plate_qposadr+3:plate_qposadr+7] = np.array([1.0, 0.0, 0.0, 0.0])
    data.qvel[model.joint('plate_joint').dofadr[0]:model.joint('plate_joint').dofadr[0]+6] = 0.0

    # Reset Ball to start offset by 5cm along Y plate channel, matching the resolved plate pos
    ball_joint_id = model.joint('ball_joint').id
    ball_qposadr = model.jnt_qposadr[ball_joint_id]
    data.qpos[ball_qposadr:ball_qposadr+3] = pos_plate_start + np.array([0.0, 0.05, 0.02])
    data.qpos[ball_qposadr+3:ball_qposadr+7] = np.array([1.0, 0.0, 0.0, 0.0])
    data.qvel[model.joint('ball_joint').dofadr[0]:model.joint('ball_joint').dofadr[0]+6] = 0.0
    
    # Reset PIDs
    for pid in pids.values():
        pid.reset()
    
    mujoco.mj_forward(model, data)
    mujoco.mj_forward(model, kin_data)

# Command listener thread
def input_listener():
    global target_ball_y, feedback_gain, exit_simulation
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
            elif val.lower() in ['t', 'telemetry', 'status']:
                print_status()
            elif val.lower() in ['h', 'help', 'menu']:
                print_menu()
            elif val.lower().startswith('g '):
                try:
                    new_gain = float(val.split()[1])
                    feedback_gain = new_gain
                    print(f"\n[GAIN] Set elbow feedback gain to: {feedback_gain:.2f}")
                except Exception:
                    print("Invalid gain syntax. Use: g [number]")
            else:
                try:
                    target_y = float(val)
                    if -0.22 <= target_y <= 0.22:
                        target_ball_y = target_y
                        print(f"\n[TARGET] Set ball target position to Y = {target_ball_y:.3f} m")
                    else:
                        print("Target must be between -0.22m and +0.22m (within channel bounds).")
                except ValueError:
                    print(f"Unknown command '{val}'. Type a number to set target, 'g [val]' to set gain, 'r' to reset, 'q' to quit.")
            print("Enter command: ", end="", flush=True)
        except EOFError:
            break
        except KeyboardInterrupt:
            exit_simulation = True
            break

def print_menu():
    print("\n" + "="*60)
    print(" CUSTOM Humanoid Robot Ball-on-Plate Balancing Task")
    print(" (SIMPLIFIED ELBOW SEE-SAW PROPORTIONAL CONTROL)")
    print("="*60)
    print(" Commands:")
    print("   [number]  : Set ball target Y coordinate (e.g. 0.0 for center)")
    print("   g [number]: Set proportional elbow feedback gain (default: 3.0)")
    print("   r / reset : Reset simulation (re-centers plate, offsets ball by +5cm)")
    print("   t / status: Print balancing telemetry")
    print("   h / menu  : Show this menu")
    print("   q / quit  : Exit simulation")
    print("="*60)
    print("Control Tips:")
    print("  - Drag the ball (Hold CTRL and Right-Click & Drag) in the MuJoCo GUI to perturb it.")
    print("="*60)
    print("Enter command: ", end="", flush=True)

def print_status():
    l_el_act = data.qpos[joint_qpos_adr['l_el_pitch']]
    r_el_act = data.qpos[joint_qpos_adr['r_el_pitch']]
    l_el_tgt = q_targets['l_el_pitch']
    r_el_tgt = q_targets['r_el_pitch']
    l_sho_act = data.qpos[joint_qpos_adr['l_sho_pitch']]
    r_sho_act = data.qpos[joint_qpos_adr['r_sho_pitch']]
    
    print("\n" + "-"*50)
    print(f" [SIM TIME]    {elapsed_time:.2f} s")
    print(f" [BALL POSE]   Local Y = {ball_y_pos * 1000:.1f} mm  (Target: {target_ball_y * 1000:.1f} mm)")
    print(f" [PLATE TILT]  Roll = {plate_tilt_deg:.2f}°")
    print(f" [ELBOW LEFT]  Act = {l_el_act:.4f} rad, Tgt = {l_el_tgt:.4f} rad")
    print(f" [ELBOW RIGHT] Act = {r_el_act:.4f} rad, Tgt = {r_el_tgt:.4f} rad")
    print(f" [SHOULDER L]  Act = {l_sho_act:.4f} rad, Prerun = {q_prerun['l_sho_pitch']:.4f} rad")
    print(f" [SHOULDER R]  Act = {r_sho_act:.4f} rad, Prerun = {q_prerun['r_sho_pitch']:.4f} rad")
    print(f" [ELBOW GAIN]  Gain = {feedback_gain:.2f}")
    print(f" [REAL-TIME]   Control Rate = {fps:.1f} Hz")
    print("-"*50)
    print("Enter command: ", end="", flush=True)

def main():
    global elapsed_time, fps, ball_y_pos, prev_ball_y, plate_tilt_deg, exit_simulation
    
    # Initialize positions and weld alignment
    reset_simulation()
    
    # Start the CLI input listener thread
    listener_thread = threading.Thread(target=input_listener, daemon=True)
    listener_thread.start()
    
    print("Launching MuJoCo passive viewer window...")
    with mujoco.viewer.launch_passive(model, data) as viewer:
        sim_start_time = data.time
        last_fps_time = time.time()
        fps_counter = 0

        while viewer.is_simulation_running() if hasattr(viewer, 'is_simulation_running') else viewer.is_running() and not exit_simulation:
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
            
            # Calculate ball velocity relative to plate along Y channel (finite differences)
            ball_y_vel = (ball_y_pos - prev_ball_y) / dt
            prev_ball_y = ball_y_pos
            
            # 2. PD control to compute see-saw elbow targets
            ball_error = ball_y_pos - target_ball_y
            
            # PD see-saw command (delta)
            kd = 0.85  # Derivative feedback gain to actively dampen oscillations
            delta = feedback_gain * ball_error + kd * ball_y_vel
            
            # 3. Lock all joints at prerun angles except elbows
            for name in MOTOR_JOINTS:
                q_targets[name] = q_prerun[name]
                
            # Set elbow joints directly to execute the see-saw
            q_targets['l_el_pitch'] = q_prerun['l_el_pitch'] - delta
            q_targets['r_el_pitch'] = q_prerun['r_el_pitch'] - delta  # Same sign change results in mirrored see-saw
            
            # Clamp elbow pitch targets to physical joint limits
            q_targets['l_el_pitch'] = np.clip(q_targets['l_el_pitch'], model.joint('l_el_pitch').range[0], model.joint('l_el_pitch').range[1])
            q_targets['r_el_pitch'] = np.clip(q_targets['r_el_pitch'], model.joint('r_el_pitch').range[0], model.joint('r_el_pitch').range[1])
            
            # 4. Joint-space control (Elbows are active, shoulder pitch & roll are kinematic/frozen, yaws & wrists are passive)
            for name in MOTOR_JOINTS:
                if 'sho_pitch' in name or 'sho_roll' in name:
                    # Kinematic locked joints (zero command torque, state is overwritten below)
                    data.ctrl[actuator_indices[name + "_act"]] = 0.0
                elif 'el_pitch' in name:
                    # Active elbow control
                    error_joint = q_targets[name] - data.qpos[joint_qpos_adr[name]]
                    vel_joint = data.qvel[joint_qvel_adr[name]]
                    torque = pids[name].update(error_joint, vel_joint, dt)
                    bias_torque = data.qfrc_bias[joint_qvel_adr[name]]
                    data.ctrl[actuator_indices[name + "_act"]] = torque + bias_torque
                else:
                    # Passive joints (sho_yaw, forearm_yaw, wrist_pitch, wrist_yaw)
                    data.ctrl[actuator_indices[name + "_act"]] = data.qfrc_bias[joint_qvel_adr[name]]
                
            # Grippers holding plate (0.10 rad closed position to snugly grasp the handles)
            data.ctrl[actuator_indices['l_gripper_l_act']] = 0.10
            data.ctrl[actuator_indices['l_gripper_r_act']] = 0.10
            data.ctrl[actuator_indices['r_gripper_l_act']] = 0.10
            data.ctrl[actuator_indices['r_gripper_r_act']] = 0.10
            
            # Ball tracking head control (Eyes look at the ball in real time!)
            head_pos = data.body('head_tilt_link').xpos.copy()
            dx_head = pos_ball[0] - head_pos[0]
            dy_head = pos_ball[1] - head_pos[1]
            dz_head = pos_ball[2] - head_pos[2]
            head_yaw_target = np.clip(np.arctan2(dy_head, dx_head), -1.57, 1.57)
            head_tilt_target = np.clip(np.arctan2(-dz_head, np.sqrt(dx_head**2 + dy_head**2)), -0.8, 0.8)
            data.ctrl[actuator_indices['head_yaw_act']] = head_yaw_target
            data.ctrl[actuator_indices['head_tilt_act']] = head_tilt_target
            
            # Hard-lock shoulder pitch and roll in state to guarantee absolute rigidity
            for name in MOTOR_JOINTS:
                if 'sho_pitch' in name or 'sho_roll' in name:
                    data.qpos[joint_qpos_adr[name]] = q_prerun[name]
                    data.qvel[joint_qvel_adr[name]] = 0.0

            # Step physics applying perturb forces if user is dragging objects in GUI
            with viewer.lock():
                data.xfrc_applied[:] = 0
                mujoco.mjv_applyPerturbForce(model, data, viewer.perturb)
                mujoco.mjv_applyPerturbPose(model, data, viewer.perturb, 0)
            mujoco.mj_step(model, data)
            
            # Measure actual plate tilt in degrees
            plate_tilt_deg = np.degrees(np.arctan2(R_plate[2, 1], R_plate[2, 2]))
            
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
