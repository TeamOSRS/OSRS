# Mathematics, Physics, and Control Theory of Cooperative Dual-Arm Plate Balancing

This document provides a rigorous, research-level mathematical and physical analysis of the cooperative dual-arm plate balancing system. It details the coordinate systems, rolling sphere physics, height-based PID control optimizations, numerical Inverse Kinematics (IK), and the mathematical formulations of all tracking and control errors.

---

## 1. System Kinematics and Coordinate Frames

To analyze the multi-body system, we define the following reference frames:
*   **World Frame $\{W\}$**: Origin located on the groundplane centered between the two robot bases. The $Z_W$ axis is vertical (opposite to gravity), $X_W$ points toward the right base, and $Y_W$ points forward.
*   **Left/Right Grasp Sites $\{S_L\}, \{S_R\}$**: The coordinate frames of the slots where the arm end-effectors grasp the plate couplers. Located at local offsets from the plate center:
    $$\mathbf{p}_{L,\text{local}} = \begin{bmatrix} -L_p \\ 0 \\ 0 \end{bmatrix}, \quad \mathbf{p}_{R,\text{local}} = \begin{bmatrix} L_p \\ 0 \\ 0 \end{bmatrix}$$
    where $L_p = 0.2758\text{ m}$ represents the leverage arm length (distance from plate center to the grasp slots).

### Forward Kinematics of the Plate
Let $\theta$ denote the pitch angle of the plate (rotation around $Y_W$). The rotation matrix of the plate $\mathbf{R}_P(\theta) \in SO(3)$ is:
$$\mathbf{R}_P(\theta) = \begin{bmatrix} \cos\theta & 0 & \sin\theta \\ 0 & 1 & 0 \\ -\sin\theta & 0 & \cos\theta \end{bmatrix}$$

The desired position of the left and right grasp sites in $\{W\}$ as a function of plate tilt $\theta$ is:
$$\mathbf{p}_{L,\text{target}} = \begin{bmatrix} -L_p\cos\theta \\ 0 \\ z_{\text{nominal}} + L_p\sin\theta \end{bmatrix}, \quad \mathbf{p}_{R,\text{target}} = \begin{bmatrix} L_p\cos\theta \\ 0 \\ z_{\text{nominal}} - L_p\sin\theta \end{bmatrix}$$
where $z_{\text{nominal}} = 0.20\text{ m}$ is the default plate height.

For height-based control, we command a vertical displacement $\Delta z$ of the arms. Comparing these with the geometric target equations, we establish the exact mapping between vertical command $\Delta z$ and plate tilt $\theta$:
$$\Delta z = L_p \sin\theta \implies \theta = \arctan2\left(2\Delta z, d_{\text{plate}}\right)$$
where $d_{\text{plate}} = 2 L_p = 0.5516\text{ m}$ is the total distance between the end-effector grasp slots.

---

## 2. Physics of the Rolling Sphere on a Tilting Plate

The ball is modeled as a uniform solid sphere of mass $m$, radius $r$, and moment of inertia $I = \frac{2}{5}mr^2$. The sphere rolls without slipping along a channel on the plate.

Let $x$ denote the position of the ball along the plate's longitudinal axis $\{X_P\}$, where $x=0$ is the plate's center. When the plate is tilted by angle $\theta$, the Lagrangian $\mathcal{L} = T - V$ is:
$$\mathcal{L} = \frac{7}{10}m \dot{x}^2 + m g x \sin\theta$$

Applying the Euler-Lagrange equation yields the physical equation of motion:
$$\ddot{x} = \frac{5}{7}g \sin\theta$$

Using the small-angle approximation ($\sin\theta \approx \theta$):
$$\ddot{x} \approx \frac{5}{7}g \theta$$

Taking the Laplace transform with zero initial conditions yields the transfer function:
$$\frac{X(s)}{\Theta(s)} = \frac{5g}{7s^2}$$

This is a double-integrator system, which is inherently unstable and requires derivative feedback ($K_d$) to provide damping.

---

## 3. Height-Based PID Control with Optimizations

### A. Ball Tracking Error
The primary tracking error $e(t)$ at time step $t$ is defined as the difference between the desired target position $x_{\text{target}}$ and the actual measured ball position $x(t)$ along the plate's local channel:
$$e(t) = x_{\text{target}}(t) - x(t)$$

### B. Smooth Quadratic Deadzone
To avoid gear backlash wear ("servo play") when the ball is close to the target, we filter the error through a smooth quadratic deadzone function $f(e)$:
$$e_{\text{filt}}(t) = f(e(t)) = \begin{cases} \text{sign}(e) \cdot \frac{e^2}{2\delta_d} & \text{if } |e| < \delta_d \\ e - \text{sign}(e) \cdot \frac{\delta_d}{2} & \text{otherwise} \end{cases}$$
where $\delta_d = 0.002\text{ m}$ ($2\text{ mm}$) is the deadzone width. 

This formulation provides a continuous derivative ($C^1$ continuity) across the deadzone boundary:
$$\frac{df}{de} = \begin{cases} \frac{e}{\delta_d} & \text{if } |e| < \delta_d \\ 1 & \text{otherwise} \end{cases}$$
At the boundary $|e| = \delta_d$, the derivative is exactly $1.0$, preventing control spikes.

### C. PID Control Law
The filtered error $e_{\text{filt}}(t)$ is fed into the PID control law:
$$\Delta z_{\text{raw}}(t) = K_p e_{\text{filt}}(t) + K_i \int_{0}^{t} e_{\text{filt}}(\tau) d\tau - K_d \frac{de_{\text{filt}}(t)}{dt}$$

### D. Smooth Saturation (Soft Limits) via Hyperbolic Tangent
To prevent joint command acceleration spikes near workspace limits, we saturate the output using a smooth hyperbolic tangent function:
$$\Delta z = \Delta z_{\text{max}} \tanh\left(\frac{\Delta z_{\text{raw}}}{\Delta z_{\text{max}}}\right)$$
where $\Delta z_{\text{max}} = 0.033\text{ m}$ (~3.3 cm) represents the maximum height offset.

---

## 4. Numerical Inverse Kinematics via Damped Least Squares

Let $q \in \mathbb{R}^n$ represent the joint vector, and let $\mathbf{x} \in S E(3)$ represent the end-effector pose. The forward kinematics relation is:
$$\mathbf{x} = f(q) \implies \dot{\mathbf{x}} = \mathbf{J}(q) \dot{q}$$
where $\mathbf{J}(q) \in \mathbb{R}^{6 \times n}$ is the analytical Jacobian matrix.

### IK Tracking Error
The IK solver tracks a 6D spatial error vector $\mathbf{e}_{6D} \in \mathbb{R}^6$ representing the target pose error:
$$\mathbf{e}_{6D} = \begin{bmatrix} \mathbf{e}_{\text{pos}} \\ \mathbf{e}_{\text{rot}} \end{bmatrix}$$
where:
1.  **Position Error $\mathbf{e}_{\text{pos}}$**: We relax horizontal tracking to avoid fighting rigid constraints, tracking only the vertical coordinate ($Z$):
    $$\mathbf{e}_{\text{pos}} = \begin{bmatrix} 0 \\ 0 \\ z_{\text{target}} - z_{\text{current}} \end{bmatrix}$$
2.  **Rotation Error $\mathbf{e}_{\text{rot}}$**: Computed from current rotation matrix columns ($\mathbf{R}_{\text{curr}} = [\mathbf{u}, \mathbf{v}, \mathbf{w}]$) and target rotation columns ($\mathbf{R}_{\text{target}} = [\mathbf{u}_d, \mathbf{v}_d, \mathbf{w}_d]$):
    $$\mathbf{e}_{\text{rot}} = \frac{1}{2} \left( \mathbf{u} \times \mathbf{u}_d + \mathbf{v} \times \mathbf{v}_d + \mathbf{w} \times \mathbf{w}_d \right)$$

### DLS IK Mathematical Derivation
To prevent joint velocities from spiking to infinity near singularities, we minimize the tracking error while penalizing large joint speeds:
$$\min_{\Delta q} E(\Delta q) = \min_{\Delta q} \left( \|\mathbf{J} \Delta q - \mathbf{e}_{6D}\|^2 + \lambda^2 \|\Delta q\|^2 \right)$$
where $\lambda = 0.015$ is the damping factor.

Expanding the objective function:
$$E(\Delta q) = (\mathbf{J} \Delta q - \mathbf{e}_{6D})^T (\mathbf{J} \Delta q - \mathbf{e}_{6D}) + \lambda^2 \Delta q^T \Delta q$$
$$E(\Delta q) = \Delta q^T \mathbf{J}^T \mathbf{J} \Delta q - 2 \Delta q^T \mathbf{J}^T \mathbf{e}_{6D} + \mathbf{e}_{6D}^T \mathbf{e}_{6D} + \lambda^2 \Delta q^T \Delta q$$

Taking the derivative of $E$ with respect to the joint update vector $\Delta q$:
$$\frac{\partial E}{\partial \Delta q} = 2 \mathbf{J}^T \mathbf{J} \Delta q - 2 \mathbf{J}^T \mathbf{e}_{6D} + 2 \lambda^2 \Delta q$$

To find the minimum, we set this derivative to zero:
$$\mathbf{J}^T \mathbf{J} \Delta q + \lambda^2 \Delta q = \mathbf{J}^T \mathbf{e}_{6D}$$
$$\left(\mathbf{J}^T \mathbf{J} + \lambda^2 \mathbf{I}\right) \Delta q = \mathbf{J}^T \mathbf{e}_{6D}$$

Solving for $\Delta q$ yields the Damped Least Squares IK equation:
$$\Delta q = \left(\mathbf{J}^T \mathbf{J} + \lambda^2 \mathbf{I}\right)^{-1} \mathbf{J}^T \mathbf{e}_{6D}$$

---

## 5. Actuator Command Smoothing (Low-Pass Filter)

The raw joint update targets are filtered through a first-order exponential moving average filter:
$$u_k = \alpha q_k + (1 - \alpha) u_{k-1}$$
where $q_k$ is the raw joint target, $u_k$ is the filtered command, and $\alpha = 0.25$.

### Frequency and Time Domain Characteristics
*   **Cutoff Frequency $f_c$**: The filter attenuates commands above:
    $$f_c \approx \frac{\alpha}{2 \pi \Delta t (1-\alpha)} = \frac{0.25}{2 \pi (0.002) (0.75)} \approx 23.3\text{ Hz}$$
    This filters out high-frequency numerical joint chatter from the IK solver.
*   **Time Constant $\tau$ (Latency)**:
    $$\tau \approx \frac{\Delta t}{\alpha} = \frac{0.002}{0.25} = 0.008\text{ s} = 8\text{ ms}$$
    An $8\text{ ms}$ delay is negligible for the physical plate dynamics, preventing control lag.
