# OSRS (Open-Source Robotic System) - Graphical User Interface Manual

This manual provides an in-depth explanation of the user interface for **OSRS (Open-Source Robotic System)**, created by **Bilal Sabugar**. The platform is designed as a professional-grade, high-density desktop control suite with an ultra-modern cybernetic mission control aesthetic (deep graphite background `#0A0F14`, neon cyan `#00F0FF` telemetry, electric blue highlighting, and emerald operational states).

---

## 1. Startup Boot Loader & Robot Profile Selector

When OSRS launches, a full-screen system booting sequence triggers. 

- **Animated Splash Console**: Displays real-time booting steps (initializing kernel, scanning ports, loading joint limit profiles, testing safety watchdogs) with a dynamic cyan progress bar.
- **Robot Profile Selector Cards**:
  Once booting finishes, the operator is prompted to choose a hardware configuration:
  1. **👐 LEAP Hand**: Controls standard **V1 (16 Servos)** or **V2 (8 Servos)** configurations.
  2. **🤖 Humanoid Bot V1**: Dual 7-DOF arms and pan-tilt head kinematic mappings.
  3. **🏗️ Rovers & Arms**: Pushes targets to **OpenManipulator-X** (5 joints), **Rover Bot** (6-wheel differential steering), or **Custom Platforms** (4 finger-mapped aux joints).
- Selecting any card sets the bounds, refreshes all view models, and fades out the overlay.

---

## 2. Persistent OS Elements

Two core layout structures remain visible across all pages:

### Global Status Top Bar
Positioned at the top of the interface:
- **Active Profile Tag**: Shows `ACTIVE SYSTEM: [Robot Name]`.
- **Communications Badge**: Displays active serial channel status (`● MOCK SIMULATOR` in warning amber, `● SYSTEM LIVE` in green, or `● SCAN FAILED` in red).
- **🚨 Emergency Stop Button**: Crimson red button. Triggering it immediately halts command writes, releases joint torques, and alerts watchdogs.
- **System Health Radial Canvas**: Renders a vector-drawn circular health indicator (0-100%) color-coded based on safety.
- **Monospace Telemetry Feed**: Real-time updates for:
  - `FPS: XX` (Perception frame rate)
  - `LAT: X.X ms` (Packet communication latency)
  - `CPU: XX.X%` (Kernel processing load)
  - `RAM: X.X GB` (System memory footprint)

### Collapsible Sidebar Navigation
Vertical drawer on the left side providing access to all 13 command center views. Can be collapsed into compact icon badges using the `◀ COLLAPSE MENU` toggle.

---

## 3. The 13 Command Center Views

### 1. 📊 Dashboard
The central environment cockpit:
- **Perception feed box**: size-constrained container frame holding OpenCV camera streams overlaid with landmarks.
- **AI Confidence Gauge**: monitors classification match accuracy.
- **Mission status badge**: green state feed (`STANDBY`, `ACTIVE RUN`, or `ESTOP LOCK`).
- **Operator Timeline Console**: timestamped scrolling records of user commands and safety logs.

### 2. 🚀 Mission Control
Routines automated scheduler:
- Commands for executing custom sweep macros.
- Hardware stress test triggers (loops joint boundaries to test thermal and load limits).
- Telemetry baseline reset actions.

### 3. 🤖 Robot Manager
Robot profiles catalog:
- Displays operational details for all OSRS-supported models.
- Individual cards show online status, battery charge (V), health (%), active devices count, and firmware tags.

### 4. 📦 Digital Twin
Skeletal wireframe synchronizer:
- Custom canvas displaying real-time joint positions.
- **Thermal Heatmap Console**: Lists real-time temperatures for all joint motors. Colors update to reflect COOL (green) or WARM (amber) conditions.

### 5. 🎛 Control Center
Manual hardware interface manager:
- Dropdowns for targeting Serial COM ports and baudrates.
- Segmented robot version switcher.
- Simulation Mode toggles.
- **Actuators Sliders Scroll**: grid of joint command sliders mapped to safe calibrated boundaries.

### 6. 📐 Calibration Wizard
Interactive 7-step guided setup replacing standard tables:
1. *Device Detection* (Scanning serial channels)
2. *Motor Verification* (Checking encoder limits)
3. *Home Position* (Resetting neutral poses)
4. *Open Limits Detection* (Homing mechanical stops)
5. *Closed Limits Detection* (Computing stall current thresholds)
6. *Safety Validation* (Testing emergency stops and watchdogs)
7. *Save Configuration* (Writing XML parameter registers)

### 7. 📈 Health Diagnostics
Health statistics panel:
- **Telemetry Waveform Canvas**: Plots real-time joint position updates.
- **Grid of Status Cards**: Displays goals vs present positions, current draws (mA), temperature logs, and communications integrity for all active servos.

### 8. 👁 Vision System
AI perception workspace:
- Object detection confidence threshold slider.
- Mesh overlays and gesture recognition toggles.

### 9. 🗺 CAD ID Mapper
Joint config re-mapper:
- CAD-style grid canvas representing joint node configurations.
- Click any node circle to populate the sidebar editor form.
- Form inputs for re-mapping Dynamixel IDs, limits, deleting nodes, or registering custom new nodes.

### 10. 💾 Raw Telemetry
Telemetry packet matrix terminal:
- Monospaced real-time readout of goal positions, actual encoder reads, and current draws.

### 11. 🗒 System Event Logs
Filtered logging console:
- Level filter triggers (ALL, WARNING).
- Export button to save register logs.

### 12. 🧪 Physics Simulator
Virtual physics simulator overrides:
- Friction coefficient sliders.
- Gravity constant controls (m/s²).

### 13. ⚙ Safety Settings
Electrical and software guardrails settings:
- Thermal warning shutdown thresholds.
- Maximum motor current draw peak limits.
