# Two-Arm (HEAL & Franka FR3) Ball Manipulation

Self-contained minimal setup for running the dual-arm cooperative plate-balancing and ball manipulation simulation.

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
