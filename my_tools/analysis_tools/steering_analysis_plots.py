import matplotlib.pyplot as plt
from my_tools.data_processing.signal_utils import (
    apply_shared_y_limits,
    get_outing_files,
    remap_lap_lists,
    PLOT_COLORS,
    SCATTER_STYLE,
    apply_global_plot_style,
)
from my_tools.data_processing.telemetry_processor import (
    process_outing_steering_and_curvature,
)

MIN_STEER_THRESHOLD = 10.0


def run_steering_analysis(outing1_files, outing2_files):
    """Processes steering and trajectory curvature telemetry and renders the 4-panel comparison figure."""
    apply_global_plot_style()
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

    (
        laps_steer_o1,
        laps_curv_o1,
        laps_steer_o2,
        laps_curv_o2,
    ) = remap_lap_lists(
        laps_steer_o1, laps_curv_o1, laps_steer_o2, laps_curv_o2
    )

    avg_steer_o1 = (
        sum(steer_speed_o1) / len(steer_speed_o1) if steer_speed_o1 else 0.0
    )
    avg_steer_o2 = (
        sum(steer_speed_o2) / len(steer_speed_o2) if steer_speed_o2 else 0.0
    )

    avg_curv_o1 = (
        sum(curvature_o1) / len(curvature_o1) if curvature_o1 else 0.0
    )
    avg_curv_o2 = (
        sum(curvature_o2) / len(curvature_o2) if curvature_o2 else 0.0
    )

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 10))

    # --- ROW 1: Steering Speed ---
    bars1 = ax1.bar(
        [0, 1],
        [avg_steer_o1, avg_steer_o2],
        color=[PLOT_COLORS["Outing 1"], PLOT_COLORS["Outing 2"]],
        edgecolor="black",
        linewidth=1.2,
    )
    for bar in bars1:
        yval = bar.get_height()
        ax1.text(
            bar.get_x() + bar.get_width() / 2.0,
            yval + (max(avg_steer_o1, avg_steer_o2, 1.0) * 0.05),
            f"{yval:.1f}°/s",
            ha="center",
            va="bottom",
            fontsize=10,
        )
    ax1.set_xticks([0, 1])
    ax1.set_xticklabels(["Outing 1", "Outing 2"])
    ax1.set_title("Average Absolute Steering Rate")
    ax1.set_ylabel("Steering Rate (deg/s)")
    apply_shared_y_limits(ax1, [avg_steer_o1], [avg_steer_o2])
    ax1.grid(axis="y", linestyle="--", alpha=0.6)

    if laps_steer_o1:
        ax2.scatter(
            laps_steer_o1,
            steer_speed_o1,
            color=PLOT_COLORS["Outing 1"],
            label="Outing 1",
            **SCATTER_STYLE,
        )
    if laps_steer_o2:
        ax2.scatter(
            laps_steer_o2,
            steer_speed_o2,
            color=PLOT_COLORS["Outing 2"],
            label="Outing 2",
            **SCATTER_STYLE,
        )

    all_steer = list(steer_speed_o1 or ()) + list(steer_speed_o2 or ())
    max_steer = max(all_steer) if all_steer else 70.0
    ax2.set_ylim(bottom=20, top=max_steer * 1.3)
    ax2.set_title(
        f"Average Absolute Steering Rate per Lap (≥{MIN_STEER_THRESHOLD:.0f} deg/s)"
    )
    ax2.set_xlabel("Lap")
    ax2.set_ylabel("Steering Rate (deg/s)")
    ax2.grid(True, linestyle="--", alpha=0.6)
    ax2.legend(loc="best")

    # --- ROW 2: Trajectory Curvature ---
    bars2 = ax3.bar(
        [0, 1],
        [avg_curv_o1, avg_curv_o2],
        color=[PLOT_COLORS["Outing 1"], PLOT_COLORS["Outing 2"]],
        edgecolor="black",
        linewidth=1.2,
    )
    for bar in bars2:
        yval = bar.get_height()
        ax3.text(
            bar.get_x() + bar.get_width() / 2.0,
            yval + (max(avg_curv_o1, avg_curv_o2, 0.001) * 0.05),
            f"{yval:.4f}",
            ha="center",
            va="bottom",
            fontsize=10,
        )
    ax3.set_xticks([0, 1])
    ax3.set_xticklabels(["Outing 1", "Outing 2"])
    ax3.set_title("Average Trajectory Curvature")
    ax3.set_ylabel("Curvature r (1/m)")
    apply_shared_y_limits(ax3, [avg_curv_o1], [avg_curv_o2])
    ax3.grid(axis="y", linestyle="--", alpha=0.6)

    if laps_curv_o1:
        ax4.scatter(
            laps_curv_o1,
            curvature_o1,
            color=PLOT_COLORS["Outing 1"],
            label="Outing 1",
            **SCATTER_STYLE,
        )
    if laps_curv_o2:
        ax4.scatter(
            laps_curv_o2,
            curvature_o2,
            color=PLOT_COLORS["Outing 2"],
            label="Outing 2",
            **SCATTER_STYLE,
        )

    all_curv = list(curvature_o1 or ()) + list(curvature_o2 or ())
    max_curv = max(all_curv) if all_curv else 0.05
    min_curv = min(all_curv) if all_curv else 0.0
    ax4.set_ylim(bottom=min_curv * 0.7 if min_curv > 0 else 0, top=max_curv * 1.3)
    ax4.set_title("Average Trajectory Curvature per Lap (r = |G_lat| / V²)")
    ax4.set_xlabel("Lap")
    ax4.set_ylabel("Curvature r (1/m)")
    ax4.grid(True, linestyle="--", alpha=0.6)
    ax4.legend(loc="best")

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
        ax2.set_xticks(ticks)
        ax4.set_xticks(ticks)

    plt.tight_layout()
    fig.canvas.manager.set_window_title("Steering & Trajectory Analysis")


if __name__ == "__main__":
    o1 = get_outing_files("Outing 1")
    o2 = get_outing_files("Outing 2")
    if o1 and o2:
        run_steering_analysis(o1, o2)
        plt.show()