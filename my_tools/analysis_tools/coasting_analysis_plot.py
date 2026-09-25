import matplotlib.pyplot as plt
from my_tools.data_processing.signal_utils import get_outing_files
from my_tools.data_processing.telemetry_processor import process_outing_throttle

SMOOTH_SAMPLES = 9
THROTTLE_THRESHOLD = 95.0
COLORS = {"Outing 1": "#1f77b4", "Outing 2": "#ff7f0e"}


def run_coasting_analysis(outing1_files, outing2_files):
    """Processes pre-braking coasting time and renders scatter comparison."""
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

    all_lap_nums = []
    for name, data in outings_data:
        all_lap_nums.extend([item["lap_num"] for item in data["laps"]])

    min_lap = min(all_lap_nums) if all_lap_nums else 1
    max_lap = max(all_lap_nums) if all_lap_nums else 1

    fig, ax = plt.subplots(figsize=(10, 6))

    for name, data in outings_data:
        x_laps = [item["lap_num"] for item in data["laps"]]
        y_coasting = [item["total_coasting_time"] for item in data["laps"]]

        ax.scatter(
            x_laps,
            y_coasting,
            color=COLORS[name],
            label=name,
            s=80,
            alpha=0.85,
            edgecolor="black",
            linewidth=0.8,
            zorder=3,
        )

    ax.set_title(
        "Total Pre-Braking Coasting Time per Lap\nby Lap Number",
        fontsize=12,
        pad=15,
    )
    ax.set_xlabel("Lap Number", fontsize=11)
    ax.set_ylabel("Total Pre-Braking Coasting Time (s)", fontsize=11)
    ax.set_ylim(0, 8)
    ax.set_xticks(range(min_lap, max_lap + 1))
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.legend(loc="best", fontsize=10)

    plt.tight_layout()
    fig.canvas.manager.set_window_title("Coasting Analysis - Outing Comparison")


if __name__ == "__main__":
    o1 = get_outing_files("Outing 1")
    o2 = get_outing_files("Outing 2")
    if o1 and o2:
        run_coasting_analysis(o1, o2)
        plt.show()