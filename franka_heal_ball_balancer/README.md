# Franka + HEAL Cooperative Ball Balancer

A MuJoCo simulation where a Franka FR3 arm and a HEAL arm cooperatively hold
a plate and balance a rolling ball on it using a PID controller (with
per-arm damped-least-squares IK).

Imported from the standalone `healing da franka` project — self-contained
here with everything needed to run it.

## Contents

- `ball_balance_controller.py` — IK solver + `BallBalancer` PID controller + viewer entry point
- `scene_franka_heal.xml` — MuJoCo scene (both arms, plate, ball, actuators, keyframe)
- `franka_fr3/assets/` — Franka FR3 visual/collision meshes (`.obj`/`.stl`)
- `heal_meshes_v2/` — HEAL arm + Robotiq 85 gripper meshes (`.STL`)

## Requirements

```powershell
pip install -r requirements.txt
```

(Kept separate from the root [requirements.txt](../requirements.txt) —
this is a standalone reference simulation, not a core OSRS runtime
dependency.)

## Running

```powershell
cd "franka_heal_ball_balancer"
python ball_balance_controller.py
```

Optionally pass a target point on the plate (plate-local metres from centre):

```powershell
python ball_balance_controller.py 0.1 -0.05
```

A passive MuJoCo viewer window opens showing both arms holding the plate
while the controller rolls the ball toward the target point.
