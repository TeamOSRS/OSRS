# Privacy & Telemetry Policy

The **Open Source Robotics System (OSRS)** project is committed to total privacy, local-first autonomy, and operator security.

---

## 1. 100% Local-First Architecture

- **No Remote Telemetry**: OSRS does not collect, harvest, or transmit any user data, system metrics, hardware telemetry, or IP addresses to third-party cloud servers.
- **Local Workstation Processing**: All web server endpoints (`http://localhost:8000`), WebSocket communication channels (`ws://localhost:8000/ws/telemetry`), and Vite frontend assets run strictly on the operator's local machine.

---

## 2. Sensor & Camera Feeds

- **Vision Streams**: Camera feeds processed by MediaPipe HandTracker, OpenCV, or Intel RealSense depth sensors are processed strictly in-memory on your local CPU/GPU.
- **Zero Cloud Video Ingestion**: Frame buffers are encoded locally for browser canvas rendering and are never uploaded or streamed outside your local network.

---

## 3. Data Recording & Storage

- **Local Telemetry Files**: Data recorded using the OSRS Telemetry Recorder is saved exclusively to local JSON/CSV files designated by the operator.
- **Configuration & Calibration**: Calibration offsets (`humanoid_calibration.json`, `load_cell_calibration.json`) and motor configurations are stored exclusively on local disk.

---

## 4. Third-Party Dependencies

OSRS utilizes standard open-source dependencies (FastAPI, Uvicorn, NumPy, OpenCV, PyMuJoCo, React, Lucide Icons, Vite). None of these packages are configured to perform external tracking within OSRS.
