import matplotlib.pyplot as plt
from my_tools.data_processing.signal_utils import (
    apply_shared_y_limits,
    get_outing_files,
)
from my_tools.data_processing.telemetry_processor import process_outing_throttle

SMOOTH_SAMPLES = 9
THROTTLE_THRESHOLD = 95.0
COLORS = {"Outing 1": "#1f77b4", "Outing 2": "#ff7f0e"}
SCATTER_STYLE = {"s": 80, "alpha": 0.85, "edgecolor": "black", "linewidth": 0.8}


def run_coasting_analysis(outing1_files, outing2_files):
    """Processes pre-braking coasting percentage relative to lap time and renders 2-panel comparison."""
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

    outings_data = [("Outing 1", data_o1), ("Outing 2", data_o2)]

    # Compute lap percentages and session averages
    pcts_o1 = [
        (
            (item["total_coasting_time"] / item["total_lap_time"] * 100.0)
            if item.get("total_lap_time", 0) > 0
            else 0.0
        )
        for item in data_o1["laps"]
    ]
    pcts_o2 = [
        (
            (item["total_coasting_time"] / item["total_lap_time"] * 100.0)
            if item.get("total_lap_time", 0) > 0
            else 0.0
        )
        for item in data_o2["laps"]
    ]

    avg_pct_o1 = sum(pcts_o1) / len(pcts_o1) if pcts_o1 else 0.0
    avg_pct_o2 = sum(pcts_o2) / len(pcts_o2) if pcts_o2 else 0.0

    all_lap_pcts = pcts_o1 + pcts_o2
    min_lap = min(
        [item["lap_num"] for name, data in outings_data for item in data["laps"]]
        or [1]
    )
    max_lap = max(
        [item["lap_num"] for name, data in outings_data for item in data["laps"]]
        or [1]
    )

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # --- Panel 1: Outing Average Bar Chart ---
    bars = ax1.bar(
        [0, 1],
        [avg_pct_o1, avg_pct_o2],
        color=[COLORS["Outing 1"], COLORS["Outing 2"]],
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
    ax1.set_title("Average Pre-Braking Coasting Time", fontsize=11, pad=12)
    ax1.set_ylabel("Coasting Time (% of Lap Time)", fontsize=10)
    apply_shared_y_limits(ax1, [avg_pct_o1], [avg_pct_o2])
    ax1.grid(axis="y", linestyle="--", alpha=0.6)

    # --- Panel 2: Lap-by-Lap Scatter Plot ---
    for name, data in outings_data:
        x_laps = [item["lap_num"] for item in data["laps"]]
        y_coasting_pct = (
            pcts_o1 if name == "Outing 1" else pcts_o2
        )

        ax2.scatter(
            x_laps,
            y_coasting_pct,
            color=COLORS[name],
            label=name,
            zorder=3,
            **SCATTER_STYLE,
        )

    max_pct = max(all_lap_pcts) if all_lap_pcts else 10.0
    ax2.set_ylim(bottom=0, top=max_pct * 1.3)

    ax2.set_title(
        "Pre-Braking Coasting Time (% of Total Lap Time) per Lap",
        fontsize=11,
        pad=12,
    )
    ax2.set_xlabel("Lap Number", fontsize=10)
    ax2.set_ylabel("Coasting Time (% of Lap Time)", fontsize=10)
    ax2.set_xticks(range(min_lap, max_lap + 1))
    ax2.grid(True, linestyle="--", alpha=0.6)
    ax2.legend(loc="best", fontsize=10)

    plt.tight_layout()
    fig.canvas.manager.set_window_title("Coasting Analysis - Outing Comparison")


if __name__ == "__main__":
    o1 = get_outing_files("Outing 1")
    o2 = get_outing_files("Outing 2")
    if o1 and o2:
        run_coasting_analysis(o1, o2)
        plt.show()