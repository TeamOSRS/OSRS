# Ball-on-Plate Balancing Simulation
### Simplified Elbow See-Saw Proportional Control — MuJoCo

A real-time MuJoCo physics simulation of an 18-DOF custom humanoid robot balancing a ball on a U-channel plate held between both hands.

---

## How It Works

The robot holds a narrow U-channel plate rigidly in both hands (weld constraints). A small red ball is placed on the plate and is free to roll along the Y-axis channel.

**Control strategy — "Simplified See-Saw":**
- The shoulder joints (J1–J3) are **locked** at their home positions via very high-stiffness PID torque control. They do not move.
- Only the **elbow pitch joints (J4)** on each arm are actuated during balancing.
- A proportional feedback law reads the ball's Y position on the plate and commands equal-and-opposite elbow pitch corrections, tilting the plate to roll the ball back to the target position.
- The robot's **head tracks the ball** in real time.

```
Ball drifts right (+Y)
  → Left elbow lowers, Right elbow raises
  → Plate tilts → Ball rolls back to center
```

---

## Requirements

- Python 3.10 or 3.11
- MuJoCo Python bindings:

```bash
pip install mujoco
```

No other external dependencies. The robot model uses **primitive geometries only** (boxes, cylinders, spheres) — no mesh files needed.

---

## Running the Simulation

### Option 1 — Double-click (Windows)
Double-click **`launch_simulation.bat`**

### Option 2 — Command line
```bash
cd ball_balance_sim
python balance_plate_simple.py
```

A terminal menu and the **MuJoCo viewer window** will open together.

---

## Interactive Commands

Once running, type commands into the terminal window:

| Command | Description |
|---|---|
| `0.0` | Set ball target to center (default) |
| `0.1` | Set ball target to +10cm right |
| `-0.1` | Set ball target to -10cm left |
| `g 3.0` | Set proportional elbow gain (default: 3.0) |
| `r` | Reset — re-centers plate, offsets ball by +5cm |
| `t` | Print live telemetry (ball pos, tilt, elbow angles) |
| `h` | Show the command menu |
| `q` | Quit |

**Tip:** Hold `CTRL` and **Right-Click & Drag** the red ball in the MuJoCo viewer to physically perturb it. The robot will recover automatically.

---

## File Structure

```
ball_balance_sim/
├── launch_simulation.bat       ← Double-click to run (Windows)
├── balance_plate_simple.py     ← Main simulation script
├── my_bot_plate_scene.xml      ← MuJoCo scene (plate, ball, lights)
├── my_bot.xml                  ← 18-DOF humanoid robot model
└── README.md                   ← This file
```

---

## Robot Model Summary

- **18 DOF** custom humanoid upper body
- **7 DOF per arm**: Shoulder Pitch, Shoulder Roll, Shoulder Yaw, Elbow Pitch, Forearm Yaw, Wrist Pitch, Wrist Yaw
- **2 DOF head**: Head Yaw, Head Tilt
- Actuators modelled after **Dynamixel XM430 / XH430** servo specs
- Plate held via **rigid weld equality constraints** between wrist links and plate body

---

*Built with MuJoCo · Python · NumPy*
