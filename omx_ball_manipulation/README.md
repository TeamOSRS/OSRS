# Stage 1: Dual OpenManipulator-X (OMX) Cooperative Ball Balancing Simulation

This directory contains the complete, self-contained **Stage 1 MuJoCo simulation environment** for cooperative dual-arm plate balancing and ball manipulation using **ROBOTIS OpenManipulator-X (OMX)**.

This simulation represents the foundational first stage of the OSRS active-balancing research, establishing the core Lagrangian rolling-sphere physics, height-based differential Inverse Kinematics (IK), Perspective-n-Point (PnP) multi-camera calibration, and real-time PID stabilization algorithms that later evolved into the full OSRS multi-robot platform.

---

## 1. Research Context & Evolutionary Timeline

The OSRS active ball-balancing research progressed through three distinct architectural stages:

```
[Stage 1: OMX Dual-Arm Simulation]  --->  [Stage 2: Asymmetric Franka/HEAL]  --->  [Stage 3: Physical OSRS Platform]
(omx_ball_manipulation)                    (two_arm_ball_manipulation)             (src/, docs/, frontend/)
- Dual OpenManipulator-X in MuJoCo        - Franka FR3 + HEAL 6-DOF               - ROBOTIS OP3 Torso / Real Dynamixels
- Height-based Delta Z PID Control        - Asymmetric kinematics & workspaces     - Intel RealSense RGB-D tracking
- Rolling sphere Lagrangian physics       - Enhanced disturbance rejection        - Dual 2D Load-Cell RLS sensor fusion
- Camera calibration & solvePnP           - High-payload cooperative grasping      - Real-time React Web Command Center
```

* **Stage 1 (This Package)**: Dual symmetric 4-DOF OpenManipulator-X arms grasping a channel plate via rigid coupler welds in MuJoCo. Proved the viability of differential height-based tilt actuation ($\Delta z$) and established our sensor-to-actuator control loop.
* **Stage 2 (`../two_arm_ball_manipulation`)**: Scaled the simulation to asymmetric industrial arms (Franka Emika FR3 + HEAL arm) with Robotiq grippers.
* **Stage 3 (`../src/` & `../simulation_ref/`)**: Deployed the control architecture onto physical hardware (dual 8-DOF humanoid arms with Dynamixel X-series servos), integrating RealSense computer vision and HX711 strain-gauge load cells.

---

## 2. Mathematical & Physical Principles

Detailed research derivations are provided in the accompanying documentation:
* **[Mathematics, Physics & Control Theory Notes](control_theory_notes.md)**: Derivations of the rolling sphere Lagrangian, DLS numerical IK, and height-based PID control.
* **[Camera Localization & Coordinate Transformation Theory](camera_localization_theory.md)**: Multi-camera PnP calibration, ray-plane intersection, and OpenGL vs. OpenCV coordinate transforms.

### A. Lagrangian Rolling Sphere Dynamics
A solid sphere of mass $m$ and radius $r$ rolling without slipping along a tilted plate of angle $\theta$:
$$\mathcal{L} = T - V = \frac{7}{10}m \dot{x}^2 + m g x \sin\theta$$
$$\ddot{x} = \frac{5}{7}g \sin\theta \approx \frac{5}{7}g \theta \quad (\text{for small angles } \theta)$$

### B. Differential Height-Based Kinematics ($\Delta z \to \theta$)
Instead of directly torquing joints or commanding Cartesian rotations, the dual arms adjust their end-effector grasp slots differentially by $\pm \Delta z$:
$$\Delta z = L_p \sin\theta \implies \theta = \arctan2\left(2\Delta z, d_{\text{plate}}\right)$$
where $L_p = 0.2758\text{ m}$ is the leverage arm length from the plate center, and $d_{\text{plate}} = 2 L_p = 0.5516\text{ m}$ is the distance between left and right grasp slots.

### C. Damped Least-Squares (DLS) Inverse Kinematics
Target end-effector positions $\mathbf{p}_{\text{target}}$ and orientations $\mathbf{R}_{\text{target}}$ are solved iteratively:
$$\Delta \mathbf{q} = \mathbf{J}^T \left(\mathbf{J}\mathbf{J}^T + \lambda^2 \mathbf{I}\right)^{-1} \mathbf{e}$$
with joint command exponential smoothing ($\alpha = 0.25$) to suppress high-frequency motor chattering.

---

## 3. Directory Layout

```
omx_ball_manipulation/
├── README.md                      # This comprehensive documentation guide
├── control_theory_notes.md        # Mathematical, physical, and control theory derivations
├── camera_localization_theory.md  # Multi-camera PnP calibration & coordinate transformation theory
├── simulate_cooperative.py        # Primary dual-arm MuJoCo simulation & interactive PID runner
├── PID.py                         # Standalone discrete PID controller validation benchmark
├── verify_cameras.py              # Multi-camera pose calibration & 3D triangulation (solvePnP)
├── capture_frame.py               # Camera snapshot utility
├── fk_check.py                    # Forward kinematics consistency verification script
├── record_video.py                # Headless video renderer for simulation runs
├── dual_scene.xml                 # MuJoCo world scene (dual arms, plate, ball, cameras, floor)
├── dual_open_manipulator_x.xml    # Dual arm kinematic base, constraints, and home keyframe
├── dual_arms.xml                  # Left and right OpenManipulator-X body trees & actuators
├── plate_assembly.xml             # Tilting plate, couplers, grasp sites, and rolling sphere
├── PIDXML.xml                     # Standalone XML definition for PID benchmarks
├── simulation.mp4                 # Pre-recorded video rendering of successful balancing
├── camera_frame.png               # Sample image captured from virtual camera
├── assets/                        # 3D STL collision and visual meshes (links, coupler, plate)
│   ├── coupler.stl
│   ├── plateV2.stl
│   ├── gripper_left_palm.stl
│   ├── gripper_right_palm.stl
│   └── link1.stl ... link5.stl
└── single_arm/                    # Standalone single OpenManipulator-X model
    ├── omx.xml
    ├── scene.xml
    ├── omx.png
    ├── LICENSE
    └── assets/
```

---

## 4. Requirements & Installation

The simulation runs in Python 3.8+ using modern MuJoCo bindings:

```bash
pip install mujoco numpy scipy opencv-python
```

---

## 5. Running the Simulations

### 1. Main Dual-Arm Cooperative Balancing Simulation
Runs the full dual-arm cooperative controller with live passive visualizer:
```bash
python simulate_cooperative.py
```
* **Interactive Controls**: If OpenCV is installed, interactive GUI trackbars appear for real-time PID tuning ($K_p, K_d, K_i$, target setpoint).
* **Mouse Perturbations**: In the MuJoCo viewer, double-click and drag the ball using the right mouse button to introduce real-time physical disturbances and observe the recovery response.
* **Headless Validation**: If no graphical display is available, the script automatically falls back to headless validation mode and executes 500 physics steps with diagnostic readouts.

### 2. Standalone PID Controller Benchmark
Validates the numerical stability and convergence of the PID controller:
```bash
python PID.py
```

### 3. Multi-Camera Pose Calibration & 3D Ball Triangulation
Runs the Perspective-n-Point (solvePnP) calibration comparing OpenGL and OpenCV conventions:
```bash
python verify_cameras.py
```

### 4. Single-Arm OpenManipulator-X Inspection
Inspect the standalone ROBOTIS OpenManipulator-X model:
```bash
python -m mujoco.viewer --mjcf=single_arm/scene.xml
```

---

## 6. References & Licensing

* **Robot Model**: ROBOTIS OpenManipulator-X (ROBOTIS Co., Ltd., Apache 2.0 License).
* **Physics Engine**: MuJoCo Physics (Google DeepMind).
* **Project Integration**: OSRS (Open Source Robotics System) Ball Balancer Research Initiative.
