import os
import tkinter as tk
from tkinter import filedialog
import matplotlib.pyplot as plt

from my_tools.data_processing.telemetry_processor import (
    process_outing_brake_release_speed,
    process_outing_brake_speed,
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

# --- STEP 2: PROCESS APPLICATION & RELEASE SPEED DATA ---
# 1. Brake Application Speed (>= 80%/s)
laps_app_o1, brake_app_speed_o1 = process_outing_brake_speed(
    outing1_files, min_brake_rate=80.0, smooth_samples=9
)
laps_app_o2, brake_app_speed_o2 = process_outing_brake_speed(
    outing2_files, min_brake_rate=80.0, smooth_samples=9
)

# 2. Brake Release Speed (Release rate >= 10%/s)
laps_rel_o1, brake_rel_speed_o1 = process_outing_brake_release_speed(
    outing1_files, min_release_rate=10.0, smooth_samples=9
)
laps_rel_o2, brake_rel_speed_o2 = process_outing_brake_release_speed(
    outing2_files, min_release_rate=10.0, smooth_samples=9
)

# Sort application data sequentially
if laps_app_o1:
    laps_app_o1, brake_app_speed_o1 = zip(
        *sorted(zip(laps_app_o1, brake_app_speed_o1))
    )
if laps_app_o2:
    laps_app_o2, brake_app_speed_o2 = zip(
        *sorted(zip(laps_app_o2, brake_app_speed_o2))
    )

# Sort release data sequentially
if laps_rel_o1:
    laps_rel_o1, brake_rel_speed_o1 = zip(
        *sorted(zip(laps_rel_o1, brake_rel_speed_o1))
    )
if laps_rel_o2:
    laps_rel_o2, brake_rel_speed_o2 = zip(
        *sorted(zip(laps_rel_o2, brake_rel_speed_o2))
    )

# --- STEP 3: RENDER PLOTS SIDE BY SIDE ---
colors = {"Outing 1": "#1f77b4", "Outing 2": "#ff7f0e"}

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

# --- SUBPLOT 1: APPLICATION SPEED ---
if laps_app_o1:
    ax1.scatter(
        laps_app_o1,
        brake_app_speed_o1,
        color=colors["Outing 1"],
        label="Outing 1",
        s=60,
        alpha=0.85,
        edgecolor="k",
        linewidth=0.8,
    )

if laps_app_o2:
    ax1.scatter(
        laps_app_o2,
        brake_app_speed_o2,
        color=colors["Outing 2"],
        label="Outing 2",
        s=60,
        alpha=0.85,
        edgecolor="k",
        linewidth=0.8,
    )

ax1.set_title(
    "Average Brake Application Speed per Lap (>80%/s)",
    fontsize=12,
    fontweight="bold",
    pad=12,
)
ax1.set_xlabel("Lap Number", fontsize=11, fontweight="bold")
ax1.set_ylabel(
    "Application Speed (%/s)", fontsize=11, fontweight="bold"
)
ax1.set_ylim(bottom=80, top=220)
ax1.grid(True, linestyle="--", alpha=0.6)
ax1.legend(loc="best", fontsize=10)

# --- SUBPLOT 2: RELEASE SPEED (SMOOTHNESS) ---
if laps_rel_o1:
    ax2.scatter(
        laps_rel_o1,
        brake_rel_speed_o1,
        color=colors["Outing 1"],
        label="Outing 1",
        s=60,
        alpha=0.85,
        edgecolor="k",
        linewidth=0.8,
    )

if laps_rel_o2:
    ax2.scatter(
        laps_rel_o2,
        brake_rel_speed_o2,
        color=colors["Outing 2"],
        label="Outing 2",
        s=60,
        alpha=0.85,
        edgecolor="k",
        linewidth=0.8,
    )

ax2.set_title(
    "Average Brake Release Speed per Lap (<10%/s)",
    fontsize=12,
    fontweight="bold",
    pad=12,
)
ax2.set_xlabel("Lap Number", fontsize=11, fontweight="bold")
ax2.set_ylabel("Release Speed (%/s)", fontsize=11, fontweight="bold")

# Dynamic Y-axis framing with safety margin
if brake_rel_speed_o1 or brake_rel_speed_o2:
    all_rel = list(brake_rel_speed_o1 or []) + list(
        brake_rel_speed_o2 or []
    )
    ax2.set_ylim(bottom=0, top=max(all_rel) * 1.15)
else:
    ax2.set_ylim(bottom=0, top=200)

ax2.grid(True, linestyle="--", alpha=0.6)
ax2.legend(loc="best", fontsize=10)

# Format X-axis for discrete lap integers across both subplots
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
plt.show()