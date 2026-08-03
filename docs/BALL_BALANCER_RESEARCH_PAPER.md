# Autonomous Dual-Axis Ball Balancing and Online System Identification: A Modular Hybrid Vision-Force Research Architecture

**Authors**: OSRS Core Engineering Team (Aditya Jadav, Archie Veera, Bilal Sabugar)  
**Target Platform**: Open Source Robotics System (OSRS)  
**Location**: `docs/BALL_BALANCER_RESEARCH_PAPER.md`  

---

## Abstract

This paper presents the comprehensive control, perception, system identification, and hardware execution framework for the **Ball Balancer Research Module** implemented within the Open Source Robotics System (OSRS). The platform addresses the stabilization of a rolling sphere on a dynamic plate using under-actuated mechanical linkages driven by high-torque Dynamixel actuators. We detail the evolution of the control system from an initial single-axis (1D) vision-based feedback loop to a fully autonomous, dual-axis (2D) hybrid estimator fusing overhead depth camera tracking with high-speed dual-load-cell force measurements. Furthermore, we outline the exact mathematical models, adaptive PID control laws, Recursive Least Squares (RLS) online plant parameter identification, active persistent excitation modes, and joint-level backlash compensation routines operating within the 50 Hz real-time backend thread.

---

## 1. Final Aim & System Objectives

The primary aim of the OSRS Ball Balancer research module is to provide a robust, zero-overhead, real-time experimental benchmark for closed-loop control of non-linear, under-actuated, open-loop unstable physical systems.

### Core Objectives:
1. **Real-time Trajectory & Setpoint Stabilization**: Maintain a rolling sphere at $s_{\text{target}} = 0.0\text{ m}$ (plate center) or navigate complex user-defined orbits (e.g., circle trajectories, figure-8 infinity loops) despite external physical perturbations.
2. **Hybrid Sensor Fusion**: Seamlessly combine low-latency, noisy force-scale readings (80 Hz) with high-accuracy, camera-derived 3D spatial coordinates (30–60 Hz) to eliminate reaction lag and ensure continuity during visual occlusions.
3. **Online System Identification**: Continuously estimate time-varying physical parameters—specifically control authority $a$ (acceleration per unit tilt) and rolling resistance/damping $b$—without needing offline dynamic calibration.
4. **Adaptive Scenario-Aware Control**: Self-tune controller gains ($K_p, K_i, K_d$) dynamically based on structural motion profiles (`STUCK_RECOVERY`, `FINE_TUNING`, `EMERGENCY_RETRIEVE`, `PREEMPTIVE_BRAKING`).
5. **Zero-Overhead Dynamic Modularity**: Decouple hardware drivers, perception filters, and control algorithms through an event-driven Python/C++ architecture integrated with a React-based telemetry dashboard.

---

## 2. Distributed Architecture & Software Stack

The software implementation is distributed across three main execution layers: embedded hardware firmware, a multi-threaded Python core runtime, and a web-based user interface.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           React UI Dashboard (Browser)                          │
│        - Real-Time 50Hz WebSocket Plots   - Gain Tuning & Scenario Controls     │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │ HTTP / WS (/ws/telemetry)
┌────────────────────────────────────────▼────────────────────────────────────────┐
│                        OSRS Backend Core (`src/core/`)                          │
│  ┌───────────────────────────┐  dxl_lock  ┌──────────────────────────────────┐  │
│  │   FastAPI Server Thread   │ ─────────► │ DXL Worker Loop (50 Hz OS Thread)│  │
│  └───────────────────────────┘            └────────────────┬─────────────────┘  │
│                ▲                                           │                    │
│                │ EventBus Notifications                    │ GroupSyncWrite     │
│  ┌─────────────┴─────────────┐                             ▼                    │
│  │ BallBalancer Coordinator  │               ┌───────────────────────────────┐  │
│  │ (`src/modules/research/`) │               │   Dynamixel Servo Bus (USB)   │  │
│  └─────────────▲─────────────┘               └───────────────────────────────┘  │
└────────────────┼────────────────────────────────────────────────────────────────┘
                 │ State Inputs
┌────────────────┴────────────────────────────────────────────────────────────────┐
│                   Perception Drivers (`src/modules/perception/`)               │
│  ┌─────────────────────────────┐         ┌───────────────────────────────────┐  │
│  │  RealSenseVision / OpenCV   │         │    ForceSensing (HX711 Scales)    │  │
│  └─────────────▲───────────────┘         └─────────────────▲─────────────────┘  │
└────────────────┼───────────────────────────────────────────┼────────────────────┘
                 │ RGB-D Video Feed                          │ Serial ASCII Data
┌────────────────┴───────────────┐         ┌─────────────────┴──────────────────┐
│  Intel RealSense D415/D435     │         │ Arduino Uno Scale Firmware (80 Hz) │
└────────────────────────────────┘         └────────────────────────────────────┘
```

### Threading & Synchronization Model:
* **DXL Worker Thread (`_dxl_worker_loop`)**: Runs in a dedicated background thread at 50 Hz. It acquires the `dxl_lock` mutex to read target motor ticks, sends bundled `GroupSyncWrite` packets over the serial bus, reads position/current telemetry via `GroupSyncRead`, and updates joint state buffers.
* **Research Control Thread**: Calls `BallBalancer.step(dt)` inside the main server loop. It polls the active state provider (`VisionBallTracker`, `ForceBallEstimator`, or `FusionBallEstimator`) and computes the target plate tilt offsets.
* **Embedded Scale Firmware**: An Arduino Uno running `LOAD CELL/OSRS_Scale/OSRS_Scale.ino` or `LOAD CELL/src/main.cpp` reads HX711 24-bit ADCs, applies a 10-sample moving average filter, and streams raw load cell counts at 80 Hz over USB serial.

---

## 3. Perception & Tracking Algorithms

The system incorporates dual perception pipelines to estimate the ball's position state vector $\mathbf{x}(t) = [x, y, v_x, v_y]^T$.

### 3.1 Computer Vision Tracking Pipeline (`src/modules/perception/realsense_vision.py` & `vision.py`)

#### A. ArUco Boundary Anchoring
To isolate the tiltable plate area from ambient room backgrounds, OpenCV detects ArUco markers (`cv2.aruco.DICT_4X4_50`). Markers placed on the plate edges define a planar coordinate frame $\mathbf{P}_{\text{plate}}$, masking out all external image regions.

#### B. Color & Geometry Segmentation
The camera feed is converted to the HSV color space to segment the target sphere (e.g., `green_ping_pong` or `metal_chrome` ball):

$$H_{\text{min}} \le H \le H_{\text{max}}, \quad S_{\text{min}} \le S \le S_{\text{max}}, \quad V_{\text{min}} \le V \le V_{\text{max}}$$

The binary threshold mask undergoes morphological closing, after which contours $\mathbf{C}$ are extracted. Contours are evaluated against two geometric invariants:
1. **Minimum Area Threshold**:
   $$A = \text{cv2.contourArea}(\mathbf{C}) \ge A_{\text{min}} \quad (A_{\text{min}} = 30\text{ px}^2)$$
2. **Circularity Metric**:
   $$\mathcal{C} = \frac{4 \pi A}{P^2} \ge \mathcal{C}_{\text{min}} \quad (P = \text{cv2.arcLength}(\mathbf{C}, \text{True}), \; \mathcal{C}_{\text{min}} = 0.40)$$

#### C. Spatial Deprojection & Coordinate Normalization
For depth cameras (Intel RealSense D415/D435), pixel coordinates $(u, v)$ and depth $D(u, v)$ are deprojected to 3D metric coordinates using the camera intrinsic matrix $\mathbf{K}$:

$$X = \frac{(u - c_x) \cdot D}{f_x}, \quad Y = \frac{(v - c_y) \cdot D}{f_y}, \quad Z = D$$

The metric position $Y$ is normalized to the plate bounds $[-0.22\text{ m}, +0.22\text{ m}]$.

#### D. Velocity Estimation & EMA Filtering (`VisionBallTracker`)
Raw velocities are computed via backward numerical differentiation over time step $\Delta t = \max(0.005, t_k - t_{k-1})$:

$$v_{\text{raw}, k} = \frac{y_k - y_{k-1}}{\Delta t}$$

To eliminate high-frequency camera measurement noise without introducing excessive phase lag, an Exponential Moving Average (EMA) filter ($\alpha = 0.30$) is applied:

$$v_{y, k} = \alpha \cdot v_{\text{raw}, k} + (1 - \alpha) \cdot v_{y, k-1}$$

---

### 3.2 Load Cell Force Estimation Pipeline (`src/modules/perception/force_sensing.py` & `LOAD CELL/`)

#### A. Raw Weight Calibration & Tare
Raw 24-bit counts from the left ($L$) and right ($R$) HX711 amplifiers ($\text{raw}_L, \text{raw}_R$) are converted to calibrated mass values (grams) using zero offsets ($\text{tare}_L, \text{tare}_R$) and calibration scale factors ($k_L, k_R$):

$$w_L = \frac{\text{raw}_L - \text{tare}_L}{k_L}, \quad w_R = \frac{\text{raw}_R - \text{tare}_R}{k_R}$$

#### B. Differential Load Ratio
The force distribution ratio $r \in [-1.0, +1.0]$ across the plate is calculated based on the configured mode:
* **Dual Load Cell Mode ($N=2$)**:
  $$r = \begin{cases} \frac{w_R - w_L}{w_L + w_R} & \text{if } (w_L + w_R) > 15.0\text{ g} \\ 0.0 & \text{otherwise} \end{cases}$$
* **Single Load Cell Mode ($N=1$)**:
  $$r = \begin{cases} 1.0 - 2.0 \cdot \left(\frac{w_L}{w_{\text{ref}}}\right) & \text{if Left Arm, } w_L > 5.0\text{ g} \\ 2.0 \cdot \left(\frac{w_R}{w_{\text{ref}}}\right) - 1.0 & \text{if Right Arm, } w_R > 5.0\text{ g} \end{cases}$$
  *(where $w_{\text{ref}}$ is the nominal reference ball weight, default $100.0\text{ g}$)*.

#### C. Cubic Polynomial Spatial Mapping
The non-linear elasticity and torque transfer of the load cell linkages are mapped to metric spatial coordinates $y_{\text{raw}} \in [-0.22\text{ m}, +0.22\text{ m}]$ using a 3rd-order polynomial fit:

$$y_{\text{raw}} = c_3 \cdot r^3 + c_2 \cdot r^2 + c_1 \cdot r + c_0$$

Where nominal coefficients are $c_0 = 0.0, c_1 = 0.22, c_2 = 0.0, c_3 = 0.0$.

#### D. Dynamic Online Coordinate Calibration
When visual tracking confidence is high ($C_{\text{vision}} \ge 0.8$) and scale weight is reliable, the system dynamically updates the polynomial coefficients $[c_0, c_1, c_2, c_3]$ using real-time gradient descent to correct for physical scale drift:

$$e_{\text{map}} = y_{\text{vision}} - y_{\text{pred}}, \quad \text{where } y_{\text{pred}} = \sum_{j=0}^{3} c_j \cdot r^j$$
$$c_0 \leftarrow c_0 + \eta \cdot e_{\text{map}}$$
$$c_1 \leftarrow c_1 + \eta \cdot e_{\text{map}} \cdot r$$
$$c_2 \leftarrow c_2 + (0.5 \eta) \cdot e_{\text{map}} \cdot r^2$$
$$c_3 \leftarrow c_3 + (0.25 \eta) \cdot e_{\text{map}} \cdot r^3$$
*($\eta = 0.02$, bounded by physical constraints $c_0 \in [-0.15, 0.15], c_1 \in [0.05, 0.60], c_2, c_3 \in [-0.25, 0.25]$)*.

---

### 3.3 Confidence-Weighted Sensor Fusion (`FusionBallEstimator`)

When operating in `fusion` mode, the state vectors from the vision tracker ($\mathbf{x}_v, C_v$) and force estimator ($\mathbf{x}_f, C_f$) are fused using dynamic confidence weighting:

$$y_{\text{fused}} = \frac{C_v \cdot y_v + C_f \cdot y_f}{C_v + C_f}, \quad v_{y, \text{fused}} = \frac{C_v \cdot v_{y, v} + C_f \cdot v_{y, f}}{C_v + C_f}$$

If the overhead camera is obstructed ($C_v \rightarrow 0.10$), $y_{\text{fused}}$ seamlessly transitions to load-cell force tracking without discontinuous step jumps in output tilt.

---

## 4. Movement & Control Algorithms

### 4.1 Physics Equations of Motion

The dynamic model of a sphere of mass $m$, radius $R$, and rotational moment of inertia $I = \frac{2}{5} m R^2$ rolling without slipping on a plate tilted by angle $\theta$ along position axis $s$ is derived via the Euler-Lagrange formulation:

$$\left( m + \frac{I}{R^2} \right) \ddot{s} = m g \sin(\theta) - \beta \dot{s}$$

Substituting $I = \frac{2}{5} m R^2$ yields the effective mass scaling factor $J = \frac{7}{5} m$:

$$\frac{7}{5} m \ddot{s} = m g \sin(\theta) - \beta \dot{s} \implies \ddot{s} = \frac{5}{7} g \sin(\theta) - \beta \dot{s}$$

For small angles $\sin(\theta) \approx \theta$, the linearized state-space form is:

$$\begin{bmatrix} \dot{s} \\ \ddot{s} \end{bmatrix} = \begin{bmatrix} 0 & 1 \\ 0 & -\beta \end{bmatrix} \begin{bmatrix} s \\ \dot{s} \end{bmatrix} + \begin{bmatrix} 0 \\ \frac{5}{7}g \end{bmatrix} \theta$$

---

### 4.2 Predictive PD / PID Control Law

To eliminate phase lag and prevent overshoot oscillations, the controller evaluates a **predictive position error** $e_{\text{pred}}$ using velocity-based forward projection over a lookahead time $t_{\text{lookahead}} \in [0.08\text{ s}, 0.16\text{ s}]$:

$$e_{\text{pred}}(t) = s(t) + v_y(t) \cdot t_{\text{lookahead}} - s_{\text{target}}(t)$$

The commanded correction signal $u(t)$ combines predictive proportional, derivative, and anti-windup integral terms:

$$u_P(t) = K_{p, \text{eff}} \cdot e_{\text{pred}}(t)$$
$$u_D(t) = K_{d, \text{eff}} \cdot v_y(t)$$
$$\text{Int}(t) = \text{clamp}\left( \text{Int}(t-1) + e(t) \cdot \Delta t, \; -0.15, \; +0.15 \right)$$
$$u_I(t) = K_{i, \text{eff}} \cdot \text{Int}(t)$$

$$\text{Correction} = - \left( u_P(t) + u_D(t) + u_I(t) \right) \cdot 650.0 \cdot S_{\text{multiplier}}$$

*(where $650.0$ is the tilt scaling gain and $S_{\text{multiplier}} \in [0.1, 2.0]$ is the user-configured speed factor)*.

---

### 4.3 Scenario-Aware Adaptive Gain Scheduling

At every control cycle ($50\text{ Hz}$), the backend classifies ball kinematics into five operational regimes and adjusts gain scales dynamically:

| Motion Scenario | Classification Trigger Condition | Lookahead ($t_{\text{lh}}$) | Effective Gains Adjustment |
| :--- | :--- | :--- | :--- |
| **`STUCK_RECOVERY`** | $|e| > 2\text{ cm}, \; \|v_y\| < 0.5\text{ cm/s}, \; t_{\text{stuck}} > 0.5\text{ s}$ | $0.10\text{ s}$ | $K_p, \; K_d, \; 1.5 \cdot K_i$ |
| **`FINE_TUNING`** | $|e| < 2\text{ cm}, \; \|v_y\| < 3\text{ cm/s}$ | $0.08\text{ s}$ | $0.8 \cdot K_p, \; 1.5 \cdot K_d, \; 1.5 \cdot K_i$ |
| **`EMERGENCY_RETRIEVE`**| $|e| > 8\text{ cm}, \; e \cdot v_y \ge 0$ (ball rolling away) | $0.12\text{ s}$ | $1.6 \cdot K_p, \; 1.4 \cdot K_d, \; K_i$ |
| **`PREEMPTIVE_BRAKING`**| $e \cdot v_y < -0.005, \; \|v_y\| > 5\text{ cm/s}$ (fast return) | $0.16\text{ s}$ | $0.7 \cdot K_p, \; 1.3 \cdot K_d, \; K_i$ |
| **`NOMINAL`** | Default steady tracking | $0.10\text{ s}$ | $K_p, \; K_d, \; K_i$ |

---

### 4.4 Online System Identification (RLS / LMS Parameter Learning)

The plant is modeled linearly as $\ddot{s}_k = a \cdot u_{k-1} + b \cdot v_{k-1}$, where:
* $a$: **Control Authority** (acceleration generated per unit of normalized tilt input $u = \frac{\Delta \theta}{100.0}$).
* $b$: **Rolling Resistance / Damping** (velocity decay rate).

#### Algorithm:
1. **Measured Acceleration**:
   $$\text{acc}_k = \frac{v_{y, k} - v_{y, k-1}}{\Delta t}$$
2. **Model Prediction**:
   $$\hat{\text{acc}}_k = \hat{a}_k \cdot u_{k-1} + \hat{b}_k \cdot v_{y, k-1}$$
3. **Prediction Error**:
   $$e_{\text{sys}, k} = \text{acc}_k - \hat{\text{acc}}_k$$
4. **Gradient Descent Update (LMS)**:
   $$\hat{a}_{k+1} = \text{clamp}\left( \hat{a}_k + \gamma_a \cdot e_{\text{sys}, k} \cdot u_{k-1}, \; 0.1, \; 3.0 \right)$$
   $$\hat{b}_{k+1} = \text{clamp}\left( \hat{b}_k + \gamma_b \cdot e_{\text{sys}, k} \cdot v_{y, k-1}, \; -1.0, \; 0.2 \right)$$
   *($\gamma_a = \gamma_b = 0.015$; updates trigger only when $\|v_y\| > 0.2\text{ cm/s}$ or $\|u\| > 0.02$)*.

#### Analytic Critical Damping Auto-Tuning (`auto_tune_enabled`):
When auto-tuning is enabled, target natural frequency $\omega_n$ is assigned based on scenario (e.g. $\omega_n = 3.2 \cdot S_{\text{multiplier}}$ for `NOMINAL`), and Gains $K_p, K_d$ are calculated directly from parameter estimates $\hat{a}, \hat{b}$:

$$K_p = \text{clamp}\left( \frac{\omega_n^2}{\hat{a}}, \; 0.4, \; 2.8 \right), \quad K_d = \text{clamp}\left( \frac{2 \omega_n + \hat{b}}{\hat{a}}, \; 0.15, \; 1.2 \right)$$

---

### 4.5 Active Model Exploration (Persistent Excitation)

Parameter convergence via RLS requires the input signals to satisfy **Persistent Excitation (PE)**. If the ball is balanced perfectly at the center ($e \rightarrow 0, v \rightarrow 0$), $\text{acc}_k \rightarrow 0$, causing estimation updates to stall.

When **Active Exploration Mode** is enabled:
1. If $|e - s_{\text{target}}| < 2\text{ cm}$ and $\|v_y\| < 5\text{ cm/s}$ continuously for $t_{\text{balanced}} \ge 1.5\text{ s}$, the system shifts $s_{\text{target}}$ along a sequence of excitation setpoints:
   $$s_{\text{target}} \in [0.0\text{ m}, \; +0.08\text{ m}, \; 0.0\text{ m}, \; -0.08\text{ m}]$$
2. These periodic setpoint shifts force the ball into controlled motion, continually exciting the system state space and driving $\hat{a}$ and $\hat{b}$ to their true physical values.

---

### 4.6 Backlash Hysteresis Compensation & Joint Target Conversion

#### A. Gentle Adaptive Incline Bias
To counter structural plate tilting or uncalibrated mounting offsets, an adaptive bias $\theta_{\text{adaptive}}$ accumulates when moving away from center:

$$\theta_{\text{adaptive}} \leftarrow \text{clamp}\left( \theta_{\text{adaptive}} - 200.0 \cdot e \cdot \Delta t, \; -\frac{\text{Limit}_{\text{neg}}}{2}, \; +\frac{\text{Limit}_{\text{pos}}}{2} \right)$$

#### B. Gear Hysteresis Offset
To counter mechanical gear backlash when reversing servo direction:

$$\text{backlash\_comp} = \begin{cases} +15.0\text{ ticks} & \text{if direction changes from } -1 \rightarrow +1 \\ -15.0\text{ ticks} & \text{if direction changes from } +1 \rightarrow -1 \end{cases}$$

#### C. Absolute Joint Tick Calculation
Target tilt is combined with the calibrated zero-tilt joint offset ($\text{Center}_{\text{L5Y}}$, loaded from `chiman_calibration.json`):

$$\theta_{\text{raw}} = \text{Center}_{\text{L5Y}} \pm \left( \text{Correction} + \theta_{\text{adaptive}} \right) + \text{backlash\_comp}$$
$$\theta_{\text{final}} = \text{clamp}\left( \text{Center}_{\text{L5Y}} - \text{Limit}_{\text{neg}}, \; \text{Center}_{\text{L5Y}} + \text{Limit}_{\text{pos}}, \; \theta_{\text{raw}} \right)$$

---

## 5. System Evolution: 1D Vision Balancing to 2D Load-Cell Fusion

The development of the OSRS Ball Balancer progressed through four distinct engineering phases:

```
[ Phase 1: 1D Vision ] ──► [ Phase 2: 2D Multi-Axis ] ──► [ Phase 3: Dual HX711 Scale ] ──► [ Phase 4: Full Hybrid Fusion ]
Single Pitch Axis          Pitch + Roll Coupling        Force Coordinate Estimator      Confidence Blended Estimator
Webcam Tracking            4-Servo Dual-Arm Link        80Hz Serial Streaming           Zero-Latency + Occlusion Safe
```

### Phase 1: 1D Single-Axis Vision Balancing
* **Setup**: Single pitch joint (L5Y), single overhead webcam tracking HSV color contours.
* **Limitations**: Highly sensitive to camera frame drops (30 Hz maximum rate), exposure changes, lighting reflections, and lack of roll-axis stabilization.

### Phase 2: 2D Multi-Axis Kinematic Coupling
* **Setup**: Coordinated pitch ($\theta$) and roll ($\phi$) control using dual-arm waist/shoulder joints (L5Y/L6R and R5Y/R6R).
* **Advancements**: Enabled circular setpoint trajectories ($s_x(t) = R \cos(\omega t), s_y(t) = R \sin(\omega t)$).

### Phase 3: Dual HX711 Load-Cell Integration
* **Setup**: Mounted HX711 strain-gauge load cells beneath the balancing plate, sampled at 80 Hz via Arduino serial firmware.
* **Advancements**: Removed vision reaction lag. Developed 3rd-order cubic polynomial spatial mapping ($y = \sum c_j r^j$) to translate differential mass ratios into physical coordinates.

### Phase 4: Hybrid Fusion & Self-Learning Architecture (Current State)
* **Setup**: `FusionBallEstimator` combining RealSense 3D camera deprojection with HX711 load cell scales.
* **Advancements**: Live online RLS plant parameter estimation ($\hat{a}, \hat{b}$), active excitation exploration orbits, scenario-aware predictive PD control, and automated stuck-ball reset dislodging sequences.

---

## 6. Complete Closed-Loop Execution Flow

A single iteration of the 50 Hz balancing execution loop follows this exact computational pipeline:

```
[1. Sensor Sampling] ──► [2. State Provider] ──► [3. RLS Plant Update] ──► [4. Scenario Classifier] ──► [5. Predictive PD] ──► [6. Hardware Write]
Read Camera/Serial       Compute y_fused & v_y   Update est_a & est_b      Select Lookahead & Gains  Compute target_tilt     GroupSyncWrite Ticks
```

1. **Sensor Sampling**: OpenCV captures frame; Arduino streams HX711 raw weights ($w_L, w_R$) over USB serial.
2. **State Estimation**: Active provider (`FusionBallEstimator`) computes fused position $y_{\text{fused}}$ and EMA velocity $v_{y, \text{fused}}$.
3. **Online RLS Identification**: System computes measured acceleration $\text{acc}_k = \frac{\Delta v_y}{\Delta t}$, computes error against predicted acceleration, and updates parameters $\hat{a}$ and $\hat{b}$.
4. **Scenario Classification**: Kinematics evaluate thresholds to set current scenario (e.g. `PREEMPTIVE_BRAKING`), setting lookahead time $t_{\text{lookahead}}$ and effective gains $K_p, K_d, K_i$.
5. **Predictive PD Calculation**: Controller computes forward projected error $e_{\text{pred}} = y + v_y \cdot t_{\text{lookahead}} - y_{\text{target}}$, evaluates PD terms, applies adaptive incline bias, and adds backlash compensation.
6. **Hardware Write**: Target servo ticks are clamped to calibration bounds (`chiman_calibration.json`) and dispatched asynchronously to Dynamixel servos via `GroupSyncWrite`. Telemetry frame is published over WebSocket `/ws/telemetry`.

---

## 7. Conclusion

The OSRS Ball Balancer research module demonstrates a highly versatile control and perception framework. By combining predictive PD control, scenario-aware gain scheduling, dynamic load cell polynomial mapping, confidence-weighted sensor fusion, and active persistent excitation RLS learning, the platform achieves robust, real-time ball stabilization and dynamic parameter identification.

---
*Document persistently saved to [docs/BALL_BALANCER_RESEARCH_PAPER.md](file:///e:/Projects/OSRS/OSRS/docs/BALL_BALANCER_RESEARCH_PAPER.md).*
