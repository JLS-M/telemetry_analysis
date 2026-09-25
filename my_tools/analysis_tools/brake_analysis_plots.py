import matplotlib.pyplot as plt
from my_tools.data_processing.signal_utils import get_outing_files
from my_tools.data_processing.telemetry_processor import (
    process_outing_brake_dynamics,
)

COLORS = {"Outing 1": "#1f77b4", "Outing 2": "#ff7f0e"}
SCATTER_STYLE = {"s": 60, "alpha": 0.85, "edgecolor": "k", "linewidth": 0.8}


def run_brake_analysis(outing1_files, outing2_files):
    """Processes brake dynamics telemetry and renders the 2-panel comparison plot."""
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

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    if laps_app_o1:
        ax1.scatter(
            laps_app_o1,
            brake_app_speed_o1,
            color=COLORS["Outing 1"],
            label="Outing 1",
            **SCATTER_STYLE,
        )
    if laps_app_o2:
        ax1.scatter(
            laps_app_o2,
            brake_app_speed_o2,
            color=COLORS["Outing 2"],
            label="Outing 2",
            **SCATTER_STYLE,
        )

    ax1.set_title(
        "Average Brake Application Speed per Lap (>80%/s)",
        fontsize=12,
        pad=12,
    )
    ax1.set_xlabel("Lap Number", fontsize=11)
    ax1.set_ylabel("Application Speed (%/s)", fontsize=11)
    ax1.set_ylim(bottom=80, top=220)
    ax1.grid(True, linestyle="--", alpha=0.6)
    ax1.legend(loc="best", fontsize=10)

    if laps_rel_o1:
        ax2.scatter(
            laps_rel_o1,
            brake_rel_speed_o1,
            color=COLORS["Outing 1"],
            label="Outing 1",
            **SCATTER_STYLE,
        )
    if laps_rel_o2:
        ax2.scatter(
            laps_rel_o2,
            brake_rel_speed_o2,
            color=COLORS["Outing 2"],
            label="Outing 2",
            **SCATTER_STYLE,
        )

    ax2.set_title(
        "Average Brake Release Speed per Lap (<10%/s)",
        fontsize=12,
        pad=12,
    )
    ax2.set_xlabel("Lap Number", fontsize=11)
    ax2.set_ylabel("Release Speed (%/s)", fontsize=11)

    all_rel = list(brake_rel_speed_o1 or ()) + list(brake_rel_speed_o2 or ())
    ax2.set_ylim(bottom=0, top=max(all_rel) * 1.15 if all_rel else 200)
    ax2.grid(True, linestyle="--", alpha=0.6)
    ax2.legend(loc="best", fontsize=10)

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
        ax1.set_xticks(ticks)
        ax2.set_xticks(ticks)

    plt.tight_layout()
    fig.canvas.manager.set_window_title("Brake Dynamics Analysis")


if __name__ == "__main__":
    o1 = get_outing_files("Outing 1")
    o2 = get_outing_files("Outing 2")
    if o1 and o2:
        run_brake_analysis(o1, o2)
        plt.show()