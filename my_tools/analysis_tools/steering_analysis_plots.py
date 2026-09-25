import matplotlib.pyplot as plt
from my_tools.data_processing.signal_utils import get_outing_files
from my_tools.data_processing.telemetry_processor import (
    process_outing_steering_and_curvature,
)

COLORS = {"Outing 1": "#1f77b4", "Outing 2": "#ff7f0e"}
SCATTER_STYLE = {"s": 60, "alpha": 0.85, "edgecolor": "k", "linewidth": 0.8}
MIN_STEER_THRESHOLD = 10.0


def run_steering_analysis(outing1_files, outing2_files):
    """Processes steering and trajectory curvature telemetry and renders figures."""
    laps_steer_o1, steer_speed_o1, laps_curv_o1, curvature_o1 = (
        process_outing_steering_and_curvature(
            outing1_files,
            min_steering_rate=MIN_STEER_THRESHOLD,
            min_lat_acc_g=0.2,
            min_speed_kmh=30.0,
        )
    )
    laps_steer_o2, steer_speed_o2, laps_curv_o2, curvature_o2 = (
        process_outing_steering_and_curvature(
            outing2_files,
            min_steering_rate=MIN_STEER_THRESHOLD,
            min_lat_acc_g=0.2,
            min_speed_kmh=30.0,
        )
    )

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    if laps_steer_o1:
        ax1.scatter(
            laps_steer_o1,
            steer_speed_o1,
            color=COLORS["Outing 1"],
            label="Outing 1",
            **SCATTER_STYLE,
        )
    if laps_steer_o2:
        ax1.scatter(
            laps_steer_o2,
            steer_speed_o2,
            color=COLORS["Outing 2"],
            label="Outing 2",
            **SCATTER_STYLE,
        )

    ax1.set_title(
        f"Average Absolute Steering Speed per Lap (≥{MIN_STEER_THRESHOLD:.0f} deg/s)",
        fontsize=12,
        pad=12,
    )
    ax1.set_xlabel("Lap Number", fontsize=11)
    ax1.set_ylabel("Steering Speed (deg/s)", fontsize=11)
    ax1.set_ylim(bottom=20, top=70)
    ax1.grid(True, linestyle="--", alpha=0.6)
    ax1.legend(loc="best", fontsize=10)

    if laps_curv_o1:
        ax2.scatter(
            laps_curv_o1,
            curvature_o1,
            color=COLORS["Outing 1"],
            label="Outing 1",
            **SCATTER_STYLE,
        )
    if laps_curv_o2:
        ax2.scatter(
            laps_curv_o2,
            curvature_o2,
            color=COLORS["Outing 2"],
            label="Outing 2",
            **SCATTER_STYLE,
        )

    ax2.set_title(
        "Average Trajectory Curvature per Lap (r = |G_lat| / V²)",
        fontsize=12,
        pad=12,
    )
    ax2.set_xlabel("Lap Number", fontsize=11)
    ax2.set_ylabel("Curvature r (1/m)", fontsize=11)

    all_curv = list(curvature_o1 or ()) + list(curvature_o2 or ())
    if all_curv:
        ax2.set_ylim(bottom=min(all_curv) * 0.7, top=max(all_curv) * 1.3)
    else:
        ax2.set_ylim(bottom=0.002, top=0.05)

    ax2.grid(True, linestyle="--", alpha=0.6)
    ax2.legend(loc="best", fontsize=10)

    all_laps = sorted(
        list(
            set(
                (laps_steer_o1 or ())
                + (laps_steer_o2 or ())
                + (laps_curv_o1 or ())
                + (laps_curv_o2 or ())
            )
        )
    )
    if all_laps:
        ticks = range(min(all_laps), max(all_laps) + 1)
        ax1.set_xticks(ticks)
        ax2.set_xticks(ticks)

    plt.tight_layout()
    fig.canvas.manager.set_window_title("Steering & Trajectory Analysis")


if __name__ == "__main__":
    o1 = get_outing_files("Outing 1")
    o2 = get_outing_files("Outing 2")
    if o1 and o2:
        run_steering_analysis(o1, o2)
        plt.show()