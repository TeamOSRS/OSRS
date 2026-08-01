# Ball Balancing Control & System Identification Research Module

This document provides a comprehensive overview of the **Ball Balancer** research module inside the Open Source Robotics Suite (OSRS). It explains the physical system, research goals, engineering rationale, underlying mathematical principles, and software implementation details.

---

## 1. What is it? (System Description)
The OSRS Ball Balancer is a closed-loop under-actuated robotic control system designed to stabilize a rolling ball at a commanded coordinate on a flat plate. 

### Hardware Architecture
* **Active Platform**: A horizontal plate supported by a dual-axis mechanical linkage driven by high-torque **Dynamixel actuators** (e.g., XC330 series). Roll and pitch servo joints manipulate the plate’s tilt angle ($\theta$).
* **Perception Sensors**:
  * **Computer Vision**: An overhead RGB/depth camera (e.g., Intel RealSense D435) tracking the ball's coordinates in real-time.
  * **Force scale**: High-speed **HX711 load cell scales** measuring weight distribution coordinates at 80Hz.
* **Controller**: A centralized control loop thread running in the Python backend at 50Hz, broadcasting telemetry outputs via WebSockets to the frontend user interface.

---

## 2. What is the Goal?
The primary research objectives of this platform are:
1. **Active Stabilization**: Dynamically stabilizing the ball ($x, y$ center coordinates) at a static setpoint ($0.0, 0.0$) or along pre-defined orbits (e.g., circular tracks, infinity loop trajectories).
2. **Online System Identification**: Tracking changing system dynamics—such as rolling friction, air resistance, or mass changes—during run-time without offline parameter fitting.
3. **Adaptive Control Tuning**: Self-tuning control loop parameters (PID gains) using live estimates of control authority and damping parameters.
4. **Sensor Fusion**: Fusing heterogeneous inputs (high-latency visual coordinates and low-latency load cell raw weights) to maintain coordinate tracking under partial sensor occlusions.

---

## 3. Why? (Research & Engineering Rationale)
The ball-on-plate system is a classic control theory benchmark. It exhibits several challenging properties:
* **Under-actuated Dynamics**: The system has fewer control inputs (2 tilt angles) than degrees of freedom (4 states: $x, y, v_x, v_y$).
* **Open-loop Instability**: A ball on a flat plate is marginally stable, and any tilt angle causes it to accelerate away from the center. Its open-loop transfer function contains poles at the origin or in the right-half plane.
* **Non-linear Noise**: Real-world rolling objects encounter static/kinetic friction, surface irregularities, camera jitter, and signal transmission latencies.
* **Dual-source Fusion**: It serves as an excellent testbed for studying Kalman Filters, Recursive Least Squares (RLS), and sensor confidence weighting under physical constraints.

---

## 4. Underlying Control & Identification Principles

### A. Equations of Motion (Physics Model)
The dynamics of a spherical ball of mass $m$ and radius $R$ rolling without slipping on a plate tilted by angle $\theta$ is modeled as:

$$J \ddot{s} = m g \sin(\theta) - F_{\text{friction}}$$

Where:
* $s$ is the position of the ball along the plate coordinate axis.
* $g$ is the acceleration due to gravity ($9.81 \, \text{m/s}^2$).
* $J$ is the effective translational inertia scaling factor incorporating the rotational moment of inertia ($I$). For a solid sphere where $I = \frac{2}{5} m R^2$:
  $$J = m + \frac{I}{R^2} = m + \frac{2}{5}m = \frac{7}{5}m$$
* This yields the simplified acceleration equation (with linear damping $\beta$ representing friction):
  $$\ddot{s} = \frac{5}{7} g \sin(\theta) - \beta \dot{s}$$

---

### B. Proportional-Integral-Derivative (PID) Control
To balance the ball, OSRS computes a target tilt angle $\theta_{\text{target}}$ using the tracking error $e(t) = s_{\text{target}}(t) - s(t)$:

$$\theta_{\text{target}}(t) = K_p e(t) + K_i \int_{0}^{t} e(\tau) d\tau + K_d \frac{de(t)}{dt}$$

* **Proportional ($K_p$)**: Corrects plate tilt relative to displacement from the center.
* **Integral ($K_i$)**: Minimizes steady-state error caused by plate leveling misalignment or surface slope errors.
* **Derivative ($K_d$)**: Acts as a damping force to counter the ball's momentum and prevent overshoot oscillations.

---

### C. Online System Identification (Recursive Least Squares)
The system is modeled as a linear system:

$$\ddot{s}(t) = a \cdot \theta(t) + b \cdot \dot{s}(t)$$

Where:
* $a$ represents the **Control Authority** (acceleration per unit of tilt angle).
* $b$ represents the **Friction/Damping Coefficient** (rolling resistance).

Using a **Recursive Least Squares (RLS)** estimator with a forgetting factor $\lambda \in [0.95, 0.99]$, the backend updates the parameter estimates $\hat{\mathbf{\theta}} = [a, b]^T$ at every control cycle:

$$\mathbf{\phi}(t) = [\theta(t), \dot{s}(t)]^T$$
$$\mathbf{K}(t) = \frac{\mathbf{P}(t-1) \mathbf{\phi}(t)}{\lambda + \mathbf{\phi}(t)^T \mathbf{P}(t-1) \mathbf{\phi}(t)}$$
$$\hat{\mathbf{\theta}}(t) = \hat{\mathbf{\theta}}(t-1) + \mathbf{K}(t) \left[ \ddot{s}(t) - \mathbf{\phi}(t)^T \hat{\mathbf{\theta}}(t-1) \right]$$
$$\mathbf{P}(t) = \frac{1}{\lambda} \left[ \mathbf{P}(t-1) - \mathbf{K}(t) \mathbf{\phi}(t)^T \mathbf{P}(t-1) \right]$$

This mathematical process allows the platform to self-identify if a heavier or friction-intensive ball (like a chrome ball) is placed on the plate instead of a ping-pong ball.

---

### D. Active Exploration Mode
To ensure the RLS estimator gathers informative data, the system must satisfy the condition of **Persistent Excitation (PE)**. In static balancing, states converge to zero, causing the parameter estimation matrices to become ill-conditioned. 

When **Active Exploration** is enabled, the plate injects small sinusoidal orbit signals:

$$\theta_{\text{exploration}}(t) = A_{\text{orbit}} \sin(\omega t)$$

These exploratory orbits keep the ball in motion, generating sufficient dynamic data to converge the parameters $a$ and $b$ accurately.

---

### E. Confidence-Weighted Sensor Fusion
Coordinates are retrieved from two sources with varying reliability:
1. **Vision Tracker** ($y_v$, high reliability, but subject to frame-rate latency or physical line-of-sight occlusion).
2. **Force Scales** ($y_f$, low latency, but noisy and susceptible to high-frequency impacts).

The fused state coordinate estimate $y_{\text{fused}}$ is computed as:

$$y_{\text{fused}} = \frac{C_{\text{vision}} \cdot y_v + C_{\text{force}} \cdot y_f}{C_{\text{vision}} + C_{\text{force}}}$$

Where $C_{\text{vision}}$ and $C_{\text{force}}$ are dynamic confidence ratings. If visual tracking is lost (e.g., hand blocking the camera lens), $C_{\text{vision}} \rightarrow 0.0$, and the system automatically falls back to force scale tracking.

---

## 5. Software Modules Implementation

* **State Providers** (`src/modules/research/ball_balancer.py`):
  * `VisionBallTracker`: Smooths coordinates with an Exponential Moving Average (EMA) filter.
  * `ForceBallEstimator`: Converts raw weight differentials from load cells into position coordinates using a cubic polynomial calibration model:
    $$y = c_3 \cdot \text{ratio}^3 + c_2 \cdot \text{ratio}^2 + c_1 \cdot \text{ratio} + c_0$$
  * `FusionBallEstimator`: Performs confidence-weighted coordinates blending.
* **Stuck-Ball Detection**: Monitors coordinates and velocities. If tracking error remains high ($|e| > 4 \, \text{cm}$) and velocity remains low ($|v| < 0.8 \, \text{cm/s}$) for over 2 seconds, the controller injects a recovery tilt sequence to dislodge the ball.
* **Data Persistence**: Calibrated load cell parameters and system estimates are serialized directly to `balancer_learning_data.json` at run-time.
