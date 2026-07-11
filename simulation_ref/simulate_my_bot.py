import mujoco
import mujoco.viewer
import numpy as np
import time
import threading
import sys
import os
import argparse

# Path to the custom robot scene XML
XML_PATH = r"E:\Projects\HumanoidV1\my_bot_scene.xml"

# Check if file exists
if not os.path.exists(XML_PATH):
    print(f"Error: XML scene file not found at: {XML_PATH}")
    sys.exit(1)

# Map mode strings to mode values
MODE_MAP = {
    "manual": "0", "0": "0",
    "home": "1", "1": "1",
    "wave": "2", "2": "2",
    "scan": "3", "3": "3",
    "grasp": "4", "4": "4",
    "taichi": "5", "5": "5",
    "handshake": "6", "6": "6"
}

# Parse command line arguments
parser = argparse.ArgumentParser(description="Custom 18-DOF Humanoid MuJoCo Simulation (IK & PID)")
parser.add_argument("-m", "--mode", type=str, default="manual", 
                    choices=list(MODE_MAP.keys()),
                    help="Initial simulation mode (default: manual)")
args = parser.parse_args()

# Control State
active_mode = MODE_MAP.get(args.mode.lower(), "0")
exit_simulation = False
elapsed_time = 0.0
fps = 0.0
base_pos = np.zeros(3)

# Load model & data
try:
    model = mujoco.MjModel.from_xml_path(XML_PATH)
    data = mujoco.MjData(model)
    kin_data = mujoco.MjData(model)
except Exception as e:
    print(f"Failed to load MuJoCo model: {e}")
    sys.exit(1)

# Get joint/actuator indices mapping
actuator_names = [model.actuator(i).name for i in range(model.nu)]
actuator_indices = {model.actuator(i).name: i for i in range(model.nu)}

# Joint Lists
LEFT_ARM_JOINTS = ['l_sho_pitch', 'l_sho_roll', 'l_sho_yaw', 'l_el_pitch', 'l_forearm_yaw', 'l_wrist_pitch', 'l_wrist_yaw']
RIGHT_ARM_JOINTS = ['r_sho_pitch', 'r_sho_roll', 'r_sho_yaw', 'r_el_pitch', 'r_forearm_yaw', 'r_wrist_pitch', 'r_wrist_yaw']
MOTOR_JOINTS = LEFT_ARM_JOINTS + RIGHT_ARM_JOINTS

# Map joint names to their velocity/configuration addresses
joint_qpos_adr = {name: model.joint(name).qposadr[0] for name in MOTOR_JOINTS}
joint_qvel_adr = {name: model.joint(name).dofadr[0] for name in MOTOR_JOINTS}

# PID Controller implementation
class PIDController:
    def __init__(self, kp, ki, kd, limit=12.0, windup=4.0):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.limit = limit
        self.windup = windup
        self.integral = 0.0
        self.prev_error = 0.0
        
    def update(self, error, dt):
        self.integral += error * dt
        # Clamp integral to prevent windup
        self.integral = np.clip(self.integral, -self.windup, self.windup)
        
        derivative = (error - self.prev_error) / dt if dt > 0.0 else 0.0
        self.prev_error = error
        
        output = self.kp * error + self.ki * self.integral + self.kd * derivative
        return np.clip(output, -self.limit, self.limit)

    def reset(self):
        self.integral = 0.0
        self.prev_error = 0.0

# Initialize PID controllers for J1-J7 of both arms (Torque controlled)
# Tuned for Dynamixel XM430 load profiles
pids = {name: PIDController(kp=120.0, ki=6.0, kd=5.0, limit=12.0, windup=6.0) for name in MOTOR_JOINTS}

# Default joint posture targets (Home pose)
q_targets = {name: 0.0 for name in MOTOR_JOINTS}
q_targets['l_sho_pitch'] = 0.5
q_targets['r_sho_pitch'] = 0.5
q_targets['l_sho_roll'] = 0.15
q_targets['r_sho_roll'] = 0.15
q_targets['l_el_pitch'] = -0.8
q_targets['r_el_pitch'] = -0.8

# Gripper state targets (0.0: closed, 0.8: open)
l_gripper_target = 0.0
r_gripper_target = 0.0

# Mocap targets home positions
L_MOCAP_HOME = np.array([0.15, 0.22, 0.75])
R_MOCAP_HOME = np.array([0.15, -0.22, 0.75])

# Helper for quaternion multiplication (q1 * q2)
def quat_mul(q1, q2):
    w1, x1, y1, z1 = q1
    w2, x2, y2, z2 = q2
    return np.array([
        w1*w2 - x1*x2 - y1*y2 - z1*z2,
        w1*x2 + x1*w2 + y1*z2 - z1*y2,
        w1*y2 - x1*z2 + y1*w2 + z1*x2,
        w1*z2 + x1*y2 - y1*x2 + z1*w2
    ])

# Helper for quaternion inverse
def quat_inv(q):
    return np.array([q[0], -q[1], -q[2], -q[3]])

# Solve 7-DOF Damped Least Squares IK for one arm
def solve_arm_ik(site_name, target_pos, target_quat, arm_joints, damping=0.03, step_scale=0.1):
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
    
    # Compute translational error
    pos_err = target_pos - current_pos
    
    # Compute rotational error vector
    # q_err = target * inv(current)
    q_err = quat_mul(target_quat, quat_inv(current_quat))
    # Angular velocity error representation: 2 * im(q_err) * sign(re(q_err))
    rot_err = 2.0 * q_err[1:4] * np.sign(q_err[0])
    
    # Combine into 6D Cartesian error vector
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
        # Fall back to transpose in case of numerical instability
        dq = J_arm.T @ dx * 0.1
        
    # 6. Apply step update to target joint positions (clamped to limits)
    for i, name in enumerate(arm_joints):
        q_targets[name] += dq[i] * step_scale
        joint_range = model.joint(name).range
        q_targets[name] = np.clip(q_targets[name], joint_range[0], joint_range[1])

# Reset Mocap Bodies to home position and quaternions
def reset_mocap_targets():
    l_mocap_id = model.body('l_target').mocapid[0]
    r_mocap_id = model.body('r_target').mocapid[0]
    
    data.mocap_pos[l_mocap_id] = L_MOCAP_HOME.copy()
    data.mocap_quat[l_mocap_id] = np.array([1.0, 0.0, 0.0, 0.0])
    
    data.mocap_pos[r_mocap_id] = R_MOCAP_HOME.copy()
    data.mocap_quat[r_mocap_id] = np.array([1.0, 0.0, 0.0, 0.0])
    
    # Reset PID integrals
    for pid in pids.values():
        pid.reset()

# Reset joint positions directly to home configuration
def reset_joints_to_home():
    global l_gripper_target, r_gripper_target
    
    q_targets['l_sho_pitch'] = 0.5
    q_targets['r_sho_pitch'] = 0.5
    q_targets['l_sho_roll'] = 0.15
    q_targets['r_sho_roll'] = 0.15
    q_targets['l_el_pitch'] = -0.8
    q_targets['r_el_pitch'] = -0.8
    for name in ['l_sho_yaw', 'l_forearm_yaw', 'l_wrist_pitch', 'l_wrist_yaw',
                 'r_sho_yaw', 'r_forearm_yaw', 'r_wrist_pitch', 'r_wrist_yaw']:
        q_targets[name] = 0.0
        
    l_gripper_target = 0.0
    r_gripper_target = 0.0
    
    # Set model position state
    for name in MOTOR_JOINTS:
        data.qpos[joint_qpos_adr[name]] = q_targets[name]
        data.qvel[joint_qvel_adr[name]] = 0.0
        kin_data.qpos[joint_qpos_adr[name]] = q_targets[name]
        kin_data.qvel[joint_qvel_adr[name]] = 0.0
        
    # Grippers
    for g_joint in ['l_finger_l_joint', 'l_finger_r_joint', 'r_finger_l_joint', 'r_finger_r_joint']:
        qpos_adr = model.joint(g_joint).qposadr[0]
        data.qpos[qpos_adr] = 0.0
        kin_data.qpos[qpos_adr] = 0.0
    
    reset_mocap_targets()

# Update the mocap targets trajectory according to the mode
def update_trajectories(mode, t):
    global l_gripper_target, r_gripper_target
    
    l_mocap_id = model.body('l_target').mocapid[0]
    r_mocap_id = model.body('r_target').mocapid[0]
    
    if mode == "0":  # MANUAL / INTERACTIVE
        # Mocap position is updated by user via mouse drag in GUI
        pass
        
    elif mode == "1":  # HOME
        # Interpolate targets back to home
        data.mocap_pos[l_mocap_id] = L_MOCAP_HOME
        data.mocap_pos[r_mocap_id] = R_MOCAP_HOME
        l_gripper_target = 0.0
        r_gripper_target = 0.0
        
    elif mode == "2":  # WAVE HAND
        # Left hand traces a waving path in Y-Z plane
        phi = 2 * np.pi * 1.5 * t
        data.mocap_pos[l_mocap_id] = L_MOCAP_HOME + np.array([0.05, 0.05, 0.15 + 0.08 * np.sin(phi)])
        # Turn head to look towards the left target
        data.ctrl[actuator_indices['head_yaw_act']] = 0.35
        data.ctrl[actuator_indices['head_tilt_act']] = -0.1
        
    elif mode == "3":  # HEAD SCAN (yaw and tilt sweeps)
        data.mocap_pos[l_mocap_id] = L_MOCAP_HOME
        data.mocap_pos[r_mocap_id] = R_MOCAP_HOME
        
        phi_yaw = 2 * np.pi * 0.2 * t
        phi_tilt = 2 * np.pi * 0.4 * t
        data.ctrl[actuator_indices['head_yaw_act']] = 0.8 * np.sin(phi_yaw)
        data.ctrl[actuator_indices['head_tilt_act']] = 0.3 * np.cos(phi_tilt)
        
    elif mode == "4":  # GRASP DEMO (Reach, close, lift, reset loop)
        cycle = t % 6.0
        
        if cycle < 2.0:  # Reach forward and open grippers
            s = cycle / 2.0
            data.mocap_pos[l_mocap_id] = L_MOCAP_HOME + np.array([0.12 * s, 0.0, -0.05 * s])
            data.mocap_pos[r_mocap_id] = R_MOCAP_HOME + np.array([0.12 * s, 0.0, -0.05 * s])
            l_gripper_target = 0.8  # Open
            r_gripper_target = 0.8
        elif cycle < 3.0:  # Close fingers/pinch
            data.mocap_pos[l_mocap_id] = L_MOCAP_HOME + np.array([0.12, 0.0, -0.05])
            data.mocap_pos[r_mocap_id] = R_MOCAP_HOME + np.array([0.12, 0.0, -0.05])
            l_gripper_target = 0.0  # Close
            r_gripper_target = 0.0
        elif cycle < 5.0:  # Lift objects up
            s = (cycle - 3.0) / 2.0
            data.mocap_pos[l_mocap_id] = L_MOCAP_HOME + np.array([0.12 * (1-0.3*s), 0.0, -0.05 + 0.12*s])
            data.mocap_pos[r_mocap_id] = R_MOCAP_HOME + np.array([0.12 * (1-0.3*s), 0.0, -0.05 + 0.12*s])
            l_gripper_target = 0.0
            r_gripper_target = 0.0
        else:  # Reset to home
            s = (cycle - 5.0)
            data.mocap_pos[l_mocap_id] = L_MOCAP_HOME + np.array([0.08 * (1-s), 0.0, 0.07 * (1-s)])
            data.mocap_pos[r_mocap_id] = R_MOCAP_HOME + np.array([0.08 * (1-s), 0.0, 0.07 * (1-s)])
            l_gripper_target = 0.8 * s  # Release
            r_gripper_target = 0.8 * s

    elif mode == "5":  # TAI CHI (Coordination circle tracking)
        omega = 2 * np.pi * 0.15 * t  # Slow circular orbits
        
        # Out of phase circular paths
        data.mocap_pos[l_mocap_id] = L_MOCAP_HOME + np.array([0.08 * np.sin(omega), 0.05 * np.cos(omega), 0.06 * np.sin(omega)])
        data.mocap_pos[r_mocap_id] = R_MOCAP_HOME + np.array([0.08 * np.sin(omega + np.pi), 0.05 * np.cos(omega + np.pi), 0.06 * np.sin(omega + np.pi)])
        
        # Head tracks left hand
        l_pos = data.mocap_pos[l_mocap_id]
        data.ctrl[actuator_indices['head_yaw_act']] = 0.3 * np.sin(omega)
        data.ctrl[actuator_indices['head_tilt_act']] = 0.1 * np.cos(omega)
        
    elif mode == "6":  # HANDSHAKE
        # Right hand moves forward and shakes
        data.mocap_pos[l_mocap_id] = L_MOCAP_HOME
        
        phi = 2 * np.pi * 1.5 * t
        data.mocap_pos[r_mocap_id] = R_MOCAP_HOME + np.array([0.15, 0.03, -0.05 + 0.03 * np.sin(phi)])
        
# Command listener thread
def input_listener():
    global active_mode, exit_simulation
    print_menu()
    while not exit_simulation:
        try:
            val = input().strip()
            if not val:
                continue
            if val.lower() in ['q', 'quit', 'exit']:
                exit_simulation = True
                break
            elif val in [str(i) for i in range(len(MODE_MAP))]:
                active_mode = val
                reset_mocap_targets()
                print_status()
            elif val.lower() in list(MODE_MAP.keys()):
                active_mode = MODE_MAP[val.lower()]
                reset_mocap_targets()
                print_status()
            elif val.lower() in ["t", "status", "telemetry"]:
                print_status()
            elif val.lower() in ["h", "help", "menu"]:
                print_menu()
            elif val.lower() in ["r", "reset"]:
                reset_joints_to_home()
                print("\n[RESET] Restored to home pose.")
                print("Enter command: ", end="", flush=True)
            else:
                print(f"Unknown command '{val}'. Type 'h' for menu, 'q' to quit.")
        except EOFError:
            print("\nNon-interactive environment (EOF) detected. CLI inputs disabled.")
            print(f"Simulation is running continuously in Mode: {get_mode_name(active_mode)}")
            print("Close the MuJoCo GUI window or terminate the process to exit.")
            break
        except KeyboardInterrupt:
            exit_simulation = True
            break

def get_mode_name(mode_val):
    mode_names = {
        "0": "MANUAL / INTERACTIVE TARGETS",
        "1": "HOME / READY POSTURE",
        "2": "WAVE HAND (IK)",
        "3": "HEAD SCAN",
        "4": "GRASP DEMO (IK)",
        "5": "TAI CHI CIRCLES (IK)",
        "6": "HANDSHAKE SHAKE (IK)"
    }
    return mode_names.get(mode_val, "UNKNOWN")

def print_menu():
    print("\n" + "="*60)
    print(" CUSTOM 18-DOF ROBOT MUJOCO INTERACTIVE SIMULATION")
    print(" (INVERSE KINEMATICS & PYTHON PID TORQUE CONTROL)")
    print("="*60)
    print(" Select Simulation Mode (Type number or name):")
    print("   0 / manual   : Manual Target Control (Drag green/red target spheres in GUI)")
    print("   1 / home     : Stand Still (Target tracking at home pose)")
    print("   2 / wave     : Wave Hand (IK tracking loop)")
    print("   3 / scan     : Head Scan (Yaw/Tilt sweeping)")
    print("   4 / grasp    : Grasp Demo (Reach, Pinch, Lift, Release IK loop)")
    print("   5 / taichi   : Tai Chi Coordinated Circle tracking")
    print("   6 / handshake: Handshake Shake (IK tracking)")
    print("   r / reset    : Reset joints directly to home posture")
    print("   t / status   : Print Current Telemetry")
    print("   h / menu     : Show This Menu")
    print("   q / quit     : Exit Simulation")
    print("="*60)
    print("Control Tips:")
    print("  - To drag targets in manual mode: Hold CTRL and Right-Click & Drag the green/red target sphere.")
    print("="*60)
    print("Enter command: ", end="", flush=True)

def print_status():
    print("\n" + "-"*40)
    print(f" [MODE CHANGE] Active Mode: {get_mode_name(active_mode)}")
    print(f" [TELEMETRY]   Sim Time:    {elapsed_time:.2f} s")
    print(f" [TELEMETRY]   Base CoM:    X={base_pos[0]:.3f}m, Y={base_pos[1]:.3f}m, Z={base_pos[2]:.3f}m")
    print(f" [TELEMETRY]   Realtime:    {fps:.1f} Hz (target: {1.0/model.opt.timestep:.0f} Hz)")
    print("-"*40)
    if active_mode == "0":
        print(" [MANUAL MODE] Drag the green/red mocap target spheres in the MuJoCo window.")
        print("               The arms will track them in real time using Jacobian IK + PID torque.")
        print("-"*40)
    print("Enter command: ", end="", flush=True)

def main():
    global elapsed_time, fps, base_pos, exit_simulation, l_gripper_target, r_gripper_target
    
    # Initialize joint positions and reset mocap bodies
    reset_joints_to_home()
    
    # Start the CLI input listener in a separate thread
    listener_thread = threading.Thread(target=input_listener, daemon=True)
    listener_thread.start()
    
    # Launch passive viewer
    print("Launching MuJoCo passive viewer window...")
    with mujoco.viewer.launch_passive(model, data) as viewer:
        start_time = time.time()
        sim_start_time = data.time
        
        last_fps_time = time.time()
        fps_counter = 0
        
        while viewer.is_running() and not exit_simulation:
            step_start = time.time()
            dt = model.opt.timestep  # dt = 0.002s
            
            # Get current simulation time
            elapsed_time = data.time - sim_start_time
            
            # 1. Update targets and trajectories based on active mode
            update_trajectories(active_mode, elapsed_time)
            
            # 2. Compute 7-DOF Jacobian Inverse Kinematics for Left & Right Arms
            l_mocap_id = model.body('l_target').mocapid[0]
            l_target_pos = data.mocap_pos[l_mocap_id].copy()
            l_target_quat = data.mocap_quat[l_mocap_id].copy()
            solve_arm_ik('l_eef', l_target_pos, l_target_quat, LEFT_ARM_JOINTS)
            
            r_mocap_id = model.body('r_target').mocapid[0]
            r_target_pos = data.mocap_pos[r_mocap_id].copy()
            r_target_quat = data.mocap_quat[r_mocap_id].copy()
            solve_arm_ik('r_eef', r_target_pos, r_target_quat, RIGHT_ARM_JOINTS)
            
            # 3. Apply custom joint-space PID torque control to J1-J7
            for name in MOTOR_JOINTS:
                qpos_adr = joint_qpos_adr[name]
                qvel_adr = joint_qvel_adr[name]
                
                # Compute error: q_target - q_current
                error = q_targets[name] - data.qpos[qpos_adr]
                
                # Compute feedback torque via Python PID
                torque = pids[name].update(error, dt)
                
                # Command actuator torque directly (motor actuator J1-J7 address is index in data.ctrl)
                actuator_idx = actuator_indices[name + "_act"]
                data.ctrl[actuator_idx] = torque
                
            # 4. Command position actuators for grippers (PD control handled natively in MuJoCo)
            data.ctrl[actuator_indices['l_gripper_l_act']] = l_gripper_target
            data.ctrl[actuator_indices['l_gripper_r_act']] = l_gripper_target
            data.ctrl[actuator_indices['r_gripper_l_act']] = r_gripper_target
            data.ctrl[actuator_indices['r_gripper_r_act']] = r_gripper_target
            
            # Head position actuators (if not modified by scan/wave mode, they hold home)
            if active_mode not in ["2", "3", "5"]:
                data.ctrl[actuator_indices['head_yaw_act']] = 0.0
                data.ctrl[actuator_indices['head_tilt_act']] = 0.0
            
            # Step physics
            mujoco.mj_step(model, data)
            
            # Sync passive viewer
            viewer.sync()
            
            # Update telemetry data for background printer
            base_pos = data.qpos[0:3].copy() if len(data.qpos) >= 3 else np.zeros(3)
            
            # Calculate FPS / real step rate
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
