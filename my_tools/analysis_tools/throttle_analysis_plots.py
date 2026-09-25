import matplotlib.pyplot as plt
from my_tools.data_processing.signal_utils import (
    apply_shared_y_limits,
    get_outing_files,
)
from my_tools.data_processing.telemetry_processor import process_outing_throttle

COLORS = {"Outing 1": "#1f77b4", "Outing 2": "#ff7f0e"}
THROTTLE_THRESHOLD = 95.0


def plot_throttle_comparison(data_o1, data_o2):
    """Renders 3-panel layout for full-throttle percentage and speed."""
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(16, 5))
    outings = [("Outing 1", data_o1), ("Outing 2", data_o2)]

    bars = ax1.bar(
        [0, 1],
        [data_o1["avg_pct"], data_o2["avg_pct"]],
        color=[COLORS["Outing 1"], COLORS["Outing 2"]],
        edgecolor="black",
        linewidth=1.2,
    )
    for bar in bars:
        yval = bar.get_height()
        ax1.text(
            bar.get_x() + bar.get_width() / 2.0,
            yval + 1.5,
            f"{yval:.2f}%",
            ha="center",
            va="bottom",
        )

    ax1.set_xticks([0, 1])
    ax1.set_xticklabels(["Outing 1", "Outing 2"])
    ax1.set_title(
        f"Average Full Throttle % (>= {THROTTLE_THRESHOLD:.0f}%)",
        fontsize=11,
        pad=12,
    )
    ax1.set_ylabel("Full Throttle %", fontsize=10)
    apply_shared_y_limits(ax1, [data_o1["avg_pct"]], [data_o2["avg_pct"]])
    ax1.grid(axis="y", linestyle="--", alpha=0.6)

    pcts_o1 = [item["pct"] for item in data_o1["laps"]]
    pcts_o2 = [item["pct"] for item in data_o2["laps"]]
    speeds_o1 = [item["avg_throttle_speed"] for item in data_o1["laps"]]
    speeds_o2 = [item["avg_throttle_speed"] for item in data_o2["laps"]]

    for name, data in outings:
        laps = [item["lap_num"] for item in data["laps"]]
        pcts = [item["pct"] for item in data["laps"]]
        speeds = [item["avg_throttle_speed"] for item in data["laps"]]

        ax2.scatter(
            laps,
            pcts,
            color=COLORS[name],
            label=name,
            s=70,
            alpha=0.85,
            edgecolor="black",
        )
        ax3.scatter(
            laps,
            speeds,
            color=COLORS[name],
            label=name,
            s=70,
            alpha=0.85,
            edgecolor="black",
        )

    ax2.set_title(
        f"Per-lap Full Throttle % (>= {THROTTLE_THRESHOLD:.0f}%)", fontsize=11, pad=12
    )
    ax2.set_xlabel("Lap Number", fontsize=10)
    ax2.set_ylabel("Full Throttle %", fontsize=10)
    apply_shared_y_limits(ax2, pcts_o1, pcts_o2)
    ax2.grid(True, linestyle="--", alpha=0.6)
    ax2.legend(loc="best")

    ax3.set_title(
        "Avg Throttle Application Speed", fontsize=11, pad=12
    )
    ax3.set_xlabel("Lap Number", fontsize=10)
    ax3.set_ylabel("Throttle Speed (%/s)", fontsize=10)
    apply_shared_y_limits(ax3, speeds_o1, speeds_o2)
    ax3.grid(True, linestyle="--", alpha=0.6)
    ax3.legend(loc="best")

    plt.tight_layout()
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