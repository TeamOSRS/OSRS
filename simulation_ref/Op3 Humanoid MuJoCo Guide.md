# Robotis OP3 Humanoid MuJoCo Simulation Guide

This guide provides the complete blueprint for setting up, parameterizing, and running a physics-based simulation of the **Robotis OP3** humanoid robot in MuJoCo. It contains link lengths, dynamic specs (mass and inertia), joint limits, actuators, MJCF configuration models, and a Python control template.

---

## 1. Kinematic Structure & Link Lengths

The Robotis OP3 is a miniature humanoid robot standing approximately **340 mm (34 cm) tall**. Its kinematics are modeled in a hierarchical tree starting from the torso center of mass (`body_link`).

Below are the calculated link lengths and joint offsets derived from the default MJCF coordinates.

| Body Link / Joint | Relative Offset Coordinates (X, Y, Z) [meters] | Calculated Physical Length [mm] | Description / Joint Axes |
| :--- | :--- | :--- | :--- |
| **Torso Base** (`body_link`) | `[0.0, 0.0, 0.3]` (World Pos) | — | Base root coordinate (300 mm above ground) |
| **Neck Height** | `[-0.001, 0.0, 0.1365]` | **136.5 mm** | Vertical distance from torso origin to Head Pan |
| **Head Offset** | `[0.01, 0.019, 0.0285]` | **35.6 mm** | Distance from Head Pan to Head Tilt pivot |
| **Shoulder Spacing** | `[-0.001, ±0.060, 0.111]` | **60.0 mm** (Y) / **111.0 mm** (Z) | Distance from torso center to Shoulder Pitch axis |
| **Upper Arm Length** | `[0.019, ±0.0285, -0.010]` | **35.6 mm** | Offset from Shoulder Pitch to Shoulder Roll axis |
| **Forearm Length** | `[0.0, ±0.0904, -0.0001]` | **90.4 mm** | Distance from Shoulder Roll to Elbow axis |
| **Hip Lateral Spacing** | `[0.0, ±0.035, 0.0]` | **35.0 mm** (Y) | Distance from torso center to Hip Yaw pivot |
| **Hip Roll Offset** | `[-0.024, 0.0, -0.0285]` | **37.3 mm** | Offset from Hip Yaw to Hip Roll axis |
| **Thigh (Upper Leg)** | `[0.0, 0.0, -0.11015]` | **110.15 mm** (Z) | Distance from Hip Pitch axis to Knee axis |
| **Calf (Lower Leg)** | `[0.0, 0.0, -0.11000]` | **110.00 mm** (Z) | Distance from Knee axis to Ankle Pitch axis |
| **Ankle Roll Offset** | `[-0.0241, ∓0.019, 0.0]` | **30.7 mm** | Offset from Ankle Pitch to Ankle Roll axis |
| **Foot Height** | `[0.024, ±0.013, -0.0265]` | **26.5 mm** (Z) | Vertical distance from Ankle Roll axis to sole plate |

### Foot Footprint Dimensions
The soles are modeled as dual collision planes with size bounds:
- **Primary boundary**: Length = **127 mm** (`size="0.0635 0.028 0.004"`, total X footprint) x Width = **56 mm** (total Y footprint)
- **Secondary boundary**: Length = **114 mm** x Width = **78 mm** (widened heel section)

---

## 2. Dynamic Parameters (Mass & Inertia)

The OP3 has a total physical mass of **3.147 kg**. The mass is distributed across links to match center-of-mass (CoM) profiles.

### Component Mass Breakdown

| Link Name | Mass [kg] | Coordinates of CoM (X, Y, Z) [meters] |
| :--- | :--- | :--- |
| **Torso Body** (`body_link`) | `1.34928` | `[-0.01501, 0.00013, 0.06582]` |
| **Head Pan Link** | `0.01176` | `[0.00233, 0.00000, 0.00823]` |
| **Head Tilt Link** (Camera) | `0.13631` | `[0.00230, -0.01863, 0.02770]` |
| **Left / Right Shoulder Pitch** | `0.01176` | `[0.00000, ±0.00823, -0.00233]` |
| **Left / Right Shoulder Roll** | `0.17758` | `[-0.01844, ±0.04514, 0.00028]` |
| **Left / Right Elbow Link** | `0.04127` | `[-0.01900, ±0.07033, 0.00380]` |
| **Left / Right Hip Yaw** | `0.01181` | `[-0.00157, 0.00000, -0.00774]` |
| **Left / Right Hip Roll** | `0.17886` | `[0.00388, ±0.00028, -0.01214]` |
| **Left / Right Hip Pitch** | `0.11543` | `[0.00059, ±0.01901, -0.08408]` |
| **Left / Right Knee Link** | `0.04015` | `[0.00000, ±0.02151, -0.05500]` |
| **Left / Right Ankle Pitch** | `0.17886` | `[-0.02022, ∓0.01872, 0.01214]` |
| **Left / Right Ankle Roll** (Foot) | `0.06934` | `[0.02373, ±0.01037, -0.02760]` |

---

## 3. Joint Dynamics & Actuator Parameters

The joint parameters match the physical characteristics of **Dynamixel XM430** and **XL430** servos.

### MJCF Default Configuration Rules
```xml
<default>
  <joint damping="1.084" armature="0.045" frictionloss="0.03"/>
  <position kp="21.1" ctrlrange="-3.141592 3.141592" forcerange="-5 5"/>
</default>
```

- **Damping (`1.084 Ns/m`)**: Regulates high-frequency oscillations during walking impacts.
- **Armature (`0.045 kg·m²`)**: Simulates rotor inertia from gear trains.
- **Friction Loss (`0.03 Nm`)**: Simulates internal friction of Dynamixel gears.
- **Proportional Gain (`kp = 21.1`)**: Emulates position-servo feedback loop stiffness.
- **Torque Limit (`forcerange="-5 5"`)**: Restricts maximum torque to **±5.0 Nm** (aligning with physical Dynamixel stall ranges).

---

## 4. XML Model Schematics

MuJoCo simulations split the description into two files:
1. **`op3.xml`**: Defines the physical humanoid links, mass properties, joints, visual mesh files, and position actuators.
2. **`scene.xml`**: Wraps the robot model with environment assets (ground plane floor texture, skyboxes, default directional lighting, and shadows).

> [!NOTE]
> The complete file contents for both models are already stored in:
> - Robot Model: [op3.xml](file:///E:/Simulation/ARMMM/robotis_mujoco_menagerie/robotis_op3/op3.xml)
> - Scene File: [scene.xml](file:///E:/Simulation/ARMMM/robotis_mujoco_menagerie/robotis_op3/scene.xml)

---

## 5. Running the Simulation

You can run the simulation using either the interactive MuJoCo GUI or via Python scripts.

### Option A: Interactive MuJoCo GUI
If you have MuJoCo installed on your system, you can inspect and interact with the robot in the GUI using the terminal command:
```powershell
simulate E:\Simulation\ARMMM\robotis_mujoco_menagerie\robotis_op3\scene.xml
```

### Option B: Python Simulation Script
Install the required packages:
```bash
pip install mujoco mujoco-python-viewer numpy
```

Use this Python template to launch the simulation programmatically and command joint positions:

```python
import mujoco
import mujoco.viewer
import numpy as np
import time

# 1. Path to model XML
xml_path = r"E:\Simulation\ARMMM\robotis_mujoco_menagerie\robotis_op3\scene.xml"

# 2. Load model & data
model = mujoco.MjModel.from_xml_path(xml_path)
data = mujoco.MjData(model)

# 3. Get joint/actuator indices mapping
actuator_names = [model.actuator(i).name for i in range(model.nu)]
print(f"Loaded {len(actuator_names)} Actuators: {actuator_names}")

# Start passive viewer thread
with mujoco.viewer.launch_passive(model, data) as viewer:
    start_time = time.time()
    
    while viewer.is_running():
        step_start = time.time()
        elapsed = step_start - start_time
        
        # 4. Control policy: Send a sine wave to left/right knees
        # Actuators: 'l_knee_act' (index 11) and 'r_knee_act' (index 17)
        knee_target = 0.4 * np.sin(2 * np.pi * 0.5 * elapsed) # 0.5 Hz oscillation
        
        # Reset control inputs
        data.ctrl[:] = 0.0
        
        # Set specific targets
        if 'l_knee_act' in actuator_names:
            l_knee_idx = actuator_names.index('l_knee_act')
            data.ctrl[l_knee_idx] = knee_target
        if 'r_knee_act' in actuator_names:
            r_knee_idx = actuator_names.index('r_knee_act')
            data.ctrl[r_knee_idx] = -knee_target # out-of-phase for stepping motion
            
        # 5. Physics step (default timestep: 2ms)
        mujoco.mj_step(model, data)
        
        # 6. Render sync
        viewer.sync()
        
        # Maintain real-time speed constraints
        time_to_sleep = model.opt.timestep - (time.time() - step_start)
        if time_to_sleep > 0:
            time.sleep(time_to_sleep)
```
