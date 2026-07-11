# OSRS Cybernetic Servo Controller GUI

> A premium, dark-themed graphical dashboard for controlling Dynamixel-powered humanoid robotic arms via a U2D2 USB-to-serial adapter. Built with CustomTkinter for a modern, responsive interface.

---

## Table of Contents

1. [Hardware Requirements](#hardware-requirements)
2. [Software Requirements](#software-requirements)
3. [Installation](#installation)
4. [Running the GUI](#running-the-gui)
5. [GUI Overview](#gui-overview)
6. [Calibration](#calibration)
7. [Arm Pose Presets](#arm-pose-presets)
8. [Smooth Movement System](#smooth-movement-system)
9. [Motor Layout Reference](#motor-layout-reference)
10. [Advanced Features](#advanced-features)
11. [File Structure](#file-structure)
12. [Troubleshooting](#troubleshooting)

---

## Hardware Requirements

| Component | Details |
|-----------|---------|
| **Servo Bus** | Dynamixel XM430-W350 or compatible Protocol 2.0 servos |
| **USB Adapter** | ROBOTIS U2D2 (USB-to-TTL/RS-485) |
| **PC** | Windows 10/11 (64-bit) recommended |
| **Power** | 12V regulated supply capable of ≥3A per servo chain |

---

## Software Requirements

- Python **3.9+**
- All packages listed in `requirements.txt`:

```
customtkinter>=5.2.0
numpy>=1.20.0
pyserial>=3.5
dynamixel-sdk>=3.7.31
```

---

## Installation

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Install U2D2 drivers (Windows)

Download and install the **CP210x USB to UART Bridge** driver from Silicon Labs:  
https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers

### 3. Connect hardware

- Plug the U2D2 into a USB port
- Connect your servo bus to the U2D2 TTL/RS-485 port
- Power the servo chain with a 12V supply

---

## Running the GUI

```bash
python gui.py
```

The GUI will open in dark mode. No arguments needed.

---

## GUI Overview

The interface is split into a **left sidebar** and a **main tabbed area**.

### Sidebar (Left Panel)

| Section | Function |
|---------|----------|
| **COM Port** | Select serial port and baud rate (default 57600) |
| **Connect / Disconnect** | Opens the bus and scans for motors |
| **Auto-Baud Scan** | Automatically tries 57600 → 1M → 2M → 4M baud |
| **Virtual Mode** | Run without hardware (mock mode for testing) |
| **Global Torque ON/OFF** | Enable or cut torque on all detected motors |
| **E-STOP** | Immediately cuts torque on all motors |
| **Arm Presets** | Quick pose buttons (see below) |
| **Calibration** | Per-arm calibration panel |

### Main Area (Tabs)

| Tab | Function |
|-----|----------|
| **MOTORS** | Live slider + entry control for every detected motor; shows present position, current draw, temperature |
| **TIMELINE** | Keyframe recorder and playback for choreographed sequences |
| **DIAGNOSTICS** | Per-motor health table (voltage, temperature, current, error flags) |
| **INSPECTOR** | Raw register read/write for any Dynamixel address |
| **PID** | Read and write Position PID gains + Profile Velocity per motor |
| **MACRO** | Python macro scripting for automated movement sequences |

---

## Calibration

Calibration stores the **dead-centre (neutral) position** of each servo so that all arm presets are relative to it.

### How to calibrate

1. **Connect** to the bus (click CONNECT in the sidebar).
2. Open the **CALIBRATION** panel (expand it in the sidebar).
3. Click **Torque ON** for the arm you want to calibrate — this powers the servos so you can move them.
4. Use the individual **torque toggles** or **sliders** in the MOTORS tab to physically position each joint to its neutral pose.
5. Click **SAVE LEFT CALIB** or **SAVE RIGHT CALIB**.
6. A confirmation popup "Done Calibration" appears when the values are saved to disk.
7. Click **Go to Left Arm Pose** or **Go to Right Arm Pose** to verify the saved position.

### Calibration file

Calibration values are saved automatically to:

```
chiman_calibration.json
```

in the same directory as `gui.py`. This file is loaded on every startup so your calibration persists across sessions.

### Calibration JSON format

```json
{
  "left": {
    "21": -3561, "12": -162, "13": 4344,
    "24": 4026,  "25": -82,  "26": -1019,
    "27": 2065,  "28": -2676
  },
  "right": {
    "11": -1674, "22": 2138, "23": -1275,
    "14": 2195,  "15": -3,   "16": 5117,
    "17": 2079,  "18": 983
  }
}
```

---

## Arm Pose Presets

All preset buttons are in the **Calibrated Pose Presets** section of the sidebar. Every preset moves from the **calibrated neutral** position as its zero reference.

### Available Presets

| Button | What it does |
|--------|-------------|
| **BOTH ARMS POSE** | Moves all 16 arm joints to their calibrated neutral positions simultaneously |
| **LEFT ARM POSE** | Moves all 8 left-arm joints to calibrated neutral |
| **RIGHT ARM POSE** | Moves all 8 right-arm joints to calibrated neutral |
| **BOTH ARMS UP** | L5 rotates **−150** from neutral; R4 rotates **+150** from neutral (ball is tossed upward) |
| **CENTRE** | Returns both arms to exact calibrated neutral |
| **BOTH ARMS DOWN** | L5 rotates **+150** from neutral; R4 rotates **−150** from neutral (ball is pushed downward) |
| **OPEN HAND** | Opens the left gripper to the calibrated open position |
| **CLOSE HAND** | Closes the left gripper to the calibrated closed position |

### Up / Down Offset

The up/down offset is **hardcoded to ±150 servo units**. Only **two joints** participate in the up/down movement:

| Joint | Motor ID | Up | Down |
|-------|----------|----|------|
| **L5** (left wrist twist) | 25 | `calib − 150` | `calib + 150` |
| **R4** (right wrist twist) | 14 | `calib + 150` | `calib − 150` |

All other joints stay at their calibrated neutral during up/down/centre transitions. This ensures the rest of the arm stays rigid while only the relevant joints move in sync.

---

## Smooth Movement System

All preset transitions (Up → Centre → Down and vice versa) use a **threaded ease-in-out interpolation**:

- **Duration**: ~700 ms total
- **Steps**: 20 interpolation frames
- **Step delay**: 35 ms between frames
- **Easing**: Cubic ease-in-out (`t = t² × (3 − 2t)`)  
  — starts slowly, accelerates through the middle, decelerates to a gentle stop
- **Thread**: Runs in a background daemon thread (non-blocking — GUI stays responsive)

```
Position
  ▲
  │      ╭──────────╮
  │    ╭╯            ╰╮
  │  ╭╯                ╰╮
  │╭╯                    ╰╮
  └─────────────────────────▶ Time
     slow → fast → slow
```

Motors all move together frame-by-frame so L5 and R4 stay perfectly synchronised throughout the entire transition.

---

## Motor Layout Reference

### Left Arm (Motor IDs 12, 13, 21, 24–28)

| ID | Joint Name | Role |
|----|-----------|------|
| 21 | L1 Shoulder Pitch | Raises/lowers the entire left arm |
| 12 | L2 Shoulder Roll | Rolls the left shoulder in/out |
| 13 | L3 Elbow Pitch | Bends the left elbow |
| 24 | L4 Wrist Pitch | Pitches the left wrist (rigid during up/down) |
| **25** | **L5 Wrist Twist** | **Active in Up/Down — rotates ±150** |
| 26 | L6 Finger Base | Finger base joint |
| 27 | L7 Finger Mid | Finger middle joint |
| 28 | L8 Gripper | Opens/closes the left hand |

### Right Arm (Motor IDs 11, 14–18, 22, 23)

| ID | Joint Name | Role |
|----|-----------|------|
| 11 | R1 Shoulder Pitch | Raises/lowers the entire right arm |
| 22 | R2 Shoulder Roll | Rolls the right shoulder in/out |
| 23 | R3 Elbow Pitch | Bends the right elbow |
| **14** | **R4 Wrist Twist** | **Active in Up/Down — rotates ±150** |
| 15 | R5 Wrist Pitch | Pitches the right wrist (rigid during up/down) |
| 16 | R6 Finger Base | Finger base joint |
| 17 | R7 Finger Mid | Finger middle joint |
| 18 | R8 Gripper | Opens/closes the right hand |

---

## Advanced Features

### Dual-Arm Symmetry Mirroring

Toggle the **Dual-Arm Symmetry Mirroring** switch in the sidebar. When active, moving any left-arm joint automatically mirrors the movement to the corresponding right-arm joint (and vice versa), keeping both arms symmetric at all times.

### Timeline / Keyframe Recorder

1. Move the robot to a pose using the sliders
2. Click **Record Keyframe** to save the current pose
3. Add more keyframes at different positions
4. Click **Play** to replay the sequence with a configurable delay between frames

### PID Tuning

Select a motor from the dropdown in the PID tab, click **Read PID** to fetch current gains, then adjust the sliders and click **Write PID** to apply new Position PID values live.

### Profile Velocity

In the PID tab, the **Velocity** slider controls `Profile Velocity` (register 112) — lower values = slower, smoother motion from the servo's built-in trapezoidal profile.

### Register Inspector

The INSPECTOR tab lets you read or write any Dynamixel register directly by address and byte length. Useful for checking hardware status or configuring advanced servo parameters.

### Python Macro Scripting

The MACRO tab accepts Python scripts with access to the `robot` object:

```python
# Example: move motor 25 to position 0 and wait
robot.set_goal(25, 0)
robot.wait(1.0)
robot.set_goal(25, -82)
```

---

## File Structure

```
osrs_gui/
├── gui.py                  # Main GUI application (CustomTkinter)
├── dynamixel_driver.py     # Dynamixel Protocol 2.0 driver wrapper
├── requirements.txt        # Python package dependencies
├── README.md               # This file
└── chiman_calibration.json # Auto-generated calibration file (created on first save)
```

---

## Troubleshooting

| Problem | Solution |
|---------|---------|
| **No COM ports listed** | Install the CP210x driver; replug the U2D2 |
| **No motors found after scan** | Check baud rate matches servo config; verify 12V power is on |
| **Torque enable fails** | Reboot the motor (REBOOT button in the motor row) and try again |
| **Calibration not saving** | Make sure `gui.py` is in a writable directory; check the log panel for errors |
| **GUI not opening** | Run `pip install -r requirements.txt` to ensure all dependencies are installed |
| **Jerky movement** | Increase `Profile Velocity` in the PID tab to a lower value (e.g., 50–150) for hardware-level smoothing |
| **Motors not detected** | Click **RE-SCAN BUS** in the sidebar or try **Auto-Baud Scan** |

---

## Notes

- The calibration values stored in `chiman_calibration.json` are specific to **your physical robot's assembly**. If you reassemble any joint, recalibrate that arm.
- All position values are in **Dynamixel raw encoder units** (12-bit, 0–4095 for XM430; extended range for multi-turn mode).
- The GUI runs a 40 ms background loop (`25 Hz`) for reading positions and writing goal positions. This loop is separate from the GUI render loop.

---

*Built for the OSRS (Open-Source Robotic System) Chiman humanoid project.*
