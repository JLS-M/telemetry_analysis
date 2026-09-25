import os
import tkinter as tk
from tkinter import filedialog
import matplotlib.pyplot as plt

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

# --- STEP 2: PROCESS TELEMETRY DATA VIA PROCESSOR ---
# Telemetry processor now automatically sorts laps sequentially by lap_num internally
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
    print("\nFailed to calculate valid averages for both outings.")
    exit()

# --- STEP 3: RENDER PLOTS (3-PANEL LAYOUT) ---
colors = {"Outing 1": "#1f77b4", "Outing 2": "#ff7f0e"}
fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(16, 5))

outings_data = [("Outing 1", data_outing1), ("Outing 2", data_outing2)]
all_lap_nums = []
for name, data in outings_data:
    all_lap_nums.extend([item["lap_num"] for item in data["laps"]])

min_lap = min(all_lap_nums) if all_lap_nums else 1
max_lap = max(all_lap_nums) if all_lap_nums else 1

# --- PLOT 1: AVERAGE BAR CHART ---
labels = ["Outing 1", "Outing 2"]
averages = [data_outing1["avg_pct"], data_outing2["avg_pct"]]
x_positions = [0, 1]
bar_width = 1.0

bars = ax1.bar(
    x_positions,
    averages,
    color=[colors["Outing 1"], colors["Outing 2"]],
    width=bar_width,
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
        fontweight="bold",
        fontsize=11,
    )

ax1.set_xticks(x_positions)
ax1.set_xticklabels(labels, fontsize=11, fontweight="bold")
ax1.set_title(
    f"Average Full Throttle (>= {THROTTLE_THRESHOLD:.0f}%)\nOuting 1 vs. Outing 2",
    fontsize=11,
    pad=15,
)
ax1.set_ylabel("Full Throttle Percentage (%)", fontsize=10)
ax1.set_ylim(0, 100)
ax1.set_xlim(-0.6, 1.6)
ax1.grid(axis="y", linestyle="--", alpha=0.6)

# --- PLOT 2: PER-LAP FULL THROTTLE % SCATTER ---
for name, data in outings_data:
    x_laps = [item["lap_num"] for item in data["laps"]]
    y_pcts = [item["pct"] for item in data["laps"]]

    ax2.scatter(
        x_laps,
        y_pcts,
        color=colors[name],
        label=name,
        s=70,
        alpha=0.85,
        edgecolor="black",
        linewidth=0.8,
        zorder=3,
    )

ax2.set_title("Full Throttle % per Lap\nby Lap Number", fontsize=11, pad=15)
ax2.set_xlabel("Lap Number", fontsize=10)
ax2.set_ylabel("Full Throttle Percentage (%)", fontsize=10)
ax2.set_ylim(0, 80)
ax2.set_xticks(range(min_lap, max_lap + 1))
ax2.grid(True, linestyle="--", alpha=0.6)
ax2.legend(loc="best")

# --- PLOT 3: PER-LAP THROTTLE APPLICATION SPEED SCATTER ---
for name, data in outings_data:
    x_laps = [item["lap_num"] for item in data["laps"]]
    y_speeds = [item["avg_throttle_speed"] for item in data["laps"]]

    ax3.scatter(
        x_laps,
        y_speeds,
        color=colors[name],
        label=name,
        s=70,
        alpha=0.85,
        edgecolor="black",
        linewidth=0.8,
        zorder=3,
    )

ax3.set_title(
    f"Avg Throttle Speed per Lap (MoTeC Smooth {SMOOTH_SAMPLES}smp)\nby Lap Number",
    fontsize=11,
    pad=15,
)
ax3.set_xlabel("Lap Number", fontsize=10)
ax3.set_ylabel("Throttle Speed (% / s)", fontsize=10)
ax3.set_ylim(20, 90)
ax3.set_xticks(range(min_lap, max_lap + 1))
ax3.grid(True, linestyle="--", alpha=0.6)
ax3.legend(loc="best")

plt.tight_layout()
fig.canvas.manager.set_window_title("Throttle Analysis")
plt.show()