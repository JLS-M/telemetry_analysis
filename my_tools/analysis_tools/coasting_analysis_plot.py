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

SMOOTH_SAMPLES = 9
THROTTLE_THRESHOLD = 95.0


def run_coasting_analysis(outing1_files, outing2_files):
    """Processes pre-braking coasting percentage relative to lap time and renders 2-panel comparison."""
    apply_global_plot_style()
    data_o1 = process_outing_throttle(
        outing1_files,
        "Outing 1",
        smooth_samples=SMOOTH_SAMPLES,
        full_throttle_threshold=THROTTLE_THRESHOLD,
    )
    data_o2 = process_outing_throttle(
        outing2_files,
        "Outing 2",
        smooth_samples=SMOOTH_SAMPLES,
        full_throttle_threshold=THROTTLE_THRESHOLD,
    )

    if not data_o1 or not data_o2:
        return

    laps_o1, laps_o2, sorted_laps_1, sorted_laps_2 = remap_outing_laps(data_o1, data_o2)

    pcts_o1 = [
        (
            (item["total_coasting_time"] / item["total_lap_time"] * 100.0)
            if item.get("total_lap_time", 0) > 0
            else 0.0
        )
        for item in sorted_laps_1
    ]
    pcts_o2 = [
        (
            (item["total_coasting_time"] / item["total_lap_time"] * 100.0)
            if item.get("total_lap_time", 0) > 0
            else 0.0
        )
        for item in sorted_laps_2
    ]

    avg_pct_o1 = sum(pcts_o1) / len(pcts_o1) if pcts_o1 else 0.0
    avg_pct_o2 = sum(pcts_o2) / len(pcts_o2) if pcts_o2 else 0.0
    all_lap_pcts = pcts_o1 + pcts_o2

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # --- Panel 1: Outing Average Bar Chart ---
    bars = ax1.bar(
        [0, 1],
        [avg_pct_o1, avg_pct_o2],
        color=[PLOT_COLORS["Outing 1"], PLOT_COLORS["Outing 2"]],
        edgecolor="black",
        linewidth=1.2,
    )
    for bar in bars:
        yval = bar.get_height()
        ax1.text(
            bar.get_x() + bar.get_width() / 2.0,
            yval + (max(avg_pct_o1, avg_pct_o2, 1.0) * 0.05),
            f"{yval:.2f}%",
            ha="center",
            va="bottom",
            fontsize=10,
        )

    ax1.set_xticks([0, 1])
    ax1.set_xticklabels(["Outing 1", "Outing 2"])
    ax1.set_title("Average Pre-Braking Coasting Time")
    ax1.set_ylabel("Coasting Time (% of Lap Time)")
    apply_shared_y_limits(ax1, [avg_pct_o1], [avg_pct_o2])
    ax1.grid(axis="y", linestyle="--", alpha=0.6)

    # --- Panel 2: Lap-by-Lap Scatter Plot ---
    ax2.scatter(
        laps_o1,
        pcts_o1,
        color=PLOT_COLORS["Outing 1"],
        label="Outing 1",
        zorder=3,
        **SCATTER_STYLE,
    )
    ax2.scatter(
        laps_o2,
        pcts_o2,
        color=PLOT_COLORS["Outing 2"],
        label="Outing 2",
        zorder=3,
        **SCATTER_STYLE,
    )

    max_pct = max(all_lap_pcts) if all_lap_pcts else 10.0
    ax2.set_ylim(bottom=0, top=max_pct * 1.3)

    ax2.set_title("Pre-Braking Coasting Time (% of Total Lap Time) per Lap")
    ax2.set_xlabel("Lap")
    ax2.set_ylabel("Coasting Time (% of Lap Time)")

    all_laps = sorted(list(set(laps_o1 + laps_o2)))
    if all_laps:
        ax2.set_xticks(range(min(all_laps), max(all_laps) + 1))

    ax2.grid(True, linestyle="--", alpha=0.6)
    ax2.legend(loc="best")

    plt.tight_layout()
    fig.canvas.manager.set_window_title("Coasting Analysis - Outing Comparison")


if __name__ == "__main__":
    o1 = get_outing_files("Outing 1")
    o2 = get_outing_files("Outing 2")
    if o1 and o2:
        run_coasting_analysis(o1, o2)
        plt.show()