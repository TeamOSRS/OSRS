import mujoco
import mujoco.viewer
import numpy as np
import cv2

# =========================================
# Load Model
# =========================================

model = mujoco.MjModel.from_xml_path("2d_pov.xml")
data = mujoco.MjData(model)

# =========================================
# PID Window
# =========================================

cv2.namedWindow("PID Controls")

# =========================================
# Stable Defaults
# =========================================

# Kp = 1.5
cv2.createTrackbar(
    "Kp x100",
    "PID Controls",
    150,
    500,
    lambda x: None
)

# Ki = 0
cv2.createTrackbar(
    "Ki x1000",
    "PID Controls",
    0,
    500,
    lambda x: None
)

# Kd = 0.8
cv2.createTrackbar(
    "Kd x100",
    "PID Controls",
    80,
    500,
    lambda x: None
)

# Target:
# 0 -> -0.20m
# 200 -> +0.20m

cv2.createTrackbar(
    "Target",
    "PID Controls",
    100,
    200,
    lambda x: None
)

# =========================================
# PID Variables
# =========================================

integral = 0.0

dt = model.opt.timestep

frame_counter = 0

# =========================================
# Launch Viewer
# =========================================

with mujoco.viewer.launch_passive(model, data) as viewer:

    # Lock side camera
    viewer.cam.fixedcamid = 0
    viewer.cam.type = mujoco.mjtCamera.mjCAMERA_FIXED

    while viewer.is_running():

        # =====================================
        # Read Slider Values
        # =====================================

        Kp = (
            cv2.getTrackbarPos(
                "Kp x100",
                "PID Controls"
            ) / 100.0
        )

        Ki = (
            cv2.getTrackbarPos(
                "Ki x1000",
                "PID Controls"
            ) / 1000.0
        )

        Kd = (
            cv2.getTrackbarPos(
                "Kd x100",
                "PID Controls"
            ) / 100.0
        )

        target_position = (
            cv2.getTrackbarPos(
                "Target",
                "PID Controls"
            ) - 100
        ) / 100.0

        # =====================================
        # Ball Position
        # =====================================

        # framepos sensor:
        # X Y Z

        ball_x = data.sensordata[0]

        # =====================================
        # Ball Velocity
        # =====================================

        # framelinvel sensor:
        # X Y Z

        ball_velocity = data.sensordata[3]

        # =====================================
        # Position Error
        # =====================================

        error = target_position - ball_x

        # =====================================
        # Integral
        # =====================================

        integral += error * dt

        # Anti-windup
        integral = np.clip(
            integral,
            -0.5,
            0.5
        )

        # =====================================
        # REAL VELOCITY DAMPING CONTROLLER
        # =====================================

        output = (
            Kp * error
            + Ki * integral
            - Kd * ball_velocity
        )

        # =====================================
        # Clamp Plate Angle
        # =====================================

        output = np.clip(
            output,
            -0.10,
            0.10
        )

        # =====================================
        # Apply Control
        # =====================================

        data.ctrl[0] = output

        # =====================================
        # Physics Step
        # =====================================

        mujoco.mj_step(
            model,
            data,
            nstep=3
        )

        viewer.sync()

        # =====================================
        # Update UI Occasionally
        # =====================================

        frame_counter += 1

        if frame_counter % 8 == 0:

            img = np.zeros(
                (180, 560, 3),
                dtype=np.uint8
            )

            cv2.putText(
                img,
                f"Kp={Kp:.2f}  Ki={Ki:.3f}  Kd={Kd:.2f}",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255,255,255),
                2
            )

            cv2.putText(
                img,
                f"Target={target_position:.2f} m",
                (20, 80),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255,255,255),
                2
            )

            cv2.putText(
                img,
                f"Ball X={ball_x:.3f} m",
                (20, 120),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255,255,255),
                2
            )

            cv2.putText(
                img,
                f"Ball Velocity={ball_velocity:.3f} m/s",
                (20, 160),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255,255,255),
                2
            )

            cv2.imshow(
                "PID Controls",
                img
            )

            cv2.waitKey(1)

cv2.destroyAllWindows()