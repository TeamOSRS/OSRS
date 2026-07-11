import mujoco
import mujoco.viewer
import numpy as np
import time
import threading
import sys
import os
import argparse

# Absolute path to the scene file (provided in the guide)
XML_PATH = r"E:\Simulation\ARMMM\robotis_mujoco_menagerie\robotis_op3\scene.xml"

# Check if file exists
if not os.path.exists(XML_PATH):
    print(f"Error: XML scene file not found at: {XML_PATH}")
    print("Please verify the path or make sure MuJoCo assets are installed correctly.")
    sys.exit(1)

# Map mode strings to mode values
MODE_MAP = {
    "manual": "0", "0": "0",
    "stand": "1", "1": "1",
    "step": "2", "2": "2",
    "walk": "3", "3": "3",
    "squat": "4", "4": "4",
    "wave": "5", "5": "5",
    "guide": "6", "6": "6"
}

# Parse command line arguments
parser = argparse.ArgumentParser(description="Robotis OP3 MuJoCo Interactive Simulation")
parser.add_argument("-m", "--mode", type=str, default="manual", 
                    choices=list(MODE_MAP.keys()),
                    help="Initial simulation mode (default: manual)")
args = parser.parse_args()

# Motion Parameters (Tuned for stability and visual quality)
WALK_FREQ = 1.25        # Hz
WALK_ROLL_AMP = 0.05    # rad, lateral weight shifting amplitude
WALK_KNEE_AMP = 0.35    # rad, knee bending amplitude
WALK_SWING_AMP = 0.12   # rad, leg swing forward/backward amplitude
WALK_KNEE_OFFSET = 0.15 # rad, default knee bend for stability

SQUAT_FREQ = 0.5        # Hz
SQUAT_AMP = 0.4         # rad, squat depth amplitude

WAVE_FREQ = 2.0         # Hz
WAVE_AMP = 0.4          # rad

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
except Exception as e:
    print(f"Failed to load MuJoCo model: {e}")
    sys.exit(1)

# Get joint/actuator indices mapping
actuator_names = [model.actuator(i).name for i in range(model.nu)]
actuator_indices = {model.actuator(i).name: i for i in range(model.nu)}

# Helper to command a joint by actuator name
def set_ctrl(ctrl_dict, name, val):
    if name in ctrl_dict:
        ctrl_dict[name] = val

def get_control_for_mode(mode, t):
    if mode == "0":  # MANUAL CONTROL
        return None
        
    # Initialize all joint controls to 0.0
    ctrls = {name: 0.0 for name in actuator_names}
    
    # Standing posture offsets (relaxed stand)
    default_knee = WALK_KNEE_OFFSET
    default_hip_pitch = -0.5 * default_knee
    default_ank_pitch = 0.5 * default_knee
    
    # Relaxed arm posture (prevent collision with hips)
    set_ctrl(ctrls, 'l_sho_pitch_act', 0.2)
    set_ctrl(ctrls, 'r_sho_pitch_act', -0.2)
    set_ctrl(ctrls, 'l_el_act', 0.4)
    set_ctrl(ctrls, 'r_el_act', -0.4)
    
    if mode == "1":  # STAND
        # Keep relaxed standing posture
        set_ctrl(ctrls, 'l_knee_act', default_knee)
        set_ctrl(ctrls, 'r_knee_act', -default_knee)  # opposite axis sign
        set_ctrl(ctrls, 'l_hip_pitch_act', default_hip_pitch)
        set_ctrl(ctrls, 'r_hip_pitch_act', -default_hip_pitch)  # opposite axis sign
        set_ctrl(ctrls, 'l_ank_pitch_act', default_ank_pitch)
        set_ctrl(ctrls, 'r_ank_pitch_act', -default_ank_pitch)  # opposite axis sign
        
    elif mode == "1":  # STEP IN PLACE
        # Lateral weight shifting (hip/ankle roll)
        phi = 2 * np.pi * WALK_FREQ * t
        roll = WALK_ROLL_AMP * np.sin(phi)
        
        set_ctrl(ctrls, 'l_hip_roll_act', roll)
        set_ctrl(ctrls, 'r_hip_roll_act', roll)
        set_ctrl(ctrls, 'l_ank_roll_act', -roll)
        set_ctrl(ctrls, 'r_ank_roll_act', -roll)
        
        # Lift foot when weight is shifted to the other side
        # Left leg lifts when roll is positive (shifting to the right)
        l_lift = np.maximum(0.0, roll / WALK_ROLL_AMP)
        r_lift = np.maximum(0.0, -roll / WALK_ROLL_AMP)
        
        l_knee = default_knee + WALK_KNEE_AMP * l_lift
        r_knee = default_knee + WALK_KNEE_AMP * r_lift
        
        set_ctrl(ctrls, 'l_knee_act', l_knee)
        set_ctrl(ctrls, 'r_knee_act', -r_knee)
        set_ctrl(ctrls, 'l_hip_pitch_act', -0.5 * l_knee)
        set_ctrl(ctrls, 'r_hip_pitch_act', 0.5 * r_knee)
        set_ctrl(ctrls, 'l_ank_pitch_act', 0.5 * l_knee)
        set_ctrl(ctrls, 'r_ank_pitch_act', -0.5 * r_knee)
        
    elif mode == "2":  # WALK FORWARD
        phi = 2 * np.pi * WALK_FREQ * t
        roll = WALK_ROLL_AMP * np.sin(phi)
        
        # Lateral weight shifting
        set_ctrl(ctrls, 'l_hip_roll_act', roll)
        set_ctrl(ctrls, 'r_hip_roll_act', roll)
        set_ctrl(ctrls, 'l_ank_roll_act', -roll)
        set_ctrl(ctrls, 'r_ank_roll_act', -roll)
        
        # Lift foot
        l_lift = np.maximum(0.0, roll / WALK_ROLL_AMP)
        r_lift = np.maximum(0.0, -roll / WALK_ROLL_AMP)
        
        l_knee = default_knee + WALK_KNEE_AMP * l_lift
        r_knee = default_knee + WALK_KNEE_AMP * r_lift
        
        set_ctrl(ctrls, 'l_knee_act', l_knee)
        set_ctrl(ctrls, 'r_knee_act', -r_knee)
        
        # Swing forward/backward
        swing = WALK_SWING_AMP * np.cos(phi)
        
        set_ctrl(ctrls, 'l_hip_pitch_act', -0.5 * l_knee + swing)
        set_ctrl(ctrls, 'r_hip_pitch_act', 0.5 * r_knee + swing) # same physical swing direction
        
        set_ctrl(ctrls, 'l_ank_pitch_act', 0.5 * l_knee - swing)
        set_ctrl(ctrls, 'r_ank_pitch_act', -0.5 * r_knee - swing) # same physical foot correction
        
        # Swing arms out of phase for natural walking gait
        set_ctrl(ctrls, 'l_sho_pitch_act', 0.2 - 0.4 * swing)
        set_ctrl(ctrls, 'r_sho_pitch_act', -0.2 - 0.4 * swing)
        
    elif mode == "3":  # SQUAT
        phi = 2 * np.pi * SQUAT_FREQ * t
        squat_val = SQUAT_AMP * (0.5 - 0.5 * np.cos(phi))
        
        knee = default_knee + squat_val
        set_ctrl(ctrls, 'l_knee_act', knee)
        set_ctrl(ctrls, 'r_knee_act', -knee)
        set_ctrl(ctrls, 'l_hip_pitch_act', -0.5 * knee)
        set_ctrl(ctrls, 'r_hip_pitch_act', 0.5 * knee)
        set_ctrl(ctrls, 'l_ank_pitch_act', 0.5 * knee)
        set_ctrl(ctrls, 'r_ank_pitch_act', -0.5 * knee)
        
    elif mode == "4":  # WAVE
        # Keep standing posture
        set_ctrl(ctrls, 'l_knee_act', default_knee)
        set_ctrl(ctrls, 'r_knee_act', -default_knee)
        set_ctrl(ctrls, 'l_hip_pitch_act', default_hip_pitch)
        set_ctrl(ctrls, 'r_hip_pitch_act', -default_hip_pitch)
        set_ctrl(ctrls, 'l_ank_pitch_act', default_ank_pitch)
        set_ctrl(ctrls, 'r_ank_pitch_act', -default_ank_pitch)
        
        # Left arm waves
        phi = 2 * np.pi * WAVE_FREQ * t
        set_ctrl(ctrls, 'l_sho_pitch_act', 1.8) # Raise arm high
        set_ctrl(ctrls, 'l_sho_roll_act', 0.5 + WAVE_AMP * np.sin(phi)) # Wave side to side
        set_ctrl(ctrls, 'l_el_act', 0.8)
        
    elif mode == "5":  # GUIDE KNEE WAVE
        # Sine wave to left/right knees as described in the guide
        knee_target = 0.4 * np.sin(2 * np.pi * 0.5 * t)
        set_ctrl(ctrls, 'l_knee_act', knee_target)
        set_ctrl(ctrls, 'r_knee_act', -knee_target)
        
    return ctrls

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
                print_status()
            elif val.lower() in list(MODE_MAP.keys()):
                active_mode = MODE_MAP[val.lower()]
                print_status()
            elif val.lower() in ["t", "status", "telemetry"]:
                print_status()
            elif val.lower() in ["h", "help", "menu"]:
                print_menu()
            else:
                print(f"Unknown command '{val}'. Type 'h' for menu, 'q' to quit.")
        except EOFError:
            print("\nNon-interactive environment (EOF) detected. CLI inputs disabled.")
            print(f"Simulation is running continuously in Mode: {get_mode_name(active_mode)}")
            print("To control the simulation, run this script from an interactive terminal.")
            print("Close the MuJoCo GUI window or terminate the process to exit.")
            break
        except KeyboardInterrupt:
            exit_simulation = True
            break

def get_mode_name(mode_val):
    mode_names = {
        "0": "MANUAL CONTROL (GUI SLIDERS)",
        "1": "STAND STILL",
        "2": "STEP IN PLACE",
        "3": "WALK FORWARD",
        "4": "SQUAT MODE",
        "5": "WAVE HAND",
        "6": "GUIDE KNEE WAVE DEMO"
    }
    return mode_names.get(mode_val, "UNKNOWN")

def print_menu():
    print("\n" + "="*60)
    print(" ROBOTIS OP3 MUJOCO INTERACTIVE SIMULATION")
    print("="*60)
    print(" Select Simulation Mode (Type number or name):")
    print("   0 / manual: Manual Control (Use GUI Sliders in MuJoCo)")
    print("   1 / stand : Stand Still (Default Posture)")
    print("   2 / step  : Step In Place")
    print("   3 / walk  : Walk Forward")
    print("   4 / squat : Squat Mode")
    print("   5 / wave  : Wave Hand")
    print("   6 / guide : Guide Knee Wave Demo")
    print("   t / status: Print Current Telemetry")
    print("   h / menu  : Show This Menu")
    print("   q / quit  : Exit Simulation")
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
        print(" [MANUAL MODE] You can now select the 'Control' tab in the MuJoCo GUI")
        print("               and use the sliders to manually adjust each joint.")
        print("-"*40)
    print("Enter command: ", end="", flush=True)

def main():
    global elapsed_time, fps, base_pos, exit_simulation
    
    # Initialize control inputs to stand posture so it starts in a stable stance
    home_ctrls = get_control_for_mode("1", 0.0) # Mode "1" is stand
    if home_ctrls is not None:
        for name, val in home_ctrls.items():
            if name in actuator_indices:
                data.ctrl[actuator_indices[name]] = val
    
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
            
            # Get current simulation time
            elapsed_time = data.time - sim_start_time
            
            # Retrieve active control dictionary
            target_ctrls = get_control_for_mode(active_mode, elapsed_time)
            
            # Apply control dictionary to data.ctrl (if not None/Manual mode)
            if target_ctrls is not None:
                for name, val in target_ctrls.items():
                    if name in actuator_indices:
                        data.ctrl[actuator_indices[name]] = val
            
            # Step physics (default timestep: 2ms)
            mujoco.mj_step(model, data)
            
            # Sync passive viewer
            viewer.sync()
            
            # Update telemetry data for background printer
            base_pos = data.qpos[0:3].copy()
            
            # Calculate FPS / real step rate
            fps_counter += 1
            now = time.time()
            if now - last_fps_time >= 1.0:
                fps = fps_counter / (now - last_fps_time)
                fps_counter = 0
                last_fps_time = now
            
            # Real-time sleep matching
            time_to_sleep = model.opt.timestep - (time.time() - step_start)
            if time_to_sleep > 0:
                time.sleep(time_to_sleep)
                
    exit_simulation = True
    print("\nSimulation ended. Goodbye!")

if __name__ == "__main__":
    main()
