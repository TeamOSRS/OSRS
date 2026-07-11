import mujoco
import numpy as np
import os
import sys

# Path to the custom robot scene XML
XML_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "steering_plate_scene.xml")

# Load model & data
model = mujoco.MjModel.from_xml_path(XML_PATH)
kin_data = mujoco.MjData(model)

LEFT_ARM_JOINTS = ['l_sho_pitch', 'l_sho_roll', 'l_sho_yaw', 'l_el_pitch', 'l_forearm_yaw', 'l_wrist_pitch', 'l_wrist_yaw']
RIGHT_ARM_JOINTS = ['r_sho_pitch', 'r_sho_roll', 'r_sho_yaw', 'r_el_pitch', 'r_forearm_yaw', 'r_wrist_pitch', 'r_wrist_yaw']
MOTOR_JOINTS = LEFT_ARM_JOINTS + RIGHT_ARM_JOINTS

LEFT_ACTIVE_JOINTS = ['l_sho_yaw', 'l_el_pitch', 'l_forearm_yaw', 'l_wrist_pitch']
RIGHT_ACTIVE_JOINTS = ['r_sho_yaw', 'r_el_pitch', 'r_forearm_yaw', 'r_wrist_pitch']

# Centered natural seeds
q_seed = {
    'l_sho_yaw': -0.35,
    'l_el_pitch': -1.4,
    'l_forearm_yaw': 0.0,
    'l_wrist_pitch': 0.0,
    'r_sho_yaw': -0.35,
    'r_el_pitch': 1.4,
    'r_forearm_yaw': 0.0,
    'r_wrist_pitch': 0.0
}

# Define targets
x_plate_nominal = 0.22
y_plate_nominal = 0.0
z_plate_nominal = 0.90
pos_left_local = np.array([0.0, 0.19, 0.03])
pos_right_local = np.array([0.0, -0.19, 0.03])

pos_plate_des = np.array([x_plate_nominal, y_plate_nominal, z_plate_nominal])
pos_left_target = pos_plate_des + pos_left_local
pos_right_target = pos_plate_des + pos_right_local

# Target orientations
R_left_home_target = np.array([
    [0.0, -1.0, 0.0],
    [0.0, 0.0, 1.0],
    [-1.0, 0.0, 0.0]
])

R_right_home_target = np.array([
    [0.0, -1.0, 0.0],
    [0.0, 0.0, -1.0],
    [1.0, 0.0, 0.0]
])

q_left_target = np.zeros(4)
mujoco.mju_mat2Quat(q_left_target, R_left_home_target.flatten())
q_right_target = np.zeros(4)
mujoco.mju_mat2Quat(q_right_target, R_right_home_target.flatten())

def quat_mul(q1, q2):
    w1, x1, y1, z1 = q1
    w2, x2, y2, z2 = q2
    return np.array([
        w1*w2 - x1*x2 - y1*y2 - z1*z2,
        w1*x2 + x1*w2 + y1*z2 - z1*y2,
        w1*y2 - x1*z2 + y1*w2 + z1*x2,
        w1*z2 + x1*y2 - y1*x2 + z1*w2
    ])

def quat_inv(q):
    return np.array([q[0], -q[1], -q[2], -q[3]])

# 6D IK solver
def solve_arm_ik(site_name, target_pos, target_quat, arm_joints, active_joints, q_t, damping=0.03, step_scale=0.2, k_posture=0.001):
    site_id = model.site(site_name).id
    for name in arm_joints:
        qpos_adr = model.joint(name).qposadr[0]
        kin_data.qpos[qpos_adr] = q_t[name]
    mujoco.mj_fwdPosition(model, kin_data)
    
    current_pos = kin_data.site_xpos[site_id].copy()
    current_rot_mat = kin_data.site_xmat[site_id].copy().reshape(3, 3)
    current_quat = np.zeros(4)
    mujoco.mju_mat2Quat(current_quat, current_rot_mat.flatten())
    
    pos_err = target_pos - current_pos
    q_err = quat_mul(target_quat, quat_inv(current_quat))
    rot_err = 2.0 * q_err[1:4] * np.sign(q_err[0])
    
    rot_err *= 0.10
    dx = np.concatenate([pos_err, rot_err])
    
    jacp = np.zeros((3, model.nv))
    jacr = np.zeros((3, model.nv))
    mujoco.mj_jacSite(model, kin_data, jacp, jacr, site_id)
    J = np.vstack([jacp, jacr])
    
    dof_indices = [model.joint(name).dofadr[0] for name in active_joints]
    J_arm = J[:, dof_indices]
    
    A = J_arm @ J_arm.T + (damping ** 2) * np.eye(6)
    try:
        dq = J_arm.T @ np.linalg.solve(A, dx)
    except np.linalg.LinAlgError:
        dq = J_arm.T @ dx * 0.1
        
    for i, name in enumerate(active_joints):
        pull = (q_seed[name] - q_t[name]) * k_posture
        q_t[name] += dq[i] * step_scale + pull
        joint_range = model.joint(name).range
        q_t[name] = np.clip(q_t[name], joint_range[0], joint_range[1])

# Test 1: l_wrist_yaw = -1.5708
q_t_1 = {name: 0.0 for name in MOTOR_JOINTS}
q_t_1['l_wrist_yaw'] = -1.5708
q_t_1['r_wrist_yaw'] = -1.5708
for name in MOTOR_JOINTS:
    if name in q_seed:
        q_t_1[name] = q_seed[name]

# Test 2: l_wrist_yaw = 1.5708
q_t_2 = {name: 0.0 for name in MOTOR_JOINTS}
q_t_2['l_wrist_yaw'] = 1.5708
q_t_2['r_wrist_yaw'] = -1.5708
for name in MOTOR_JOINTS:
    if name in q_seed:
        q_t_2[name] = q_seed[name]

for _ in range(150):
    solve_arm_ik('l_eef', pos_left_target, q_left_target, LEFT_ARM_JOINTS, LEFT_ACTIVE_JOINTS, q_t_1)
    solve_arm_ik('l_eef', pos_left_target, q_left_target, LEFT_ARM_JOINTS, LEFT_ACTIVE_JOINTS, q_t_2)

# Print tracking errors for Left arm in both cases
l_site_id = model.site('l_eef').id

# Case 1
for name in MOTOR_JOINTS:
    qpos_adr = model.joint(name).qposadr[0]
    kin_data.qpos[qpos_adr] = q_t_1[name]
mujoco.mj_fwdPosition(model, kin_data)
pos_1 = kin_data.site_xpos[l_site_id].copy()

# Case 2
for name in MOTOR_JOINTS:
    qpos_adr = model.joint(name).qposadr[0]
    kin_data.qpos[qpos_adr] = q_t_2[name]
mujoco.mj_fwdPosition(model, kin_data)
pos_2 = kin_data.site_xpos[l_site_id].copy()

print("="*80)
print("LEFT EEF TRACKING ERRORS:")
print("="*80)
print(f"Case 1 (l_wrist_yaw = -1.5708): Error = {np.linalg.norm(pos_left_target - pos_1)*1000:.2f} mm")
print(f"  Joints: l_sho_yaw={q_t_1['l_sho_yaw']:.3f}, l_el_pitch={q_t_1['l_el_pitch']:.3f}, l_forearm_yaw={q_t_1['l_forearm_yaw']:.3f}, l_wrist_pitch={q_t_1['l_wrist_pitch']:.3f}")
print("-" * 50)
print(f"Case 2 (l_wrist_yaw =  1.5708): Error = {np.linalg.norm(pos_left_target - pos_2)*1000:.2f} mm")
print(f"  Joints: l_sho_yaw={q_t_2['l_sho_yaw']:.3f}, l_el_pitch={q_t_2['l_el_pitch']:.3f}, l_forearm_yaw={q_t_2['l_forearm_yaw']:.3f}, l_wrist_pitch={q_t_2['l_wrist_pitch']:.3f}")
print("="*80)
