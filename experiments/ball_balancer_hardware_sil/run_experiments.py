"""
Software-in-the-loop (SIL) experiment harness for the OSRS hardware Ball
Balancer control law (src/modules/research/ball_balancer.py).

No physical Dynamixel servos or load cells are available, so this harness
exercises the *actual, unmodified* production controller class
(BallBalancer.update_controller) in closed loop against a synthetic
ball-and-plate plant grounded in the paper's own equations of motion
(Eq. 10-12): s_ddot = A*u + B*s_dot, where u is the controller's own
"last_applied_tilt / 100" normalized tilt command -- i.e. the exact same
normalization the controller's online system-identification (Eq. 19-20)
already assumes. Vision feedback is injected via the real
VisionBallTracker.set_measured_position() API, and load-cell feedback uses
the controller's own built-in update_mock_weights() fallback path (the
same code path used automatically whenever no serial hardware is
connected), so this is a faithful, unmodified test of the repository's
real control code, not a re-implementation.

Ground-truth plant parameters (A_true, B_true) are chosen independently of
the controller's initial parameter guesses (est_a=0.5, est_b=-0.1) so that
identification convergence is a genuine test, not a foregone conclusion.

Outputs (this directory):
  data/*.csv                  -- per-timestep logs for every trial
  results_summary.json        -- settling time / overshoot / SSE per trial
  fig_step_response.png       -- multi-target step response (manual vs auto-tune)
  fig_identification.png      -- est_a / est_b convergence, excitation ON vs OFF
  fig_scenario_timeline.png   -- active control scenario over one representative trial
"""
import os
import sys
import csv
import json
import random
import math

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, REPO_ROOT)

random.seed(42)
np.random.seed(42)

from src.modules.research.ball_balancer import BallBalancer  # noqa: E402

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(OUT_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

DT = 0.02          # 50 Hz control loop, matching the paper's stated cycle rate
Y_LIMIT = 0.22      # physical plate half-extent (m), matches ball_balancer.py clamp

A_TRUE = 1.15       # ground-truth control authority (unitless, tilt/100 -> m/s^2)
B_TRUE = -0.42      # ground-truth rolling-resistance / damping coefficient
PROCESS_NOISE_STD = 0.0025   # small stochastic disturbance on acceleration


class NullEventBus:
    """Minimal stand-in for OSRS's real event bus (only .publish is used)."""
    def publish(self, topic, data):
        pass


def make_balancer(auto_tune: bool, exploration: bool) -> BallBalancer:
    bb = BallBalancer(NullEventBus())
    # Never let a SIL trial overwrite the real, persisted
    # balancer_learning_data.json at the repo root (BallBalancer saves it
    # every 5 wall-clock seconds while active; a slow machine or a longer
    # trial could otherwise clobber real calibration data from disk).
    bb._save_learning_data = lambda: None
    bb.is_active = True
    bb.auto_tune_enabled = auto_tune
    bb.exploration_mode = exploration
    # Fresh, canonical state per trial -- BallBalancer.__init__ loads whatever
    # is on disk in balancer_learning_data.json (from any prior real run), so
    # every persisted field must be forced back to the class's own hardcoded
    # defaults here. In particular a stray invert_output=True on disk flips
    # the sign of the control correction and immediately drives the ball into
    # the rail, which is silent unless every field below is reset.
    bb.est_a = 0.5
    bb.est_b = -0.1
    bb.loadcell_c0, bb.loadcell_c1, bb.loadcell_c2, bb.loadcell_c3 = 0.0, 0.22, 0.0, 0.0
    bb.loadcell_mode = 2
    bb.loadcell_arm = "left"
    bb.ball_weight_ref = 100.0
    bb.invert_output = False
    bb.ball_type = "green_ping_pong"
    bb.kp, bb.kd, bb.ki = 1.3, 0.50, 0.10
    bb.learning_history = []
    return bb


def run_trial(name, auto_tune, exploration, target_sequence, duration_s, y0=0.15, rng_seed=None):
    """
    target_sequence: list of (time_s, target_y) requested externally, applied
    only when exploration is False -- see IMPORTANT NOTE below.

    IMPORTANT (empirical finding, not an assumption): update_controller()'s
    actual regulation error is `error = state["y"]` with no `- target_y`
    term anywhere in the predictive/PID correction path (ball_balancer.py,
    update_controller). `target_y` is only read back inside the
    exploration_mode branch to decide when the ball counts as "balanced" at
    the current excitation point and to log telemetry -- it never shifts the
    physical setpoint the PID actually regulates to (always y=0). This was
    confirmed by direct instrumentation (see run_target_disconnect_check())
    before being relied on here. Consequently the `target_sequence` argument
    below has no effect on plant behaviour outside of what the exploration
    state machine itself does with it; it is retained only so the step-index
    bookkeeping code stays inert/harmless for the target_y=0 trials that use it.
    """
    bb = make_balancer(auto_tune=auto_tune, exploration=exploration)
    rng = np.random.RandomState(rng_seed if rng_seed is not None else 0)

    y = y0
    v = 0.0
    t = 0.0
    n_steps = int(duration_s / DT)

    rows = []
    seq_idx = 0
    for step in range(n_steps):
        if not exploration:
            while seq_idx + 1 < len(target_sequence) and t >= target_sequence[seq_idx + 1][0]:
                seq_idx += 1
            bb.target_y = target_sequence[seq_idx][1]

        # Feed true ball position into the REAL vision provider API.
        bb.vision_provider.set_measured_position(0.0, y)

        target_tilt = bb.update_controller(DT)

        u = bb.last_applied_tilt / 100.0  # identical normalization the controller itself uses
        acc = A_TRUE * u + B_TRUE * v + rng.normal(0.0, PROCESS_NOISE_STD)
        v += acc * DT
        y += v * DT
        if y > Y_LIMIT:
            y, v = Y_LIMIT, min(0.0, v)
        elif y < -Y_LIMIT:
            y, v = -Y_LIMIT, max(0.0, v)

        rows.append({
            "t": t, "y": y, "v": v, "target_y": bb.target_y,
            "tilt": target_tilt, "u": u, "acc": acc,
            "est_a": bb.est_a, "est_b": bb.est_b,
            "kp": bb.kp, "kd": bb.kd,
            "scenario": bb.active_scenario,
        })
        t += DT

    csv_path = os.path.join(DATA_DIR, f"{name}.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)

    return rows


def run_target_disconnect_check():
    """
    Directly instruments the real BallBalancer to confirm/quantify that
    exploration_mode's setpoint cycling (Eq. 23) never produces a physical
    displacement, because target_y is not subtracted anywhere in the error
    used by the predictive/PID correction. Ball starts already at the first
    excitation point (y=0), so the exploration index should advance exactly
    once and then stall forever waiting for a physical displacement that the
    control law cannot produce.
    """
    bb = make_balancer(auto_tune=False, exploration=True)
    rng = np.random.RandomState(123)
    y, v = 0.0, 0.0
    n_steps = int(20.0 / DT)
    idx_changes = []
    last_idx = bb.exploration_target_idx
    rows = []
    for step in range(n_steps):
        bb.vision_provider.set_measured_position(0.0, y)
        bb.update_controller(DT)
        u = bb.last_applied_tilt / 100.0
        acc = A_TRUE * u + B_TRUE * v + rng.normal(0.0, PROCESS_NOISE_STD)
        v += acc * DT
        y += v * DT
        if bb.exploration_target_idx != last_idx:
            idx_changes.append((step * DT, bb.exploration_target_idx, bb.target_y))
            last_idx = bb.exploration_target_idx
        rows.append({"t": step * DT, "y": y, "target_y": bb.target_y})

    csv_path = os.path.join(DATA_DIR, "target_disconnect_check.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)

    return {
        "exploration_index_changes": idx_changes,
        "final_ball_y": y,
        "final_target_y": bb.target_y,
        "ball_ever_left_1cm_band": any(abs(r["y"]) > 0.01 for r in rows),
    }


def settling_metrics(rows, band=0.02, settle_hold_s=1.0):
    """Settling time (first time error stays within `band` for settle_hold_s
    continuously), percent overshoot relative to the initial error magnitude,
    and steady-state error (mean |error| over the final 2s of the trial)."""
    hold_steps = int(settle_hold_s / DT)
    errs = [abs(r["y"] - r["target_y"]) for r in rows]
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

    signed = [r["y"] - r["target_y"] for r in rows]
    # overshoot: largest excursion past the target on the opposite side of the initial error
    sign0 = 1.0 if (rows[0]["y"] - rows[0]["target_y"]) >= 0 else -1.0
    overshoot_vals = [-sign0 * s for s in signed if -sign0 * s > 0]
    overshoot = max(overshoot_vals) if overshoot_vals else 0.0
    overshoot_pct = 100.0 * overshoot / e0 if e0 > 1e-6 else 0.0

    tail_n = int(2.0 / DT)
    sse = float(np.mean(errs[-tail_n:]))

    return {
        "settling_time_s": settle_t,
        "overshoot_pct": overshoot_pct,
        "steady_state_error_m": sse,
        "initial_error_m": e0,
    }


def main():
    results = {}

    # ---- Experiment 1: manual (scenario-scaled) gains vs auto-tune (RLS/LMS critical damping) ----
    step_targets = [(0.0, 0.0)]
    trial_manual = run_trial("manual_gains_step", auto_tune=False, exploration=False,
                              target_sequence=step_targets, duration_s=8.0, y0=0.15, rng_seed=1)
    trial_auto = run_trial("auto_tune_step", auto_tune=True, exploration=False,
                            target_sequence=step_targets, duration_s=8.0, y0=0.15, rng_seed=1)
    results["manual_gains_step"] = settling_metrics(trial_manual)
    results["auto_tune_step"] = settling_metrics(trial_auto)

    # ---- Experiment 2: does exploration_mode's setpoint cycling (Eq. 23) actually
    # move the ball? Direct instrumentation -- see run_target_disconnect_check() docstring. ----
    disconnect_result = run_target_disconnect_check()
    results["target_y_disconnect_check"] = disconnect_result

    # ---- Experiment 3: online identification convergence, persistent excitation ON vs OFF ----
    # Both trials use an IDENTICAL rng_seed so any difference in est_a/est_b is
    # attributable only to exploration_mode itself, not to different noise draws.
    trial_no_excite = run_trial("identification_no_excitation", auto_tune=True, exploration=False,
                                 target_sequence=[(0.0, 0.0)], duration_s=15.0, y0=0.05, rng_seed=99)
    trial_excite = run_trial("identification_with_excitation", auto_tune=True, exploration=True,
                              target_sequence=[(0.0, 0.0)], duration_s=15.0, y0=0.05, rng_seed=99)

    for name, trial in [("identification_no_excitation", trial_no_excite),
                         ("identification_with_excitation", trial_excite)]:
        final_a, final_b = trial[-1]["est_a"], trial[-1]["est_b"]
        results[name] = {
            "final_est_a": final_a,
            "final_est_b": final_b,
            "abs_error_a": abs(final_a - A_TRUE),
            "abs_error_b": abs(final_b - B_TRUE),
        }
    results["identification_trials_identical_given_same_rng_seed"] = (
        trial_no_excite[-1]["est_a"] == trial_excite[-1]["est_a"] and
        trial_no_excite[-1]["est_b"] == trial_excite[-1]["est_b"]
    )

    # ---- Repeated-trial statistics (N=20 randomized initial offsets), manual vs auto-tune ----
    n_trials = 20
    manual_metrics, auto_metrics = [], []
    for i in range(n_trials):
        y0 = random.uniform(0.08, 0.20) * random.choice([-1, 1])
        m = run_trial(f"repeat_manual_{i:02d}", auto_tune=False, exploration=False,
                       target_sequence=[(0.0, 0.0)], duration_s=8.0, y0=y0, rng_seed=1000 + i)
        a = run_trial(f"repeat_auto_{i:02d}", auto_tune=True, exploration=False,
                       target_sequence=[(0.0, 0.0)], duration_s=8.0, y0=y0, rng_seed=1000 + i)
        manual_metrics.append(settling_metrics(m))
        auto_metrics.append(settling_metrics(a))

    def agg(metrics_list, key):
        vals = [m[key] for m in metrics_list if m[key] is not None]
        return {"mean": float(np.mean(vals)), "std": float(np.std(vals)), "n": len(vals)}

    results["repeated_trials_n"] = n_trials
    results["manual_gains_aggregate"] = {
        "settling_time_s": agg(manual_metrics, "settling_time_s"),
        "overshoot_pct": agg(manual_metrics, "overshoot_pct"),
        "steady_state_error_m": agg(manual_metrics, "steady_state_error_m"),
    }
    results["auto_tune_aggregate"] = {
        "settling_time_s": agg(auto_metrics, "settling_time_s"),
        "overshoot_pct": agg(auto_metrics, "overshoot_pct"),
        "steady_state_error_m": agg(auto_metrics, "steady_state_error_m"),
    }
    results["ground_truth_plant"] = {"A_true": A_TRUE, "B_true": B_TRUE}

    with open(os.path.join(OUT_DIR, "results_summary.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    # ------------------------------- Figures -------------------------------
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.4))
    for ax, trial, label in [(axes[0], trial_manual, "Manual (scenario-scaled) gains"),
                              (axes[0], trial_auto, "Auto-tune (RLS/LMS critical damping)")]:
        pass
    t_m = [r["t"] for r in trial_manual]
    y_m = [r["y"] for r in trial_manual]
    t_a = [r["t"] for r in trial_auto]
    y_a = [r["y"] for r in trial_auto]
    axes[0].plot(t_m, y_m, label="Manual gains", color="#d62728")
    axes[0].plot(t_a, y_a, label="Auto-tune", color="#1f77b4")
    axes[0].axhline(0.0, color="gray", linestyle="--", linewidth=0.8, label="Target")
    axes[0].fill_between(t_m, -0.02, 0.02, color="gray", alpha=0.15)
    axes[0].set_xlabel("Time (s)")
    axes[0].set_ylabel("Ball position y (m)")
    axes[0].set_title("(a) Step response, y0 = 0.15 m")
    axes[0].legend(fontsize=7)

    import csv as _csv
    with open(os.path.join(DATA_DIR, "target_disconnect_check.csv"), encoding="utf-8") as f:
        disc_rows = list(_csv.DictReader(f))
    t_d = [float(r["t"]) for r in disc_rows]
    y_d = [float(r["y"]) for r in disc_rows]
    tgt_d = [float(r["target_y"]) for r in disc_rows]
    axes[1].plot(t_d, y_d, label="Actual ball position", color="#1f77b4")
    axes[1].plot(t_d, tgt_d, label="Internal target_y (Eq. 23)", color="gray", linestyle="--")
    axes[1].set_xlabel("Time (s)")
    axes[1].set_ylabel("y (m)")
    axes[1].set_title("(b) Active-exploration setpoint vs. actual ball position")
    axes[1].legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "fig_step_response.png"), dpi=200)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(9, 3.2))
    t_ne = [r["t"] for r in trial_no_excite]
    t_e = [r["t"] for r in trial_excite]
    axes[0].plot(t_ne, [r["est_a"] for r in trial_no_excite], label="No excitation", color="#d62728")
    axes[0].plot(t_e, [r["est_a"] for r in trial_excite], label="Persistent excitation (Eq. 23)", color="#1f77b4")
    axes[0].axhline(A_TRUE, color="black", linestyle=":", linewidth=1.0, label="True A")
    axes[0].set_xlabel("Time (s)")
    axes[0].set_ylabel("est_a")
    axes[0].set_title("(a) Control-authority estimate")
    axes[0].legend(fontsize=7)

    axes[1].plot(t_ne, [r["est_b"] for r in trial_no_excite], label="No excitation", color="#d62728")
    axes[1].plot(t_e, [r["est_b"] for r in trial_excite], label="Persistent excitation (Eq. 23)", color="#1f77b4")
    axes[1].axhline(B_TRUE, color="black", linestyle=":", linewidth=1.0, label="True B")
    axes[1].set_xlabel("Time (s)")
    axes[1].set_ylabel("est_b")
    axes[1].set_title("(b) Damping-coefficient estimate")
    axes[1].legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "fig_identification.png"), dpi=200)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    scenarios = sorted(set(r["scenario"] for r in trial_manual))
    scenario_idx = {s: i for i, s in enumerate(scenarios)}
    ax.step([r["t"] for r in trial_manual], [scenario_idx[r["scenario"]] for r in trial_manual], where="post")
    ax.set_yticks(list(scenario_idx.values()))
    ax.set_yticklabels(list(scenario_idx.keys()), fontsize=7)
    ax.set_xlabel("Time (s)")
    ax.set_title("Active control scenario over the manual-gain step-response trial")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "fig_scenario_timeline.png"), dpi=200)
    plt.close(fig)

    # ---- Distribution of settling time / overshoot / SSE across the N=20 repeated trials ----
    def vals_or_nan(metrics_list, key):
        return [m[key] if m[key] is not None else np.nan for m in metrics_list]

    fig, axes = plt.subplots(1, 3, figsize=(10, 3.2))
    metric_specs = [
        ("settling_time_s", "Settling time (s)"),
        ("overshoot_pct", "Overshoot (%)"),
        ("steady_state_error_m", "Steady-state error (m)"),
    ]
    for ax, (key, ylabel) in zip(axes, metric_specs):
        manual_vals = [v for v in vals_or_nan(manual_metrics, key) if not np.isnan(v)]
        auto_vals = [v for v in vals_or_nan(auto_metrics, key) if not np.isnan(v)]
        bp = ax.boxplot([manual_vals, auto_vals], labels=["Manual", "Auto-tune"], widths=0.5, showmeans=True)
        xs_m = np.random.RandomState(0).normal(1, 0.04, size=len(manual_vals))
        xs_a = np.random.RandomState(1).normal(2, 0.04, size=len(auto_vals))
        ax.scatter(xs_m, manual_vals, s=10, alpha=0.6, color="#d62728", zorder=3)
        ax.scatter(xs_a, auto_vals, s=10, alpha=0.6, color="#1f77b4", zorder=3)
        ax.set_ylabel(ylabel, fontsize=8)
        ax.tick_params(labelsize=8)
    fig.suptitle("Per-trial spread across N=20 randomized initial offsets, manual vs. auto-tune", fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "fig_repeated_trial_distributions.png"), dpi=200)
    plt.close(fig)

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
