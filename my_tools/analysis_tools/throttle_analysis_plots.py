import matplotlib.pyplot as plt
from my_tools.data_processing.signal_utils import (
    apply_shared_y_limits,
    get_outing_files,
    remap_outing_laps,
    PLOT_COLORS,
    SCATTER_STYLE,
    apply_global_plot_style,
)
from my_tools.data_processing.telemetry_processor import process_outing_throttle

THROTTLE_THRESHOLD = 95.0


def plot_throttle_comparison(data_o1, data_o2):
    """Renders 4-panel layout for full-throttle percentage and application speed (averages + scatters)."""
    apply_global_plot_style()
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 10))

    laps_o1, laps_o2, sorted_laps_1, sorted_laps_2 = remap_outing_laps(data_o1, data_o2)

    pcts_o1 = [item["pct"] for item in sorted_laps_1]
    pcts_o2 = [item["pct"] for item in sorted_laps_2]
    speeds_o1 = [item["avg_throttle_speed"] for item in sorted_laps_1]
    speeds_o2 = [item["avg_throttle_speed"] for item in sorted_laps_2]

    avg_speed_o1 = sum(speeds_o1) / len(speeds_o1) if speeds_o1 else 0.0
    avg_speed_o2 = sum(speeds_o2) / len(speeds_o2) if speeds_o2 else 0.0

    # --- ROW 1: Full Throttle % ---
    bars1 = ax1.bar(
        [0, 1],
        [data_o1["avg_pct"], data_o2["avg_pct"]],
        color=[PLOT_COLORS["Outing 1"], PLOT_COLORS["Outing 2"]],
        edgecolor="black",
        linewidth=1.2,
    )
    for bar in bars1:
        yval = bar.get_height()
        ax1.text(
            bar.get_x() + bar.get_width() / 2.0,
            yval + 1.5,
            f"{yval:.2f}%",
            ha="center",
            va="bottom",
            fontsize=10,
        )

    ax1.set_xticks([0, 1])
    ax1.set_xticklabels(["Outing 1", "Outing 2"])
    ax1.set_title(f"Average Full Throttle % (>= {THROTTLE_THRESHOLD:.0f}%)")
    ax1.set_ylabel("Full Throttle %")
    apply_shared_y_limits(ax1, [data_o1["avg_pct"]], [data_o2["avg_pct"]])
    ax1.grid(axis="y", linestyle="--", alpha=0.6)

    ax2.scatter(laps_o1, pcts_o1, color=PLOT_COLORS["Outing 1"], label="Outing 1", **SCATTER_STYLE)
    ax2.scatter(laps_o2, pcts_o2, color=PLOT_COLORS["Outing 2"], label="Outing 2", **SCATTER_STYLE)

    ax2.set_title(f"Per-lap Full Throttle % (>= {THROTTLE_THRESHOLD:.0f}%)")
    ax2.set_xlabel("Lap")
    ax2.set_ylabel("Full Throttle %")
    apply_shared_y_limits(ax2, pcts_o1, pcts_o2)
    ax2.grid(True, linestyle="--", alpha=0.6)
    ax2.legend(loc="best")

    # --- ROW 2: Throttle Application Speed ---
    bars2 = ax3.bar(
        [0, 1],
        [avg_speed_o1, avg_speed_o2],
        color=[PLOT_COLORS["Outing 1"], PLOT_COLORS["Outing 2"]],
        edgecolor="black",
        linewidth=1.2,
    )
    for bar in bars2:
        yval = bar.get_height()
        ax3.text(
            bar.get_x() + bar.get_width() / 2.0,
            yval + (max(avg_speed_o1, avg_speed_o2, 1.0) * 0.05),
            f"{yval:.1f}%/s",
            ha="center",
            va="bottom",
            fontsize=10,
        )

    ax3.set_xticks([0, 1])
    ax3.set_xticklabels(["Outing 1", "Outing 2"])
    ax3.set_title("Average Throttle Application Speed")
    ax3.set_ylabel("Throttle Speed (%/s)")
    apply_shared_y_limits(ax3, [avg_speed_o1], [avg_speed_o2])
    ax3.grid(axis="y", linestyle="--", alpha=0.6)

    ax4.scatter(laps_o1, speeds_o1, color=PLOT_COLORS["Outing 1"], label="Outing 1", **SCATTER_STYLE)
    ax4.scatter(laps_o2, speeds_o2, color=PLOT_COLORS["Outing 2"], label="Outing 2", **SCATTER_STYLE)

    ax4.set_title("Avg Throttle Application Speed per Lap")
    ax4.set_xlabel("Lap")
    ax4.set_ylabel("Throttle Speed (%/s)")
    apply_shared_y_limits(ax4, speeds_o1, speeds_o2)
    ax4.grid(True, linestyle="--", alpha=0.6)
    ax4.legend(loc="best")

    all_laps = sorted(list(set(laps_o1 + laps_o2)))
    if all_laps:
        ticks = range(min(all_laps), max(all_laps) + 1)
        ax2.set_xticks(ticks)
        ax4.set_xticks(ticks)

    fig.canvas.manager.set_window_title("Throttle Analysis - Outing Comparison")


def run_throttle_analysis(outing1_files, outing2_files):
    """Processes throttle telemetry and renders the comparison figure."""
    data_o1 = process_outing_throttle(
        outing1_files, "Outing 1", full_throttle_threshold=THROTTLE_THRESHOLD
    )
    data_o2 = process_outing_throttle(
        outing2_files, "Outing 2", full_throttle_threshold=THROTTLE_THRESHOLD
    )

    if data_o1 and data_o2:
        plot_throttle_comparison(data_o1, data_o2)


if __name__ == "__main__":
    files_1 = get_outing_files("Outing 1")
    files_2 = get_outing_files("Outing 2")
    if files_1 and files_2:
        run_throttle_analysis(files_1, files_2)
        plt.show()