"""
Headless (no-viewer) experiment harness for the MuJoCo Franka+HEAL
cooperative ball-balancer digital twin (ball_balance_controller.py).

Runs the actual, unmodified BallBalancer/IKSolver classes from the sim
against the real MuJoCo rigid-body physics (implicit-fast integrator,
500 Hz / dt=0.002s), for a battery of step-response and repeated
randomized-offset trials, and logs plate-local ball position at every
control step.

Outputs (this directory):
  data/*.csv                 -- per-timestep plate-local ball trajectory logs
  results_summary.json       -- settling time / overshoot / SSE per trial + aggregate stats
  fig_step_response.png      -- single-axis and off-diagonal step responses
  fig_tilt_commands.png      -- commanded phi/theta tilt over one trial
"""
import os
import sys
import csv
import json
import random

import numpy as np
import mujoco
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SIM_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, SIM_DIR)
os.chdir(SIM_DIR)  # scene_franka_heal.xml and mesh dirs are referenced relative to this folder

random.seed(7)
np.random.seed(7)

from ball_balance_controller import BallBalancer  # noqa: E402

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(OUT_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

CONTROL_LOG_HZ = 100  # log every Nth physics step so files stay a reasonable size


def run_trial(name, target_point, initial_offset, duration_s):
    # BallBalancer registers its control law via the GLOBAL
    # mujoco.set_mjcb_control() callback (not scoped to one model/data pair).
    # A stale callback from the previous trial's now-defunct MjData causes
    # `from_xml_path` on the next trial to raise "engine error: Python
    # exception raised", so it must be cleared before loading a fresh model.
    mujoco.set_mjcb_control(None)
    model = mujoco.MjModel.from_xml_path("scene_franka_heal.xml")
    data = mujoco.MjData(model)

    controller = BallBalancer(model, data, target_point=target_point)
    controller.reset(randomize_ball=False)

    # Deterministically place the ball at a known plate-local offset from the
    # (flat, un-tilted) plate at reset time, instead of the class's own
    # random spawn -- required for reproducible step-response trials.
    plate_xy = data.qpos[controller.plate_qpos_adr:controller.plate_qpos_adr + 2].copy()
    data.qpos[controller.ball_qpos_adr:controller.ball_qpos_adr + 2] = plate_xy + np.array(initial_offset)
    mujoco.mj_forward(model, data)

    dt = model.opt.timestep
    n_steps = int(duration_s / dt)
    log_every = max(1, int(round(1.0 / CONTROL_LOG_HZ / dt)))

    rows = []
    for step in range(n_steps):
        mujoco.mj_step(model, data)
        if step % log_every == 0:
            plate_pos = data.xpos[controller.plate_id]
            plate_mat = data.xmat[controller.plate_id].reshape(3, 3)
            ball_pos = data.xpos[controller.ball_id]
            ball_local = plate_mat.T @ (ball_pos - plate_pos)
            rows.append({
                "t": step * dt,
                "x": ball_local[0], "y": ball_local[1],
                "target_x": controller.target_point[0], "target_y": controller.target_point[1],
                "phi_cmd": controller.phi_cmd, "theta_cmd": controller.theta_cmd,
            })

    csv_path = os.path.join(DATA_DIR, f"{name}.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)

    return rows


def settling_metrics(rows, axis, band=0.01, settle_hold_s=1.0, log_dt=1.0 / CONTROL_LOG_HZ):
    hold_steps = max(1, int(settle_hold_s / log_dt))
    tgt_key = f"target_{axis}"
    errs = [abs(r[axis] - r[tgt_key]) for r in rows]
    e0 = errs[0]

    settle_t = None
    run = 0
    for i, e in enumerate(errs):
        if e <= band:
            run += 1
            if run >= hold_steps:
                settle_t = rows[i - hold_steps + 1]["t"]
                break
        else:
            run = 0

    signed = [r[axis] - r[tgt_key] for r in rows]
    sign0 = 1.0 if signed[0] >= 0 else -1.0
    overshoot_vals = [-sign0 * s for s in signed if -sign0 * s > 0]
    overshoot = max(overshoot_vals) if overshoot_vals else 0.0
    overshoot_pct = 100.0 * overshoot / e0 if e0 > 1e-6 else 0.0

    tail_n = max(1, int(2.0 / log_dt))
    sse = float(np.mean(errs[-tail_n:]))

    return {
        "settling_time_s": settle_t,
        "overshoot_pct": overshoot_pct,
        "steady_state_error_m": sse,
        "initial_error_m": e0,
    }


def main():
    results = {}

    # ---- Single-axis step response: ball starts 0.12 m off-centre along local X, target = centre ----
    trial_x = run_trial("step_x_axis", target_point=(0.0, 0.0), initial_offset=(0.12, 0.0), duration_s=9.0)
    results["step_x_axis"] = settling_metrics(trial_x, "x")

    # ---- Off-diagonal step response: offset on both axes simultaneously ----
    trial_diag = run_trial("step_diagonal", target_point=(0.0, 0.0), initial_offset=(0.10, -0.10), duration_s=9.0)
    results["step_diagonal_x"] = settling_metrics(trial_diag, "x")
    results["step_diagonal_y"] = settling_metrics(trial_diag, "y")

    # ---- Off-centre target (not plate centre) ----
    trial_offctr = run_trial("step_offcenter_target", target_point=(0.08, -0.05), initial_offset=(-0.05, 0.06), duration_s=9.0)
    results["step_offcenter_target_x"] = settling_metrics(trial_offctr, "x")
    results["step_offcenter_target_y"] = settling_metrics(trial_offctr, "y")

    # ---- Repeated randomized-offset trials for aggregate statistics (N=12; MuJoCo trials are expensive) ----
    n_trials = 12
    metrics_x, metrics_y = [], []
    for i in range(n_trials):
        ox = random.uniform(0.08, 0.12) * random.choice([-1, 1])
        oy = random.uniform(0.08, 0.12) * random.choice([-1, 1])
        trial = run_trial(f"repeat_{i:02d}", target_point=(0.0, 0.0), initial_offset=(ox, oy), duration_s=9.0)
        metrics_x.append(settling_metrics(trial, "x"))
        metrics_y.append(settling_metrics(trial, "y"))

    def agg(metrics_list, key):
        vals = [m[key] for m in metrics_list if m[key] is not None]
        return {"mean": float(np.mean(vals)) if vals else None,
                "std": float(np.std(vals)) if vals else None,
                "n_settled": len(vals), "n_total": len(metrics_list)}

    results["repeated_trials_n"] = n_trials
    results["repeated_aggregate_x"] = {
        "settling_time_s": agg(metrics_x, "settling_time_s"),
        "overshoot_pct": agg(metrics_x, "overshoot_pct"),
        "steady_state_error_m": agg(metrics_x, "steady_state_error_m"),
    }
    results["repeated_aggregate_y"] = {
        "settling_time_s": agg(metrics_y, "settling_time_s"),
        "overshoot_pct": agg(metrics_y, "overshoot_pct"),
        "steady_state_error_m": agg(metrics_y, "steady_state_error_m"),
    }

    with open(os.path.join(OUT_DIR, "results_summary.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    # ------------------------------- Figures -------------------------------
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.4))
    axes[0].plot([r["t"] for r in trial_x], [r["x"] for r in trial_x], label="Ball x (plate-local)", color="#1f77b4")
    axes[0].axhline(0.0, color="gray", linestyle="--", linewidth=0.8, label="Target")
    axes[0].fill_between([r["t"] for r in trial_x], -0.01, 0.01, color="gray", alpha=0.15)
    axes[0].set_xlabel("Time (s)")
    axes[0].set_ylabel("x (m)")
    axes[0].set_title("(a) Single-axis step, x0 = 0.12 m")
    axes[0].legend(fontsize=7)

    axes[1].plot([r["t"] for r in trial_diag], [r["x"] for r in trial_diag], label="x", color="#1f77b4")
    axes[1].plot([r["t"] for r in trial_diag], [r["y"] for r in trial_diag], label="y", color="#d62728")
    axes[1].axhline(0.0, color="gray", linestyle="--", linewidth=0.8)
    axes[1].set_xlabel("Time (s)")
    axes[1].set_ylabel("Position (m)")
    axes[1].set_title("(b) Off-diagonal step, (x0,y0) = (0.10,-0.10) m")
    axes[1].legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "fig_step_response.png"), dpi=200)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.4, 2.8))
    ax.plot([r["t"] for r in trial_x], [r["phi_cmd"] for r in trial_x], label="phi_cmd (pitch)", color="#1f77b4")
    ax.plot([r["t"] for r in trial_x], [r["theta_cmd"] for r in trial_x], label="theta_cmd (roll)", color="#d62728")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Commanded tilt (rad)")
    ax.set_title("Smoothed plate-tilt commands, single-axis step trial")
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "fig_tilt_commands.png"), dpi=200)
    plt.close(fig)

    # ---- Off-centre-target trial (target away from plate centre, not just the origin) ----
    fig, ax = plt.subplots(figsize=(6.4, 2.8))
    ax.plot([r["t"] for r in trial_offctr], [r["x"] for r in trial_offctr], label="x", color="#1f77b4")
    ax.plot([r["t"] for r in trial_offctr], [r["y"] for r in trial_offctr], label="y", color="#d62728")
    ax.axhline(trial_offctr[0]["target_x"], color="#1f77b4", linestyle="--", linewidth=0.8, label="target x")
    ax.axhline(trial_offctr[0]["target_y"], color="#d62728", linestyle="--", linewidth=0.8, label="target y")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Position (m)")
    ax.set_title("Off-centre target, (target_x,target_y) = (0.08,-0.05) m")
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "fig_offcenter_target.png"), dpi=200)
    plt.close(fig)

    # ---- Distribution of settling time / overshoot / SSE across the N=12 repeated trials, by axis ----
    def vals_only(metrics_list, key):
        return [m[key] for m in metrics_list if m[key] is not None]

    fig, axes = plt.subplots(1, 3, figsize=(10, 3.2))
    metric_specs = [
        ("settling_time_s", "Settling time (s)"),
        ("overshoot_pct", "Overshoot (%)"),
        ("steady_state_error_m", "Steady-state error (m)"),
    ]
    for ax, (key, ylabel) in zip(axes, metric_specs):
        x_vals = vals_only(metrics_x, key)
        y_vals = vals_only(metrics_y, key)
        ax.boxplot([x_vals, y_vals], labels=["Roll / x", "Pitch / y"], widths=0.5, showmeans=True)
        xs_x = np.random.RandomState(0).normal(1, 0.04, size=len(x_vals))
        xs_y = np.random.RandomState(1).normal(2, 0.04, size=len(y_vals))
        ax.scatter(xs_x, x_vals, s=10, alpha=0.6, color="#1f77b4", zorder=3)
        ax.scatter(xs_y, y_vals, s=10, alpha=0.6, color="#d62728", zorder=3)
        ax.set_ylabel(ylabel, fontsize=8)
        ax.tick_params(labelsize=8)
    fig.suptitle("Per-trial spread across N=12 randomized initial offsets, by tilt axis", fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "fig_repeated_trial_distributions.png"), dpi=200)
    plt.close(fig)

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
