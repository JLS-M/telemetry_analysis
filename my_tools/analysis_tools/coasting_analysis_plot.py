import os
import tkinter as tk
from tkinter import filedialog
import matplotlib.pyplot as plt

# Import telemetry processor
from my_tools.data_processing.telemetry_processor import process_outing_throttle

DATA_FOLDER_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../telemetry_data")
)

SMOOTH_SAMPLES = 9
THROTTLE_THRESHOLD = 95.0


def get_outing_files(outing_name):
    """Opens a file dialog to select files for a specific outing."""
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    file_paths = filedialog.askopenfilenames(
        initialdir=DATA_FOLDER_PATH,
        title=f"Select {outing_name} - MoTeC Telemetry Files (Hold Ctrl/Cmd for multiple)",
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

# --- STEP 2: PROCESS TELEMETRY DATA VIA PROCESSOR ---
# Speed threshold is managed directly inside telemetry_processor.py
data_outing1 = process_outing_throttle(
    outing1_files,
    "Outing 1",
    smooth_samples=SMOOTH_SAMPLES,
    full_throttle_threshold=THROTTLE_THRESHOLD,
)
data_outing2 = process_outing_throttle(
    outing2_files,
    "Outing 2",
    smooth_samples=SMOOTH_SAMPLES,
    full_throttle_threshold=THROTTLE_THRESHOLD,
)

if data_outing1 is None or data_outing2 is None:
    print("\nFailed to process data for both outings. Exiting script.")
    exit()

# --- STEP 3: RENDER SINGLE SCATTER PLOT ---
colors = {"Outing 1": "#1f77b4", "Outing 2": "#ff7f0e"}
outings_data = [("Outing 1", data_outing1), ("Outing 2", data_outing2)]

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
        color=colors[name],
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
    fontweight="bold",
    pad=15,
)
ax.set_xlabel("Lap Number", fontsize=11, fontweight="bold")
ax.set_ylabel("Total Pre-Braking Coasting Time (s)", fontsize=11, fontweight="bold")

# Fixed Y-axis scale from 0 to 8 seconds
ax.set_ylim(0, 8)

ax.set_xticks(range(min_lap, max_lap + 1))
ax.grid(True, linestyle="--", alpha=0.6)
ax.legend(loc="best", fontsize=10)

plt.tight_layout()
fig.canvas.manager.set_window_title("Coasting Analysis - Outing Comparison")
plt.show()