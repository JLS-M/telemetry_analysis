import os
import matplotlib.pyplot as plt

# Import centralized file picker helper
from my_tools.data_processing.signal_utils import get_outing_files

# Import optimized single-pass processor functions
from my_tools.data_processing.telemetry_processor import (
    process_outing_brake_dynamics,
    process_outing_steering_and_curvature,
    process_outing_throttle,
)

# Shared plot styling constants
COLORS = {"Outing 1": "#1f77b4", "Outing 2": "#ff7f0e"}
SCATTER_STYLE = {"s": 60, "alpha": 0.85, "edgecolor": "k", "linewidth": 0.8}
THROTTLE_THRESHOLD = 95.0
SMOOTH_SAMPLES = 9


def format_x_ticks(axes, *lap_lists):
    """Applies discrete integer lap ticks across multiple matplotlib axes."""
    all_laps = set()
    for laps in lap_lists:
        if laps:
            all_laps.update(laps)
    if all_laps:
        ticks = range(min(all_laps), max(all_laps) + 1)
        for ax in axes:
            ax.set_xticks(ticks)


def apply_shared_y_limits(ax, *data_lists):
    """Sets Y-axis bounds: 70% of min value and 130% (+30%) of max value across input series."""
    combined = []
    for d in data_lists:
        if d:
            combined.extend(d)

    if combined:
        min_val = min(combined)
        max_val = max(combined)

        # Handle edge cases where values are zero or negative
        y_min = min_val * 0.7 if min_val > 0 else min_val * 1.3
        y_max = max_val * 1.3 if max_val > 0 else max_val * 0.7

        # If min and max are identical (flat signal), frame around that value
        if y_min == y_max:
            y_min = y_min * 0.7 if y_min != 0 else -1.0
            y_max = y_max * 1.3 if y_max != 0 else 1.0

        ax.set_ylim(bottom=y_min, top=y_max)


# --- 1. PLOT GENERATORS ---


def plot_throttle_comparison(data_o1, data_o2):
    """Renders 3-panel layout: Average %, Full Throttle % per lap, and Throttle Speed."""
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(16, 5))
    outings = [("Outing 1", data_o1), ("Outing 2", data_o2)]

    # Subplot 1: Average Full Throttle Bar Chart
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
        f"Average Full Throttle (>= {THROTTLE_THRESHOLD:.0f}%)",
        fontsize=11,
        pad=12,
    )
    ax1.set_ylabel("Full Throttle %", fontsize=10)
    apply_shared_y_limits(ax1, [data_o1["avg_pct"], data_o2["avg_pct"]])
    ax1.grid(axis="y", linestyle="--", alpha=0.6)

    # Subplot 2 & 3: Per-Lap Scatter Plots
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
        f"Full Throttle % (>= {THROTTLE_THRESHOLD:.0f}%)", fontsize=11, pad=12
    )
    ax2.set_xlabel("Lap Number", fontsize=10)
    ax2.set_ylabel("Percentage (%)", fontsize=10)
    apply_shared_y_limits(ax2, pcts_o1, pcts_o2)
    ax2.grid(True, linestyle="--", alpha=0.6)
    ax2.legend(loc="best")

    ax3.set_title(
        "Avg Positive Throttle Application Speed", fontsize=11, pad=12
    )
    ax3.set_xlabel("Lap Number", fontsize=10)
    ax3.set_ylabel("Throttle Speed (%/s)", fontsize=10)
    apply_shared_y_limits(ax3, speeds_o1, speeds_o2)
    ax3.grid(True, linestyle="--", alpha=0.6)
    ax3.legend(loc="best")

    laps_o1 = [item["lap_num"] for item in data_o1["laps"]]
    laps_o2 = [item["lap_num"] for item in data_o2["laps"]]
    format_x_ticks([ax2, ax3], laps_o1, laps_o2)

    plt.tight_layout()
    fig.canvas.manager.set_window_title("Throttle Analysis - Outing Comparison")


def plot_coasting_comparison(data_o1, data_o2):
    """Renders single scatter plot for total pre-braking coasting time per lap."""
    fig, ax = plt.subplots(figsize=(10, 6))
    outings = [("Outing 1", data_o1), ("Outing 2", data_o2)]

    coasting_o1 = [item["total_coasting_time"] for item in data_o1["laps"]]
    coasting_o2 = [item["total_coasting_time"] for item in data_o2["laps"]]

    for name, data in outings:
        laps = [item["lap_num"] for item in data["laps"]]
        coasting = [item["total_coasting_time"] for item in data["laps"]]

        ax.scatter(
            laps,
            coasting,
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
    apply_shared_y_limits(ax, coasting_o1, coasting_o2)
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.legend(loc="best", fontsize=10)

    laps_o1 = [item["lap_num"] for item in data_o1["laps"]]
    laps_o2 = [item["lap_num"] for item in data_o2["laps"]]
    format_x_ticks([ax], laps_o1, laps_o2)

    plt.tight_layout()
    fig.canvas.manager.set_window_title("Coasting Analysis - Outing Comparison")


def plot_brake_comparison(
    laps_app_o1,
    app_o1,
    laps_rel_o1,
    rel_o1,
    laps_app_o2,
    app_o2,
    laps_rel_o2,
    rel_o2,
):
    """Renders 2-panel layout for brake application and release rates."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    if laps_app_o1:
        ax1.scatter(
            laps_app_o1,
            app_o1,
            color=COLORS["Outing 1"],
            label="Outing 1",
            **SCATTER_STYLE,
        )
    if laps_app_o2:
        ax1.scatter(
            laps_app_o2,
            app_o2,
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
    apply_shared_y_limits(ax1, app_o1, app_o2)
    ax1.grid(True, linestyle="--", alpha=0.6)
    ax1.legend(loc="best", fontsize=10)

    if laps_rel_o1:
        ax2.scatter(
            laps_rel_o1,
            rel_o1,
            color=COLORS["Outing 1"],
            label="Outing 1",
            **SCATTER_STYLE,
        )
    if laps_rel_o2:
        ax2.scatter(
            laps_rel_o2,
            rel_o2,
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
    apply_shared_y_limits(ax2, rel_o1, rel_o2)
    ax2.grid(True, linestyle="--", alpha=0.6)
    ax2.legend(loc="best", fontsize=10)

    format_x_ticks(
        [ax1, ax2], laps_app_o1, laps_app_o2, laps_rel_o1, laps_rel_o2
    )

    plt.tight_layout()
    fig.canvas.manager.set_window_title("Brake Dynamics Analysis")


def plot_steering_comparison(
    laps_steer_o1,
    steer_o1,
    laps_curv_o1,
    curv_o1,
    laps_steer_o2,
    steer_o2,
    laps_curv_o2,
    curv_o2,
):
    """Renders 2-panel layout for steering speed and trajectory curvature."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    if laps_steer_o1:
        ax1.scatter(
            laps_steer_o1,
            steer_o1,
            color=COLORS["Outing 1"],
            label="Outing 1",
            **SCATTER_STYLE,
        )
    if laps_steer_o2:
        ax1.scatter(
            laps_steer_o2,
            steer_o2,
            color=COLORS["Outing 2"],
            label="Outing 2",
            **SCATTER_STYLE,
        )

    ax1.set_title(
        "Average Absolute Steering Speed per Lap (≥10 deg/s)",
        fontsize=12,
        pad=12,
    )
    ax1.set_xlabel("Lap Number", fontsize=11)
    ax1.set_ylabel("Steering Speed (deg/s)", fontsize=11)
    apply_shared_y_limits(ax1, steer_o1, steer_o2)
    ax1.grid(True, linestyle="--", alpha=0.6)
    ax1.legend(loc="best", fontsize=10)

    if laps_curv_o1:
        ax2.scatter(
            laps_curv_o1,
            curv_o1,
            color=COLORS["Outing 1"],
            label="Outing 1",
            **SCATTER_STYLE,
        )
    if laps_curv_o2:
        ax2.scatter(
            laps_curv_o2,
            curv_o2,
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
    apply_shared_y_limits(ax2, curv_o1, curv_o2)
    ax2.grid(True, linestyle="--", alpha=0.6)
    ax2.legend(loc="best", fontsize=10)

    format_x_ticks(
        [ax1, ax2], laps_steer_o1, laps_steer_o2, laps_curv_o1, laps_curv_o2
    )

    plt.tight_layout()
    fig.canvas.manager.set_window_title("Steering & Trajectory Analysis")


# --- 2. MAIN EXECUTION ROUTINE ---


def main():
    print("==================================================")
    print("      OUTING COMPARATIVE TELEMETRY ANALYSIS       ")
    print("==================================================")

    # 1. Prompt for files once per outing
    outing1_files = get_outing_files("Outing 1")
    if not outing1_files:
        print("\nNo files selected for Outing 1. Exiting.")
        return

    outing2_files = get_outing_files("Outing 2")
    if not outing2_files:
        print("\nNo files selected for Outing 2. Exiting.")
        return

    # 2. Process Throttle & Coasting Data (Shared)
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

    if data_o1 is None or data_o2 is None:
        print("\nFailed to process throttle/coasting telemetry data. Exiting.")
        return

    # 3. Process Brake Dynamics Data (Single pass per outing)
    laps_app_o1, app_o1, laps_rel_o1, rel_o1 = process_outing_brake_dynamics(
        outing1_files, min_brake_rate=80.0, min_release_rate=10.0
    )
    laps_app_o2, app_o2, laps_rel_o2, rel_o2 = process_outing_brake_dynamics(
        outing2_files, min_brake_rate=80.0, min_release_rate=10.0
    )

    # 4. Process Steering & Curvature Data (Single pass per outing)
    laps_steer_o1, steer_o1, laps_curv_o1, curv_o1 = (
        process_outing_steering_and_curvature(
            outing1_files,
            min_steering_rate=10.0,
            min_lat_acc_g=0.2,
            min_speed_kmh=30.0,
        )
    )
    laps_steer_o2, steer_o2, laps_curv_o2, curv_o2 = (
        process_outing_steering_and_curvature(
            outing2_files,
            min_steering_rate=10.0,
            min_lat_acc_g=0.2,
            min_speed_kmh=30.0,
        )
    )

    # 5. Build Figures
    plot_throttle_comparison(data_o1, data_o2)
    plot_coasting_comparison(data_o1, data_o2)
    plot_brake_comparison(
        laps_app_o1,
        app_o1,
        laps_rel_o1,
        rel_o1,
        laps_app_o2,
        app_o2,
        laps_rel_o2,
        rel_o2,
    )
    plot_steering_comparison(
        laps_steer_o1,
        steer_o1,
        laps_curv_o1,
        curv_o1,
        laps_steer_o2,
        steer_o2,
        laps_curv_o2,
        curv_o2,
    )

    # Display all comparison figures simultaneously
    plt.show()


if __name__ == "__main__":
    main()