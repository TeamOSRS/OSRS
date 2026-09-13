import mujoco
import mujoco.viewer
import numpy as np
import sys
import time


def _maximize_window(title_substr, timeout=3.0):
    """Best-effort maximize of the native viewer window (Windows only).

    launch_passive spawns its GLFW window on a background render thread, so we
    poll briefly for a visible top-level window whose title contains
    `title_substr` and maximize it once found.
    """
    if sys.platform != 'win32':
        return

    import ctypes

    user32 = ctypes.windll.user32
    found = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    def _enum_proc(hwnd, _lparam):
        length = user32.GetWindowTextLengthW(hwnd)
        if length > 0 and user32.IsWindowVisible(hwnd):
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            if title_substr.lower() in buf.value.lower():
                found.append(hwnd)
                return False
        return True

    deadline = time.time() + timeout
    while time.time() < deadline and not found:
        user32.EnumWindows(_enum_proc, 0)
        if not found:
            time.sleep(0.05)

    if found:
        SW_MAXIMIZE = 3
        user32.ShowWindow(found[0], SW_MAXIMIZE)


def quat_mul(q1, q2):
    """Multiplies two quaternions in [w, x, y, z] format."""
    w1, x1, y1, z1 = q1
    w2, x2, y2, z2 = q2
    return np.array([
        w1*w2 - x1*x2 - y1*y2 - z1*z2,
        w1*x2 + x1*w2 + y1*z2 - z1*y2,
        w1*y2 - x1*z2 + y1*w2 + z1*x2,
        w1*z2 + x1*y2 - y1*x2 + z1*w2
    ])

# ─────────────────────────────────────────────────────────────────
# IK Solver
# ─────────────────────────────────────────────────────────────────

class IKSolver:
    def __init__(self, model):
        self.model = model
        self.data  = mujoco.MjData(model)  # Sandbox solver iterations using private MjData

        self.franka_jnt_ids   = [model.joint(f'fr3_joint{i}').id      for i in range(1, 8)]
        self.franka_qpos_adr  = [model.joint(f'fr3_joint{i}').qposadr[0] for i in range(1, 8)]
        self.franka_dof_adr   = [model.joint(f'fr3_joint{i}').dofadr[0]  for i in range(1, 8)]

        self.heal_jnt_ids     = [model.joint(f'joint{i}').id          for i in range(1, 7)]
        self.heal_qpos_adr    = [model.joint(f'joint{i}').qposadr[0]  for i in range(1, 7)]
        self.heal_dof_adr     = [model.joint(f'joint{i}').dofadr[0]   for i in range(1, 7)]

        self.franka_ee_id = model.body('hand').id
        self.heal_ee_id   = model.body('end-effector').id

        # Plate-holding configurations (avoid singularities, validated flat grip)
        self.franka_plate_q = np.array([-0.4091, -1.3020, 0.1714, -2.9253, -1.4271,  1.9426,  0.8450])
        self.heal_plate_q   = np.array([-0.1229, -0.4379, -0.6354, -1.7579, -0.2429,  2.9555])

    def solve(self, robot, target_pos, target_quat=None, q_init=None, max_steps=50, tol=5e-4, damp=5e-3):
        """Damped Least-Squares IK. Returns (q_sol, success)."""
        if robot == 'franka':
            jnt_ids, qpos_adr, dof_adr = self.franka_jnt_ids, self.franka_qpos_adr, self.franka_dof_adr
            ee_id = self.franka_ee_id
        else:
            jnt_ids, qpos_adr, dof_adr = self.heal_jnt_ids, self.heal_qpos_adr, self.heal_dof_adr
            ee_id = self.heal_ee_id

        q_sol = self.data.qpos.copy()
        if q_init is not None:
            q_sol[:] = q_init
            self.data.qpos[:] = q_sol

        for _ in range(max_steps):
            mujoco.mj_forward(self.model, self.data)
            cur_pos = self.data.xpos[ee_id].copy()
            cur_mat = self.data.xmat[ee_id].reshape(3, 3)

            pos_err = target_pos - cur_pos

            rot_err = np.zeros(3)
            if target_quat is not None:
                tgt_mat = np.zeros(9)
                mujoco.mju_quat2Mat(tgt_mat, target_quat)
                tgt_mat = tgt_mat.reshape(3, 3)
                rel = tgt_mat @ cur_mat.T
                val = np.clip((np.trace(rel) - 1.0) / 2.0, -1, 1)
                theta = np.arccos(val)
                if abs(theta) > 1e-6:
                    ax = np.array([rel[2,1]-rel[1,2], rel[0,2]-rel[2,0], rel[1,0]-rel[0,1]])
                    rot_err = ax / (2*np.sin(theta)) * theta

            err = np.concatenate([pos_err, rot_err]) if target_quat is not None else pos_err
            if np.linalg.norm(err) < tol:
                return q_sol[qpos_adr].copy(), True

            jac_p = np.zeros((3, self.model.nv))
            jac_r = np.zeros((3, self.model.nv))
            mujoco.mj_jacBody(self.model, self.data, jac_p, jac_r, ee_id)
            J = np.vstack([jac_p, jac_r])[:, dof_adr] if target_quat is not None else jac_p[:, dof_adr]

            n_err = len(err)
            dq = J.T @ np.linalg.solve(J @ J.T + damp**2 * np.eye(n_err), err)

            q_sol[qpos_adr] += dq
            for i, jid in enumerate(jnt_ids):
                if self.model.jnt_limited[jid]:
                    lo, hi = self.model.jnt_range[jid]
                    q_sol[qpos_adr[i]] = np.clip(q_sol[qpos_adr[i]], lo, hi)
            self.data.qpos[:] = q_sol

        return q_sol[qpos_adr].copy(), False


# ─────────────────────────────────────────────────────────────────
# Cooperative Tray-Balancing Controller
# ─────────────────────────────────────────────────────────────────

class BallBalancer:
    # ── geometry ─────────────────────────────────────────────────
    PLATE_HALF_LEN = 0.20   # m  — half of 40cm (arm-to-arm axis = world Y)
    PLATE_HEIGHT   = 0.55   # m  — IK-verified

    # IK-verified EE positions with exact fingertip offsets.
    # Franka hand is at y=-0.110 (fingertips at plate +Y edge = -0.215)
    # HEAL   hand is at y=-0.730 (fingertips at plate -Y edge = -0.604)
    FRANKA_EE_NOMINAL = np.array([ 0.20, -0.110,  0.55])
    HEAL_EE_NOMINAL   = np.array([ 0.20, -0.730,  0.55])

    # Target orientations for flat grip
    FRANKA_QUAT = np.array([0.70710678, 0.70710678, 0.0, 0.0])
    HEAL_QUAT   = np.array([0.5, 0.5, -0.5, 0.5])

    # ── IK control rate ──────────────────────────────────────────
    IK_UPDATE_HZ  = 50  # how often to re-solve IK (Hz) — higher = smoother joint motion

    # Keep requested targets away from the physical edge (half-extent 0.20m) so that
    # transient overshoot during convergence can't roll the ball off the plate.
    TARGET_SAFE_MARGIN = 0.12

    # Random ball spawn point is drawn from within this margin of the plate centre.
    SPAWN_MARGIN = 0.15

    # Low-pass smoothing applied to the commanded plate tilt every physics step
    # (500Hz), to stop PID/noise-driven jitter from turning into jerky arm motion.
    TILT_SMOOTH_ALPHA = 0.02

    def __init__(self, model, data, target_point=(0.0, 0.0)):
        self.model = model
        self.data  = data
        self.ik    = IKSolver(model)

        self.plate_id = model.body('plate').id
        self.ball_id  = model.body('ball').id

        # qpos start addresses of the plate's and ball's freejoints, so we can
        # randomize/read their position directly without needing a forward pass.
        self.plate_qpos_adr = model.jnt_qposadr[model.body('plate').jntadr[0]]
        self.ball_qpos_adr  = model.jnt_qposadr[model.body('ball').jntadr[0]]

        # Actuator control addresses
        self.franka_act  = [model.actuator(f'fr3_joint{i}').id for i in range(1, 8)]
        self.heal_act    = [model.actuator(n).id for n in
                            ['turret','shoulder','elbow','wrist_1','wrist_2','wrist_3']]
        # Gripper actuators
        self.franka_gripper_act = model.actuator('actuator8').id
        self.heal_gripper_act   = model.actuator('heal_gripper').id

        # Close positions
        self.FRANKA_GRIP_CLOSE = 0.0
        self.HEAL_GRIP_CLOSE   = 0.725

        # Initialize configurations from keyframe values
        self.franka_q = self.ik.franka_plate_q.copy()
        self.heal_q   = self.ik.heal_plate_q.copy()

        self._last_ik_t   = -999.0
        self._initialized = False

        # --- Ball-on-Plate PID State ---
        # Target point for the ball, expressed in the plate's own local XY frame
        # (0, 0) = plate centre. Plate half-extent is PLATE_HALF_LEN in each axis.
        self.target_point = np.clip(np.array(target_point, dtype=float),
                                     -self.TARGET_SAFE_MARGIN, self.TARGET_SAFE_MARGIN)

        self.ball_local_filt = None   # filtered ball position in plate-local frame (x, y)
        self.ball_vel_filt   = np.zeros(2)
        self.last_ball_local = None
        self.last_time       = 0.0

        self.integral_x = 0.0
        self.integral_y = 0.0
        self.INTEGRAL_LIMIT = 0.6  # anti-windup clamp on the accumulated (error * dt) term

        # PID gains (position error -> desired plate tilt angle, radians)
        # Tuned for a ~0.1kg ball on a ~0.4m plate, gravity-driven dynamics.
        self.K_p = 0.85
        self.K_i = 0.18
        self.K_d = 0.55

        self.MAX_ROLL_RAD  = 0.0700   # ~4 deg max roll  (about plate local Y axis, controls X motion)
        self.MAX_PITCH_RAD = 0.0700   # ~4 deg max pitch (about plate local X axis, controls Y motion)

        # Smoothed tilt commands actually sent to the IK targets (see TILT_SMOOTH_ALPHA)
        self.phi_cmd   = 0.0
        self.theta_cmd = 0.0

        # Register control callback for real-time tracking
        def control_callback(model, data):
            # Apply gravity compensation to avoid sagging
            data.qfrc_applied[:] = data.qfrc_gravcomp

            if self._initialized:
                # Return immediately if called for sandbox data!
                if data is not self.data:
                    return
                self._control_step(model, data)

        mujoco.set_mjcb_control(control_callback)

    def set_target(self, x, y):
        """Move the ball's target point (plate-local XY, metres from plate centre)."""
        self.target_point = np.clip(np.array([x, y], dtype=float),
                                     -self.TARGET_SAFE_MARGIN, self.TARGET_SAFE_MARGIN)
        self.integral_x = 0.0
        self.integral_y = 0.0

    def _control_step(self, model, data):
        """Internal control step executed on every physics timestep inside the callback.

        Reads the ball's true position/velocity relative to the plate (both are
        free-jointed bodies in the model) and runs a PID controller that outputs
        a desired plate pitch/roll, mimicking how a person tilts a tray by hand
        to roll a ball toward a target point.
        """
        # 1. Ball position relative to the plate, expressed in the plate's local frame
        plate_pos = data.xpos[self.plate_id]
        plate_mat = data.xmat[self.plate_id].reshape(3, 3)
        ball_pos  = data.xpos[self.ball_id]

        ball_local = plate_mat.T @ (ball_pos - plate_pos)
        ball_local_xy = ball_local[:2]

        # 2. Light low-pass filter on position, and a filtered finite-difference velocity
        if self.ball_local_filt is None:
            self.ball_local_filt = ball_local_xy.copy()
            self.last_ball_local = ball_local_xy.copy()
            self.last_time = data.time

        alpha_pos = 0.15
        self.ball_local_filt = alpha_pos * ball_local_xy + (1.0 - alpha_pos) * self.ball_local_filt

        dt = data.time - self.last_time
        if dt > 0:
            vel_raw = (self.ball_local_filt - self.last_ball_local) / dt
            alpha_vel = 0.08
            self.ball_vel_filt = alpha_vel * vel_raw + (1.0 - alpha_vel) * self.ball_vel_filt
        self.last_ball_local = self.ball_local_filt.copy()
        self.last_time = data.time

        # 3. PID error terms (position error = current - target; zero error = ball at rest on target)
        error = self.ball_local_filt - self.target_point   # [error_x, error_y]

        # Only integrate once the ball is (roughly) placed on the plate & settling, to avoid windup
        # during the initial drop/transient.
        if data.time > 0.5:
            self.integral_x = np.clip(self.integral_x + error[0] * dt, -self.INTEGRAL_LIMIT, self.INTEGRAL_LIMIT)
            self.integral_y = np.clip(self.integral_y + error[1] * dt, -self.INTEGRAL_LIMIT, self.INTEGRAL_LIMIT)

        # 4. PID -> desired plate tilt angles.
        # Rotating the plate about its local X axis (pitch, phi) by +phi raises the +Y edge,
        # so a ball with error_y > 0 (past the target, toward +Y) needs +phi to roll it back.
        phi_des = (self.K_p * error[1] + self.K_i * self.integral_y + self.K_d * self.ball_vel_filt[1])
        phi_des = np.clip(phi_des, -self.MAX_PITCH_RAD, self.MAX_PITCH_RAD)

        # Rotating the plate about its local Y axis (roll, theta) by +theta LOWERS the +X edge,
        # so a ball with error_x > 0 needs -theta to raise the +X edge and roll it back.
        theta_des = -(self.K_p * error[0] + self.K_i * self.integral_x + self.K_d * self.ball_vel_filt[0])
        theta_des = np.clip(theta_des, -self.MAX_ROLL_RAD, self.MAX_ROLL_RAD)

        if data.time < 0.5:
            # Let the ball settle onto the plate before actively tilting it.
            phi_des = 0.0
            theta_des = 0.0

        # 5. Low-pass filter the tilt command itself (on top of the PID output) so that
        # any remaining jitter turns into smooth, gradual arm motion instead of jerks.
        self.phi_cmd   += self.TILT_SMOOTH_ALPHA * (phi_des - self.phi_cmd)
        self.theta_cmd += self.TILT_SMOOTH_ALPHA * (theta_des - self.theta_cmd)

        # 6. Apply desired rotations to consistent coordinate targets
        p_plate = np.array([0.20, -0.40, 0.55])

        q_pitch = np.array([np.cos(self.phi_cmd/2), np.sin(self.phi_cmd/2), 0.0, 0.0])
        q_roll = np.array([np.cos(self.theta_cmd/2), 0.0, np.sin(self.theta_cmd/2), 0.0])
        q_plate = quat_mul(q_roll, q_pitch)
        
        R_plate = np.zeros(9)
        mujoco.mju_quat2Mat(R_plate, q_plate)
        R_plate = R_plate.reshape(3, 3)
        
        franka_target = p_plate + R_plate @ np.array([0.0, 0.29, 0.0])
        heal_target = p_plate + R_plate @ np.array([0.0, -0.33, 0.0])
        
        franka_quat = quat_mul(q_plate, self.FRANKA_QUAT)
        # HEAL target_quat is None so orientation complies naturally, avoiding closed-loop fighting

        # ── 7. Re-solve IK at throttled rate ─────────────────────
        sim_time = data.time
        dt_ik = sim_time - self._last_ik_t
        if dt_ik >= 1.0 / self.IK_UPDATE_HZ:
            self._last_ik_t = sim_time

            # Franka IK (solving for both position and orientation)
            q_init_f = data.qpos.copy()
            q_init_f[self.ik.franka_qpos_adr] = self.franka_q
            q_f, ok_f = self.ik.solve('franka', franka_target, target_quat=franka_quat, q_init=q_init_f, max_steps=20)
            if ok_f:
                self.franka_q = q_f

            # HEAL IK (solving for position ONLY)
            q_init_h = data.qpos.copy()
            q_init_h[self.ik.heal_qpos_adr] = self.heal_q
            q_h, ok_h = self.ik.solve('heal', heal_target, target_quat=None, q_init=q_init_h, max_steps=20)
            if ok_h:
                self.heal_q = q_h

        # ── 8. Apply control ──────────────────────────────────────
        for i, act_id in enumerate(self.franka_act):
            data.ctrl[act_id] = self.franka_q[i]
        for i, act_id in enumerate(self.heal_act):
            data.ctrl[act_id] = self.heal_q[i]

        # Keep grippers securely closed on plate edges
        data.ctrl[self.franka_gripper_act] = self.FRANKA_GRIP_CLOSE
        data.ctrl[self.heal_gripper_act]   = self.HEAL_GRIP_CLOSE

    def reset(self, randomize_ball=True):
        """Resets simulation state by loading Keyframe 0 (plate-holding posture)."""
        mujoco.mj_resetDataKeyframe(self.model, self.data, 0)

        # Randomize the ball's spawn point within a safe margin of the (flat) plate centre,
        # keeping its resting height/orientation from the keyframe. The PID controller then
        # has to actively roll it back to the target point instead of starting there.
        if randomize_ball:
            plate_xy = self.data.qpos[self.plate_qpos_adr:self.plate_qpos_adr + 2]
            offset = np.random.uniform(-self.SPAWN_MARGIN, self.SPAWN_MARGIN, size=2)
            self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr + 2] = plate_xy + offset

        # Seed the controller targets
        self.franka_q = self.ik.franka_plate_q.copy()
        self.heal_q   = self.ik.heal_plate_q.copy()
        
        # Apply initial control targets
        for i, act_id in enumerate(self.franka_act):
            self.data.ctrl[act_id] = self.franka_q[i]
        for i, act_id in enumerate(self.heal_act):
            self.data.ctrl[act_id] = self.heal_q[i]
        self.data.ctrl[self.franka_gripper_act] = self.FRANKA_GRIP_CLOSE
        self.data.ctrl[self.heal_gripper_act]   = self.HEAL_GRIP_CLOSE

        mujoco.mj_forward(self.model, self.data)

        self._last_ik_t   = -999.0
        self._initialized = True

        # Reset PID state
        self.ball_local_filt = None
        self.ball_vel_filt   = np.zeros(2)
        self.last_ball_local = None
        self.last_time       = 0.0
        self.integral_x      = 0.0
        self.integral_y      = 0.0
        self.phi_cmd         = 0.0
        self.theta_cmd       = 0.0

        print(f"[reset] Keyframe 0 loaded successfully.")
        print(f"[reset] Plate  : {self.data.xpos[self.plate_id].round(4)}")
        print(f"[reset] Ball   : {self.data.xpos[self.ball_id].round(4)}")


# ─────────────────────────────────────────────────────────────────
# Main Execution
# ─────────────────────────────────────────────────────────────────

def main():
    # Optional target point (plate-local metres from centre): python ball_balance_controller.py 0.1 -0.05
    target = (float(sys.argv[1]), float(sys.argv[2])) if len(sys.argv) >= 3 else (0.0, 0.0)

    print("Loading model scene...")
    model = mujoco.MjModel.from_xml_path('scene_franka_heal.xml')
    data  = mujoco.MjData(model)

    controller = BallBalancer(model, data, target_point=target)
    controller.reset()
    tx, ty = controller.target_point
    print(f"[target] Ball will converge to plate-local point ({tx:.3f}, {ty:.3f})")

    print("Launching passive viewer...")
    with mujoco.viewer.launch_passive(model, data) as viewer:
        # Camera: front-on view of the plate (facing along +X, arms symmetric
        # left/right), tilted down at a steep angle to look down onto the ball.
        viewer.cam.lookat    = np.array([0.20, -0.40, 0.55])  # plate centre
        viewer.cam.distance  = 1.4
        viewer.cam.azimuth   = 0
        viewer.cam.elevation = -45

        _maximize_window('MuJoCo')

        # Physics steps at 1/timestep Hz (500Hz for a 0.002s step), but the display
        # can't (and needn't) redraw that fast. Calling viewer.sync() every physics
        # step lets vsync throttle the WHOLE loop down to the display refresh rate
        # (e.g. 60Hz), which starves the physics of steps and makes the sim crawl in
        # slow motion. Instead, step physics continuously and only sync the viewer
        # at a fixed ~60Hz cadence.
        RENDER_HZ = 60
        steps_per_render = max(1, round(1.0 / RENDER_HZ / model.opt.timestep))

        step_i = 0
        while viewer.is_running():
            t0 = time.time()

            # Stepping the simulation automatically triggers the gravcomp and controller callback
            mujoco.mj_step(model, data)
            step_i += 1
            if step_i % steps_per_render == 0:
                viewer.sync()

            # Real-time pacing
            elapsed = time.time() - t0
            sleep_t = model.opt.timestep - elapsed
            if sleep_t > 0:
                time.sleep(sleep_t)

    print("Done.")

if __name__ == '__main__':
    main()
