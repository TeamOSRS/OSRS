import numpy as np

def rot_y(theta):
    c, s = np.cos(theta), np.sin(theta)
    return np.array([[c, 0.0, s, 0.0], [0.0, 1.0, 0.0, 0.0], [-s, 0.0, c, 0.0], [0.0, 0.0, 0.0, 1.0]])

def rot_z(theta):
    c, s = np.cos(theta), np.sin(theta)
    return np.array([[c, -s, 0.0, 0.0], [s, c, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])

def trans(x, y, z):
    return np.array([[1.0, 0.0, 0.0, x], [0.0, 1.0, 0.0, y], [0.0, 0.0, 1.0, z], [0.0, 0.0, 0.0, 1.0]])

def fk_left(q_active):
    # q_active = [Joint3, Joint4]
    q = [0.0, -0.5938813, q_active[0], q_active[1]]
    T = trans(-0.46, 0.0, 0.0) @ trans(0.012, 0.0, 0.017) @ rot_z(q[0])
    T = T @ trans(0.0, 0.0, 0.0595) @ rot_y(q[1])
    T = T @ trans(0.024, 0.0, 0.128) @ rot_y(q[2])
    T = T @ trans(0.124, 0.0, 0.0) @ rot_y(q[3])
    T = T @ trans(0.10, 0.0, 0.0)
    return T

def fk_right(q_active):
    q = [0.0, -0.5938813, q_active[0], q_active[1]]
    T = trans(0.46, 0.0, 0.0) @ rot_z(np.pi) @ trans(0.012, 0.0, 0.017) @ rot_z(q[0])
    T = T @ trans(0.0, 0.0, 0.0595) @ rot_y(q[1])
    T = T @ trans(0.024, 0.0, 0.128) @ rot_y(q[2])
    T = T @ trans(0.124, 0.0, 0.0) @ rot_y(q[3])
    T = T @ trans(0.10, 0.0, 0.0)
    return T

# cmd: [left_Joint3, left_Joint4, right_Joint3, right_Joint4] = [0.897, -0.412, 0.223, 0.48]
q_left = np.array([0.897, -0.412])
q_right = np.array([0.223, 0.48])

T_l = fk_left(q_left)
T_r = fk_right(q_right)

print("Left End Effector target Z:", T_l[2, 3])
print("Right End Effector target Z:", T_r[2, 3])
