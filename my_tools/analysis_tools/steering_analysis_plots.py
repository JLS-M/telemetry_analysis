import os
import tkinter as tk
from tkinter import filedialog
import matplotlib.pyplot as plt

from my_tools.data_processing.telemetry_processor import (
    process_outing_steering_speed,
    process_outing_trajectory_curvature,
)

DATA_FOLDER_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../telemetry_data")
)


def get_outing_files(outing_name):
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    file_paths = filedialog.askopenfilenames(
        initialdir=DATA_FOLDER_PATH,
        title=f"Select {outing_name} - MoTeC Telemetry Files",
        filetypes=[("MoTeC Log Files", "*.ld"), ("All Files", "*.*")],
    )

    root.destroy()
    return list(file_paths)


# --- STEP 1: SELECT FILES FOR BOTH OUTINGS ---
outing1_files = get_outing_files("Outing 1")
if not outing1_files:
    print("\nNo files selected for Outing 1. Exiting script.")
    exit()

outing2_files = get_outing_files("Outing 2")
if not outing2_files:
    print("\nNo files selected for Outing 2. Exiting script.")
    exit()

# --- STEP 2: PROCESS STEERING SPEED & CURVATURE DATA ---
MIN_STEER_THRESHOLD = 10.0  # deg/s

# 1. Steering Speed
laps_steer_o1, steer_speed_o1 = process_outing_steering_speed(
    outing1_files, min_steering_rate=MIN_STEER_THRESHOLD, smooth_samples=9
)
laps_steer_o2, steer_speed_o2 = process_outing_steering_speed(
    outing2_files, min_steering_rate=MIN_STEER_THRESHOLD, smooth_samples=9
)

# 2. Trajectory Curvature (r = |G_lat| / V^2)
laps_curv_o1, curvature_o1 = process_outing_trajectory_curvature(
    outing1_files, min_lat_acc_g=0.2, min_speed_kmh=30.0
)
laps_curv_o2, curvature_o2 = process_outing_trajectory_curvature(
    outing2_files, min_lat_acc_g=0.2, min_speed_kmh=30.0
)

# Sort steering speed data sequentially
if laps_steer_o1:
    laps_steer_o1, steer_speed_o1 = zip(
        *sorted(zip(laps_steer_o1, steer_speed_o1))
    )
if laps_steer_o2:
    laps_steer_o2, steer_speed_o2 = zip(
        *sorted(zip(laps_steer_o2, steer_speed_o2))
    )

# Sort curvature data sequentially
if laps_curv_o1:
    laps_curv_o1, curvature_o1 = zip(*sorted(zip(laps_curv_o1, curvature_o1)))
if laps_curv_o2:
    laps_curv_o2, curvature_o2 = zip(*sorted(zip(laps_curv_o2, curvature_o2)))

# --- STEP 3: RENDER PLOTS SIDE BY SIDE ---
colors = {"Outing 1": "#1f77b4", "Outing 2": "#ff7f0e"}

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

# --- SUBPLOT 1: STEERING SPEED ---
if laps_steer_o1:
    ax1.scatter(
        laps_steer_o1,
        steer_speed_o1,
        color=colors["Outing 1"],
        label="Outing 1",
        s=60,
        alpha=0.85,
        edgecolor="k",
        linewidth=0.8,
    )

if laps_steer_o2:
    ax1.scatter(
        laps_steer_o2,
        steer_speed_o2,
        color=colors["Outing 2"],
        label="Outing 2",
        s=60,
        alpha=0.85,
        edgecolor="k",
        linewidth=0.8,
    )

ax1.set_title(
    f"Average Absolute Steering Speed per Lap (≥{MIN_STEER_THRESHOLD:.0f} deg/s)",
    fontsize=12,
    fontweight="bold",
    pad=12,
)
ax1.set_xlabel("Lap Number", fontsize=11, fontweight="bold")
ax1.set_ylabel("Steering Speed (deg/s)", fontsize=11, fontweight="bold")
ax1.set_ylim(bottom=20, top=70)
ax1.grid(True, linestyle="--", alpha=0.6)
ax1.legend(loc="best", fontsize=10)

# --- SUBPLOT 2: TRAJECTORY CURVATURE ---
if laps_curv_o1:
    ax2.scatter(
        laps_curv_o1,
        curvature_o1,
        color=colors["Outing 1"],
        label="Outing 1",
        s=60,
        alpha=0.85,
        edgecolor="k",
        linewidth=0.8,
    )

if laps_curv_o2:
    ax2.scatter(
        laps_curv_o2,
        curvature_o2,
        color=colors["Outing 2"],
        label="Outing 2",
        s=60,
        alpha=0.85,
        edgecolor="k",
        linewidth=0.8,
    )

ax2.set_title(
    "Average Trajectory Curvature per Lap (r = |G_lat| / V²)",
    fontsize=12,
    fontweight="bold",
    pad=12,
)
ax2.set_xlabel("Lap Number", fontsize=11, fontweight="bold")
ax2.set_ylabel("Curvature r (1/m)", fontsize=11, fontweight="bold")

# Dynamic Y-axis framing with safety margin for curvature
if curvature_o1 or curvature_o2:
    all_curv = list(curvature_o1 or ()) + list(curvature_o2 or ())
    ax2.set_ylim(bottom=min(all_curv) * 0.7, top=max(all_curv) * 1.3)
else:
    ax2.set_ylim(bottom=0.002, top=0.05)

ax2.grid(True, linestyle="--", alpha=0.6)
ax2.legend(loc="best", fontsize=10)

# Format X-axis discrete integer lap ticks across both subplots
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
plt.show()