# Stage 2: Asymmetric Two-Arm (HEAL & Franka FR3) Ball Manipulation Simulation

This directory contains the self-contained setup for running the **Stage 2 MuJoCo simulation**, advancing from the symmetric dual OpenManipulator-X setup ([Stage 1](../omx_ball_manipulation/)) to an asymmetric high-payload industrial manipulation platform.

## Research Context
* **Stage 1 ([`../omx_ball_manipulation`](../omx_ball_manipulation/))**: Symmetric dual OpenManipulator-X arms validating rolling-sphere physics, height-based differential kinematics ($\Delta z = L_p \sin\theta$), and baseline PID stabilization.
* **Stage 2 (This Directory)**: Heterogeneous asymmetric dual-arm setup (Franka Emika FR3 7-DOF + HEAL 6-DOF arm) with Robotiq 2F-85 grippers, expanding the workspace, dynamic load capacity, and 2D trajectory tracking capabilities.
* **Stage 3 ([`../src/`](../src/) & [`../simulation_ref/`](../simulation_ref/))**: Full physical robotic platform deployment with humanoid arms, Dynamixel servos, Intel RealSense vision, and load cell sensor fusion.

## Requirements
```bash
pip install mujoco numpy
```

## Running the Simulation
To run with the ball converging to the plate center (0, 0):
```bash
python ball_balance_controller.py
```

To target a specific plate-local coordinate (in meters, e.g. x = 0.1, y = -0.05):
```bash
python ball_balance_controller.py 0.1 -0.05
```

## Included Files
- `ball_balance_controller.py`: Main dual-arm kinematics, IK solver, PID controller, and MuJoCo passive viewer execution loop.
- `scene_franka_heal.xml`: Dual-arm MuJoCo scene XML defining the Franka FR3, HEAL arm, Robotiq 2F-85 gripper, plate, and ball.
- `franka_fr3/assets/`: Collision and visual 3D mesh files for Franka FR3.
- `heal_meshes_v2/`: Collision and visual 3D mesh files for HEAL arm and Robotiq gripper.
