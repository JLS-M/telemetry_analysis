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
    process_outing_brake_dynamics,
)


def run_brake_analysis(outing1_files, outing2_files):
    """Processes brake dynamics telemetry and renders the 4-panel comparison figure."""
    apply_global_plot_style()
    laps_app_o1, brake_app_speed_o1, laps_rel_o1, brake_rel_speed_o1 = (
        process_outing_brake_dynamics(
            outing1_files, min_brake_rate=80.0, min_release_rate=10.0
        )
    )
    laps_app_o2, brake_app_speed_o2, laps_rel_o2, brake_rel_speed_o2 = (
        process_outing_brake_dynamics(
            outing2_files, min_brake_rate=80.0, min_release_rate=10.0
        )
    )

    (
        laps_app_o1,
        laps_rel_o1,
        laps_app_o2,
        laps_rel_o2,
    ) = remap_lap_lists(
        laps_app_o1, laps_rel_o1, laps_app_o2, laps_rel_o2
    )

    avg_app_o1 = (
        sum(brake_app_speed_o1) / len(brake_app_speed_o1)
        if brake_app_speed_o1
        else 0.0
    )
    avg_app_o2 = (
        sum(brake_app_speed_o2) / len(brake_app_speed_o2)
        if brake_app_speed_o2
        else 0.0
    )

    avg_rel_o1 = (
        sum(brake_rel_speed_o1) / len(brake_rel_speed_o1)
        if brake_rel_speed_o1
        else 0.0
    )
    avg_rel_o2 = (
        sum(brake_rel_speed_o2) / len(brake_rel_speed_o2)
        if brake_rel_speed_o2
        else 0.0
    )

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 10))

    # --- ROW 1: Brake Application ---
    bars1 = ax1.bar(
        [0, 1],
        [avg_app_o1, avg_app_o2],
        color=[PLOT_COLORS["Outing 1"], PLOT_COLORS["Outing 2"]],
        edgecolor="black",
        linewidth=1.2,
    )
    for bar in bars1:
        yval = bar.get_height()
        ax1.text(
            bar.get_x() + bar.get_width() / 2.0,
            yval + (max(avg_app_o1, avg_app_o2, 1.0) * 0.05),
            f"{yval:.1f}%/s",
            ha="center",
            va="bottom",
            fontsize=10,
        )
    ax1.set_xticks([0, 1])
    ax1.set_xticklabels(["Outing 1", "Outing 2"])
    ax1.set_title("Average Brake Application Speed")
    ax1.set_ylabel("Application Speed (%/s)")
    apply_shared_y_limits(ax1, [avg_app_o1], [avg_app_o2])
    ax1.grid(axis="y", linestyle="--", alpha=0.6)

    if laps_app_o1:
        ax2.scatter(
            laps_app_o1,
            brake_app_speed_o1,
            color=PLOT_COLORS["Outing 1"],
            label="Outing 1",
            **SCATTER_STYLE,
        )
    if laps_app_o2:
        ax2.scatter(
            laps_app_o2,
            brake_app_speed_o2,
            color=PLOT_COLORS["Outing 2"],
            label="Outing 2",
            **SCATTER_STYLE,
        )

    all_app = list(brake_app_speed_o1 or ()) + list(brake_app_speed_o2 or ())
    max_app = max(all_app) if all_app else 200.0
    ax2.set_ylim(bottom=80, top=max_app * 1.3)
    ax2.set_title("Brake Application Speed per Lap (>80%/s)")
    ax2.set_xlabel("Lap")
    ax2.set_ylabel("Application Speed (%/s)")
    ax2.grid(True, linestyle="--", alpha=0.6)
    ax2.legend(loc="best")

    # --- ROW 2: Brake Release ---
    bars2 = ax3.bar(
        [0, 1],
        [avg_rel_o1, avg_rel_o2],
        color=[PLOT_COLORS["Outing 1"], PLOT_COLORS["Outing 2"]],
        edgecolor="black",
        linewidth=1.2,
    )
    for bar in bars2:
        yval = bar.get_height()
        ax3.text(
            bar.get_x() + bar.get_width() / 2.0,
            yval + (max(avg_rel_o1, avg_rel_o2, 1.0) * 0.05),
            f"{yval:.1f}%/s",
            ha="center",
            va="bottom",
            fontsize=10,
        )
    ax3.set_xticks([0, 1])
    ax3.set_xticklabels(["Outing 1", "Outing 2"])
    ax3.set_title("Average Brake Release Speed")
    ax3.set_ylabel("Release Speed (%/s)")
    apply_shared_y_limits(ax3, [avg_rel_o1], [avg_rel_o2])
    ax3.grid(axis="y", linestyle="--", alpha=0.6)

    if laps_rel_o1:
        ax4.scatter(
            laps_rel_o1,
            brake_rel_speed_o1,
            color=PLOT_COLORS["Outing 1"],
            label="Outing 1",
            **SCATTER_STYLE,
        )
    if laps_rel_o2:
        ax4.scatter(
            laps_rel_o2,
            brake_rel_speed_o2,
            color=PLOT_COLORS["Outing 2"],
            label="Outing 2",
            **SCATTER_STYLE,
        )

    all_rel = list(brake_rel_speed_o1 or ()) + list(brake_rel_speed_o2 or ())
    max_rel = max(all_rel) if all_rel else 200.0
    ax4.set_ylim(bottom=0, top=max_rel * 1.3)
    ax4.set_title("Brake Release Speed per Lap (<10%/s)")
    ax4.set_xlabel("Lap")
    ax4.set_ylabel("Release Speed (%/s)")
    ax4.grid(True, linestyle="--", alpha=0.6)
    ax4.legend(loc="best")

    all_laps = sorted(
        list(
            set(
                (laps_app_o1 or ())
                + (laps_app_o2 or ())
                + (laps_rel_o1 or ())
                + (laps_rel_o2 or ())
            )
        )
    )
    if all_laps:
        ticks = range(min(all_laps), max(all_laps) + 1)
        ax2.set_xticks(ticks)
        ax4.set_xticks(ticks)

    plt.tight_layout()
    fig.canvas.manager.set_window_title("Brake Dynamics Analysis")


if __name__ == "__main__":
    o1 = get_outing_files("Outing 1")
    o2 = get_outing_files("Outing 2")
    if o1 and o2:
        run_brake_analysis(o1, o2)
        plt.show()