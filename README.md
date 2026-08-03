# Open Source Robotics System (OSRS

OSRS is a modular, real-time control, perception, and simulation system designed for humanoid robotics, robotic arms, and active-balancing research platforms. It features a dynamic plugin-discovery architecture, allowing developers to integrate custom robot kinematics, computer vision pipelines, sensor arrays, and simulation environments without hardcoded imports.

## System Architecture

The project is split into a Python backend that handles hardware driver loops and perception algorithms, and a React-based frontend that provides a real-time web dashboard for configuration, telemetry plotting, and digital twin rendering.

```
OSRS/
├── src/
│   ├── core/                      # Core runtime and communication layer
│   │   ├── server.py              # FastAPI HTTP and WebSocket server
│   │   ├── plugin_manager.py      # Dynamic runtime plugin discovery engine
│   │   ├── robot_manager.py       # Serial bus driver and command sequencer
│   │   └── logging.py             # Memory-buffered telemetry logger
│   └── modules/                   # Dynamically discovered extensions
│       ├── robots/                # Actuator configurations and joint profiles
│       ├── perception/            # Camera tracking and force sensor drivers
│       ├── research/              # Control algorithms and training tasks
│       └── simulation/            # Digital twin and physics engine bridges
├── frontend/                      # Vite React dashboard application
├── docs/                          # Detailed system manuals and operator's guides
└── LOAD CELL/                     # Embedded Arduino firmware and calibrations
```

## Documentation

The repository features comprehensive guides detailing hardware setup, visual mapping coordinate convention details, tracking algorithms, and web interface controls:

* **[GUI Operator's Manual](docs/GUI_MANUAL.md)**: Steps to run and navigate the web-based OSRS Command Center.
* **[Vision System Guide](docs/vision_system_manual.md)**: Instructions for calibrating camera sensors, depth configurations, and tracking HSV parameters.
* **[Kinematics Coordinates Map](docs/simulation_ref_mapping.md)**: Explains the skeletal bone structure configurations and coordinate conventions.
* **[Filter & Target Tracking Explanation](docs/EXPLANATION.md)**: Explains the math and algorithms behind target reflection isolation, boundary limits, and active PID balancing.
* **[Ball Balancing Control & Estimation](docs/BALL_BALANCE_RESEARCH.md)**: Details the active PID balancing control loops, Recursive Least Squares (RLS) system identification, and sensor confidence-weighting equations.
* **[Ball Balancer Research Paper](docs/BALL_BALANCER_RESEARCH_PAPER.md)**: Complete theoretical research paper, mathematics, control laws, perception algorithms, and evolution from 1D vision to 2D dual-axis load cell fusion.

---

### 1. Core Engine
* **Plugin Discovery**: The `PluginManager` dynamically traverses directories inside `src/modules/` at startup, registering classes that inherit from base interfaces.
* **Actuator Bus**: Powered by Dynamixel protocol drivers, managing multi-joint synchronizations, profile constraints, and real-time motor state polling.
* **Telemetry Broadcast**: A high-frequency WebSocket loop broadcasts joint states, 3D target coordinates, and load cell weight calculations to the web interface.

### 2. Modules Layer
* **Robots**: Declares joint profiles, physical limits, mirroring maps, and starting poses (e.g., Leap Hand, Humanoid Bot, Open Manipulator X).
* **Perception**: Runs the Intel RealSense camera tracker, ArUco plate coordinate calculations, HSV color masks, and HX711 serial communications.
* **Research**: Contains execution loops for research tasks, such as the `BallBalancer` controller implementing PID, Active Exploration, and Recursive Least Squares (RLS) load cell model training.
* **Simulation**: Connects to physics engines (MuJoCo, digital twin viewers) to sync physical and simulated components.

---

## Installation and Prerequisites

### Backend Dependencies
Ensure you have Python 3.10+ installed.

1. Install required Python libraries:
   ```powershell
   pip install fastapi uvicorn pyserial opencv-python numpy pycompilation
   ```

2. Optional: Install the Intel RealSense SDK if using a physical depth camera, or MuJoCo for physics simulations.

### Frontend Dependencies
Ensure you have Node.js (v18+) and npm installed.

1. Navigate to the frontend directory:
   ```powershell
   cd frontend
   ```
2. Install Node packages:
   ```powershell
   npm install
   ```

---

## Getting Started

### Running the Platform

#### 1. Start the Production Server
The backend is configured to host the pre-compiled frontend assets directly. Simply run:
```powershell
python main.py
```
By default, the server initializes dynamic plugins, establishes connections to serial actuator buses, and opens a web browser to `http://localhost:8000`.

#### 2. Start the Frontend Development Server (For editing UI)
If you are editing the React code and want hot-reloading:
1. Start the backend server as normal.
2. In a separate terminal, navigate to the frontend directory and start Vite:
   ```powershell
   cd frontend
   npm run dev
   ```
3. Open `http://localhost:5173` to view the hot-reloading development dashboard.

---

## Embedded Firmware (Load Cells)

The `LOAD CELL` directory contains PlatformIO and Arduino CLI firmware configurations for an Arduino Uno reading HX711 weight sensors.

### Compiling and Uploading Firmware
If the Arduino firmware needs to be updated or flashed:
1. Locate your Arduino IDE installation directory. The compiler is located at:
   `C:\Program Files\Arduino IDE\resources\app\lib\backend\resources\arduino-cli.exe`

2. Compile the sketch:
   ```powershell
   & "C:\Program Files\Arduino IDE\resources\app\lib\backend\resources\arduino-cli.exe" compile --fqbn arduino:avr:uno "LOAD CELL\OSRS_Scale"
   ```

3. Upload to the Arduino (replace `COM9` with your active Arduino port):
   ```powershell
   & "C:\Program Files\Arduino IDE\resources\app\lib\backend\resources\arduino-cli.exe" upload -p COM9 --fqbn arduino:avr:uno "LOAD CELL\OSRS_Scale"
   ```

---

## Development Guide (How to Start Editing)

### 1. Extending Backend Functionality

To add a new feature, implement a class inside the appropriate subdirectory under `src/modules/`. The startup sequence will automatically find and register it.

#### Adding a New Robot Profile
Create a python file in `src/modules/robots/` subclassing `BaseRobot`:
```python
from src.modules.robots.base_robot import BaseRobot

class CustomManipulator(BaseRobot):
    def __init__(self):
        super().__init__()
        self.profile_name = "Custom Manipulator"
        
    def get_joint_layout(self):
        # Return motor IDs, angular ranges, and names
        return {
            1: {"name": "Base Joint", "min": 0, "max": 4095, "default": 2048}
        }
```

#### Adding a Perception Module
Create a python file in `src/modules/perception/` subclassing the appropriate base class, or register it within the plugin manager.

#### Adding a Research Task
Create a python file in `src/modules/research/` subclassing `BaseResearchTask`:
```python
from src.modules.research.base_research_task import BaseResearchTask

class TargetAlignmentTask(BaseResearchTask):
    def __init__(self, event_bus):
        super().__init__(event_bus)
        self.name = "target_alignment"
        self.is_active = False

    def step(self):
        if not self.is_active:
            return
        # Execute research task step here (e.g., read sensor states, command motors)
        pass
```

### 2. Modifying the User Interface

1. Edit components inside `frontend/src/components/` (such as `BallBalancerResearch.jsx`).
2. When your modifications are complete, compile the production bundle:
   ```powershell
   cd frontend
   npm run build
   ```
3. The build process outputs static files to the backend static directories. The changes will be visible when running `python main.py`.

---

## Hardware Integration Notes

### RealSense Tracker
* The vision tracker matches coordinate systems using ArUco markers mounted on the robotic hands to construct a dynamic Plate Bounding Box.
* Masking limits search bounds strictly to the plate surface, ignoring room reflections and flooring.

### Force Sensing (Load Cells)
* Weight calibration maps raw counts to grams.
* Run calibration through the dashboard under **Load Cells** -> **Calibrate** after running a **Tare** command with an empty plate.
