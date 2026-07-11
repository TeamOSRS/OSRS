# OSRS Simulation Reference Mapping

This document details how the control models, coordinate frames, kinematics algorithms, and actuator systems validated in `simulation_ref` map to the modular OSRS architecture, and how they remain separated from the visual Digital Twin assets.

---

## 1. Separation of Concerns Architecture

To allow future high-fidelity CAD meshes and visual assets to be updated seamlessly without breaking control loops, OSRS maintains a strict boundary between the **Control Model** and the **Digital Twin Model**:

```
                  +----------------------------------+
                  |         Robot Module             |
                  |     (e.g., humanoid.py)          |
                  +-----------------+----------------+
                                    |
            +-----------------------+-----------------------+
            |                                               |
            v                                               v
+-----------------------+                       +-----------------------+
|     Control Model     |                       |  Digital Twin Model   |
|   (simulation_ref)    |                       |  (Visual Assets)      |
+-----------+-----------+                       +-----------+-----------+
            |                                               |
            | - Coordinate Systems (ENU/MuJoCo)             | - Mesh geometry / visual body
            | - Kinematics (FK / IK / Jacobians)            | - Loading format (URDF/MJCF/GLTF)
            | - Controllers (PID gains, limits)             | - Cosmetic offsets & scaling
            | - Physics Stepping (MuJoCo XML)               | - Joint transforms and links
            v                                               v
+-----------------------+                       +-----------------------+
|  OSRS Robot Controller|                       |  Three.js 3D Viewer   |
|   & Hardware Drivers  |                       |  (DigitalTwinViewer)  |
+-----------------------+                       +-----------------------+
```

---

## 2. Coordinate Systems & Conventions

* **Primary Coordinate System:** OSRS uses the Right-Handed Coordinate System matching MuJoCo’s default conventions:
  - **+X Axis:** Points **Forward** (anterior)
  - **+Y Axis:** Points **Left** (lateral left)
  - **+Z Axis:** Points **Up** (vertical superior)
  - **Angles:** Expressed in radians, following the right-hand rule (counter-clockwise positive).
* **Sensor Frame Mapping:**
  - Hand landmarks detected via the camera feed (MediaPipe) are normalized to screen coordinates ($x, y$ from $0.0$ to $1.0$).
  - These are mapped to Cartesian coordinates in the robot's end-effector task space or joint angular goals.

---

## 3. Actuator & Joint ID Mappings (OP3 Humanoid Bot)

The following table maps the joints defined in the `simulation_ref/my_bot.xml` MJCF model to the physical/virtual Dynamixel actuator IDs handled by OSRS:

| Motor ID | MJCF Joint Name | OSRS Channel / Short Name | Physical ID | Default Position (ticks) | Min Limit (ticks) | Max Limit (ticks) | Range (rad) | Description |
|---|---|---|---|---|---|---|---|---|
| **11** | `r_sho_pitch` | R1P | 11 | 1674 | -5770 | 2422 | -2.50 to 2.50 | Right Shoulder Pitch |
| **22** | `r_sho_roll` | R2R | 22 | 2138 | -1958 | 6234 | -2.00 to 0.20 | Right Shoulder Roll |
| **23** | `r_sho_yaw` | R3Y | 23 | -1275 | -5371 | 2821 | -1.57 to 1.57 | Right Shoulder Yaw |
| **14** | `r_el_pitch` | R4F | 14 | 4038 | -58 | 8134 | -0.10 to 2.00 | Right Elbow Pitch (Flex) |
| **15** | `r_forearm_yaw` | R5Y | 15 | -995 | -5091 | 3101 | -2.00 to 2.00 | Right Forearm Yaw |
| **16** | `r_wrist_pitch` | R6R | 16 | 4077 | -19 | 8173 | -1.57 to 1.57 | Right Wrist Pitch |
| **17** | `r_wrist_yaw` | R7P | 17 | 74 | -4022 | 4170 | -1.57 to 1.57 | Right Wrist Yaw |
| **18** | `r_finger_l_joint` / `r_finger_r_joint` | R8G | 18 | 983 | -3113 | 5079 | 0.00 to 0.80 | Right Hand Gripper |
| **21** | `l_sho_pitch` | L1P | 21 | -3561 | -7657 | 535 | -2.50 to 2.50 | Left Shoulder Pitch |
| **12** | `l_sho_roll` | L2R | 12 | -162 | -4258 | 3934 | -0.20 to 2.00 | Left Shoulder Roll |
| **13** | `l_sho_yaw` | L3Y | 13 | 4344 | 248 | 8440 | -1.57 to 1.57 | Left Shoulder Yaw |
| **24** | `l_el_pitch` | L4F | 24 | 812 | -3284 | 4908 | -2.00 to 0.10 | Left Elbow Pitch (Flex) |
| **25** | `l_forearm_yaw` | L5Y | 25 | 943 | -3153 | 5039 | -2.00 to 2.00 | Left Forearm Yaw |
| **26** | `l_wrist_pitch` | L6R | 26 | 21 | -4075 | 4117 | -1.57 to 1.57 | Left Wrist Pitch |
| **27** | `l_wrist_yaw` | L7P | 27 | 60 | -4036 | 4156 | -1.57 to 1.57 | Left Wrist Yaw |
| **28** | `l_finger_l_joint` / `l_finger_r_joint` | L8G | 28 | -2676 | -6772 | 1420 | 0.00 to 0.80 | Left Hand Gripper |
| **31** | `head_yaw` | Head Yaw | 31 | 0 | -4096 | 4096 | -1.57 to 1.57 | Head Yaw (L/R) |
| **32** | `head_tilt` | Head Pitch | 32 | 0 | -4096 | 4096 | -0.80 to 0.80 | Head Pitch (U/D) |

*Note: Actuator values map linearly between Dynamixel encoder ticks (0-4095 range represents -pi to +pi radians, or extended multi-turn values for offsets).*

---

## 4. Kinematics & Reference Algorithms

### Forward & Inverse Kinematics
* The kinematics engine implements a **7-DOF Damped Least Squares (DLS)** Inverse Kinematics solver extracted directly from `simulation_ref/balance_plate.py` to command coordinates safely.
* Singularity avoidance is handled by regularizing the Jacobian transpose:
  $$J^* = J^T (J J^T + \lambda^2 I)^{-1}$$
  where $\lambda = 0.01$ is the damping factor preventing velocity explosion near singular configurations.

### Controller Interface
* **Joint Controller:** Default parameters use PID gains configured in the Control Model:
  - $K_p = 120.0$, $K_i = 6.0$, $K_d = 5.0$
* **State Updates:** Hardware state is retrieved at 50Hz and broadcast via WebSockets. Replays use a synchronized timeline slider that updates the virtual model state directly.
