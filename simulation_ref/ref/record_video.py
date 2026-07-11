import mujoco
import numpy as np
import cv2
from scipy.spatial.transform import Rotation as R

# Load model and data
model = mujoco.MjModel.from_xml_path("dual_scene.xml")
data = mujoco.MjData(model)

# Reset to home keyframe
mujoco.mj_resetDataKeyframe(model, data, 0)

# Move the ball slightly to the side to trigger control action
ball_joint_id = model.joint('ball_joint').id
ball_qposadr = model.jnt_qposadr[ball_joint_id]
data.qpos[ball_qposadr] = 0.05  # x_ball initial displacement

# Setup renderer
renderer = mujoco.Renderer(model, height=480, width=640)

# Video writer
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
video_path = "simulation.mp4"
out = cv2.VideoWriter(video_path, fourcc, 30.0, (640, 480))

# Arm joint names definition: Joint 1 (yaw) and Joint 2 (shoulder pitch) are kept locked
# at their home keyframe values. Only Joint 3 (elbow pitch) and Joint 4 (wrist pitch)
# are actively updated to tilt the plate.
left_joint_names = ["left_Joint3", "left_Joint4"]
right_joint_names = ["right_Joint3", "right_Joint4"]

def get_joint_limits(model, names):
    ranges = []
    for name in names:
        j_id = model.joint(name).id
        ranges.append(model.jnt_range[j_id])
    return ranges

left_limits = get_joint_limits(model, left_joint_names)
right_limits = get_joint_limits(model, right_joint_names)

def get_indices(names):
    dofs = [model.joint(n).dofadr[0] for n in names]
    qpos = [model.joint(n).qposadr[0] for n in names]
    return dofs, qpos

left_dof_idx, left_qpos_idx = get_indices(left_joint_names)
right_dof_idx, right_qpos_idx = get_indices(right_joint_names)

left_site_id = model.site("left_grasp_frame").id
right_site_id = model.site("right_grasp_frame").id

left_qpos_curr = np.array([data.qpos[idx] for idx in left_qpos_idx])
right_qpos_curr = np.array([data.qpos[idx] for idx in right_qpos_idx])

from simulate_cooperative import BallBalancingPID, solve_ik_for_step
pid = BallBalancingPID(kp=0.41, kd=0.22, ki=0.0, max_delta_z=0.033)

z_plate_nominal = 0.20
pos_left_local = np.array([-0.2758, 0, 0.0])
pos_right_local = np.array([0.2758, 0, 0.0])

R_left_local = np.eye(3)
R_right_local = np.diag([-1.0, -1.0, 1.0])

dt = model.opt.timestep
sim_time = 0.0

# Initialize filtered joint positions for exponential smoothing
left_qpos_filt = left_qpos_curr.copy()
right_qpos_filt = right_qpos_curr.copy()

# Render 3 seconds of simulation (1500 steps, recording every 10 steps -> 150 frames at 30 fps = 5 seconds)
max_steps = 1500
record_interval = 10

# Set a camera view (front view: looking at the X-Z plane)
# In MuJoCo, the default camera is fine, but we can set the camera lookat and distance.
# Let's check available cameras or use default.
camera = mujoco.MjvCamera()
camera.type = mujoco.mjtCamera.mjCAMERA_FREE
camera.lookat = np.array([0, 0, 0.2])
camera.distance = 1.0
camera.elevation = -10
camera.azimuth = 90  # 90 degrees faces the X-Z plane from the front (along +Y)

for step in range(max_steps):
    pos_plate = data.body('plate_assembly').xpos
    R_plate = data.body('plate_assembly').xmat.reshape(3, 3)
    pos_ball = data.body('ball').xpos
    
    pos_ball_local = R_plate.T @ (pos_ball - pos_plate)
    x_ball_local = pos_ball_local[0]
    
    ball_dofadr = model.jnt_dofadr[ball_joint_id]
    vel_ball_world = data.qvel[ball_dofadr:ball_dofadr+3]
    
    plate_joint_id = model.joint('plate_joint').id
    plate_dofadr = model.jnt_dofadr[plate_joint_id]
    vel_plate_world = data.qvel[plate_dofadr:plate_dofadr+3]
    
    vel_rel_world = vel_ball_world - vel_plate_world
    vel_ball_local = R_plate.T @ vel_rel_world
    dx_ball_local = vel_ball_local[0]
    
    error = 0.0 - x_ball_local
    delta_z = pid.update(error, dx_ball_local, dt)
    
    theta = np.arctan2(2.0 * delta_z, 0.5516)
    R_plate_des = R.from_euler('y', theta).as_matrix()
    
    pos_plate_des = np.array([0.0, 0.0, z_plate_nominal])
    pos_left_target = pos_plate_des + R_plate_des @ pos_left_local
    R_left_target = R_plate_des @ R_left_local
    
    pos_right_target = pos_plate_des + R_plate_des @ pos_right_local
    R_right_target = R_plate_des @ R_right_local
    
    for _ in range(5):
        left_qpos_curr, left_err = solve_ik_for_step(
            model, data, left_site_id, left_dof_idx, left_qpos_idx, left_limits,
            pos_left_target, R_left_target, left_qpos_curr
        )
        right_qpos_curr, right_err = solve_ik_for_step(
            model, data, right_site_id, right_dof_idx, right_qpos_idx, right_limits,
            pos_right_target, R_right_target, right_qpos_curr
        )
        
    # Exponential joint command filter to smooth out high frequency mechanical vibrations
    alpha = 0.25
    left_qpos_filt = alpha * left_qpos_curr + (1.0 - alpha) * left_qpos_filt
    right_qpos_filt = alpha * right_qpos_curr + (1.0 - alpha) * right_qpos_filt
    
    data.ctrl[0] = 0.0
    data.ctrl[1] = -0.5938813
    data.ctrl[2] = left_qpos_filt[0]
    data.ctrl[3] = left_qpos_filt[1]
    data.ctrl[4] = 0.015 # gripper
    
    data.ctrl[5] = 0.0
    data.ctrl[6] = -0.5938813
    data.ctrl[7] = right_qpos_filt[0]
    data.ctrl[8] = right_qpos_filt[1]
    data.ctrl[9] = 0.015 # gripper
    
    mujoco.mj_step(model, data)
    sim_time += dt
    
    if step % record_interval == 0:
        renderer.update_scene(data, camera=camera)
        pixels = renderer.render()
        # Convert RGB to BGR for OpenCV
        bgr_pixels = cv2.cvtColor(pixels, cv2.COLOR_RGB2BGR)
        out.write(bgr_pixels)

out.release()
print(f"Video saved to {video_path}")
