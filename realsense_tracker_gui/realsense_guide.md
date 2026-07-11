# Beginner's Guide: Intel RealSense 3D Ball Tracking (Consolidated Viewer)

This document explains how your consolidated RealSense ball tracking application works, the core concepts behind it, how to use the single unified interface, and where to edit the code.

---

## 1. Project Architecture (Where to Edit)

The project is structured into three distinct Python files:

```
realsense_project/
├── camera.py          # Handles the physical camera hardware, settings, and depth projection
├── ball_tracker.py    # Handles computer vision (detecting the ball's shape and color)
└── main.py            # The coordinator: manages the interface and links the other files
```

### 📂 [camera.py](file:///c:/Users/Archie/.gemini/antigravity-ide/scratch/realsense_project/camera.py)
* **What it does**: Initializes the Intel RealSense camera, starts the streams, aligns the depth pixels to match the color pixels, and contains built-in helper methods for settings manipulation (`set_laser_power`, `set_emitter_state`, `set_exposure`, etc.).
* **When to edit**: Edit this file if you want to add support for new camera options or change the initialization parameters.

### 📂 [ball_tracker.py](file:///c:/Users/Archie/.gemini/antigravity-ide/scratch/realsense_project/ball_tracker.py)
* **What it does**: Converts the image to the HSV color space, filters out everything except the ball's color, removes image noise, and calculates the center point and radius of the ball.
* **When to edit**: Edit this file if you want to change the tracking shape (e.g. detecting a square, or using a different contour algorithm).

### 📂 [main.py](file:///c:/Users/Archie/.gemini/antigravity-ide/scratch/realsense_project/main.py)
* **What it does**: Runs the main loop, coordinates the camera and tracker, builds the 2x2 unified viewport grid, draws the dashboard telemetry pane, and links the trackbar adjustments to the hardware in real-time.
* **When to edit**: Edit this file if you want to modify dashboard colors, change trackbar ranges, or add new tracking logic based on the 3D coordinates.

---

## 2. The Consolidated 2x2 Viewer Window

Instead of opening multiple messy windows, everything runs inside a single window named **"Intel RealSense SDK Viewer & Tracker"**. 

It stacks four panels together into a 2x2 grid (`1280x960` pixels):

```
┌───────────────────────────────────────┬───────────────────────────────────────┐
│                                       │                                       │
│    Top-Left: COLOR STREAM             │    Top-Right: DEPTH COLORMAP          │
│    Shows color feed, yellow circle    │    JET colormap mapping distance.    │
│    trajectory tail, and 3D overlay.   │    Red=Close, Blue=Far.               │
│                                       │                                       │
├───────────────────────────────────────┼───────────────────────────────────────┤
│                                       │                                       │
│    Bottom-Left: HSV MASK              │    Bottom-Right: TELEMETRY DASHBOARD  │
│    Binary black-and-white mask.       │    Dark-mode stats pane displaying    │
│    White = tracked color area.        │    3D Position, status, and SDK info. │
│                                       │                                       │
└───────────────────────────────────────┴───────────────────────────────────────┘
```

---

## 3. Real-Time Sliders (Main Window Controls)

All control sliders are attached to the top of the main window. They are divided into two sections:

### 🎨 HSV Color Tuning (For Ball Detection)
Standard images use RGB. For tracking, we use **HSV (Hue, Saturation, Value)** because it is less affected by room lighting changes:
* **Min H / Max H**: Color tint. (Green is typically between `29` and `64`).
* **Min S / Max S**: Vibrancy of the color. (Filters out gray/white light).
* **Min V / Max V**: Brightness. (Filters out dark shadows).

### ⚙️ Intel RealSense Hardware Controls
These controls communicate directly with the camera's internal electronics:
* **IR Emitter**:
  * `0`: Turns off the IR projector (removes the dotted grid overlay on the color stream).
  * `1`: Enables the IR projector.
  * `2`: Sets the IR projector to auto-mode.
* **Laser Power**: Sets the projector laser power from `0` to `360` mW (increases depth scanning accuracy in low light).
* **Auto Exp**: Sets the camera exposure mode:
  * `1`: Auto exposure (camera adjusts brightness automatically).
  * `0`: Manual exposure (uses the value set by the `Exposure(us)` slider).
* **Exposure(us)**: Sets manual exposure time in microseconds. Lower values prevent motion blur when objects move fast. (Active only when `Auto Exp` is `0`).

---

## 4. The Telemetry Dashboard

The bottom-right quadrant of the screen displays live feedback from the system:
1. **Target Tracking Status**:
   * Displays **ACTIVE TRACKING** (green) or **SEARCHING FOR TARGET...** (red).
   * Shows real-world `X` (left/right deviation in meters), `Y` (up/down deviation in meters), and `Z` (distance from camera lens in meters) of the tracked object center.
2. **Hardware Parameters**:
   * Shows the current active state of the IR Emitter, Laser Power, and Exposure mode.
3. **Device Information**:
   * Displays the connected RealSense model, serial number, active firmware version, and connection type (**USB 3.2** or **USB 2.1**).
