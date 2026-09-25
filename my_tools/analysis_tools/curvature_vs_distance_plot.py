import os
import tkinter as tk
from tkinter import filedialog
import matplotlib.pyplot as plt
import numpy as np

from my_tools.data_processing.signal_utils import motec_smooth
from my_tools.data_processing.telemetry_loader import load_acc_telemetry

DATA_FOLDER_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../telemetry_data")
)


def select_telemetry_file():
    """Opens a file dialog to select a single MoTeC telemetry file."""
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    file_path = filedialog.askopenfilename(
        initialdir=DATA_FOLDER_PATH,
        title="Select MoTeC Telemetry File for Curvature & Steering Test",
        filetypes=[("MoTeC Log Files", "*.ld"), ("All Files", "*.*")],
    )

    root.destroy()
    return file_path


def find_channel_col(df, aliases, default_name=None):
    """Case-insensitive search for channel aliases in DataFrame columns."""
    for col in df.columns:
        if col.lower() in [a.lower() for a in aliases]:
            return col
    return default_name


# --- STEP 1: SELECT TELEMETRY FILE ---
file_path = select_telemetry_file()
if not file_path:
    print("No file selected. Exiting script.")
    exit()

filename = os.path.basename(file_path)
print(f"\n--- Loading and Analyzing: {filename} ---")

# --- STEP 2: LOAD TELEMETRY & EXTRACT CHANNELS ---
df = load_acc_telemetry(file_path)

steer_aliases = ["steering", "steer", "steerangle", "steering angle", "steer_angle", "steering_angle"]
g_lat_aliases = ["g_lat", "lat_g", "acc_lat", "g_lateral", "lateral_acc", "lat g", "g lat"]
speed_aliases = ["speed", "v", "vehicle_speed", "car_speed"]

steer_col = find_channel_col(df, steer_aliases)
g_lat_col = find_channel_col(df, g_lat_aliases)
speed_col = find_channel_col(df, speed_aliases, default_name="Speed")

if not steer_col or not g_lat_col:
    print(f"\n[Error] Missing required channels in {filename}.")
    exit()

# Extract full-length primary distance baseline
speed = df[speed_col].dropna().values
speed_dist = df["Speed_Distance"].dropna().values if "Speed_Distance" in df else np.arange(len(speed))
speed_time = df["Speed_Time"].dropna().values if "Speed_Time" in df else np.linspace(0, 100, len(speed))

speed_kmh = speed * 3.6 if np.max(speed) < 150.0 else speed
v_ms = speed if np.max(speed) < 150.0 else speed / 3.6


# --- RESAMPLING FUNCTION TO PREVENT EARLY CUTOFF ---
def resample_to_lap_distance(channel_name):
    """
    Safely resamples a channel onto the primary `speed_dist` vector across the full lap.
    """
    if channel_name not in df:
        return np.zeros_like(speed_dist)

    s_data = df[channel_name].dropna().values

    # Try using dedicated channel time/distance if exported by loader
    time_col = f"{channel_name}_Time"
    dist_col = f"{channel_name}_Distance"

    if dist_col in df:
        s_dist = df[dist_col].dropna().values
    elif time_col in df:
        s_time = df[time_col].dropna().values
        s_dist = np.interp(s_time, speed_time, speed_dist)
    else:
        # Fallback: stretch across full lap distance linearly
        s_dist = np.linspace(speed_dist[0], speed_dist[-1], len(s_data))

    return np.interp(speed_dist, s_dist, s_data)


# Extract and align channels across entire lap length
steer_aligned = resample_to_lap_distance(steer_col)
g_lat_aligned = resample_to_lap_distance(g_lat_col)
throttle_aligned = resample_to_lap_distance("Throttle")
brake_aligned = resample_to_lap_distance("Brake")

steer_smoothed = motec_smooth(steer_aligned, num_samples=9)

# --- CURVATURE CALCULATION (r = |G_lat| / V^2) ---
is_in_g_units = np.max(np.abs(g_lat_aligned)) < 5.0
g_ms2 = np.abs(g_lat_aligned) * 9.81 if is_in_g_units else np.abs(g_lat_aligned)
abs_g_units = np.abs(g_lat_aligned) if is_in_g_units else np.abs(g_lat_aligned) / 9.81

cornering_mask = (abs_g_units >= 0.2) & (speed_kmh >= 30.0)
curvature = np.zeros_like(speed_dist)
curvature[cornering_mask] = g_ms2[cornering_mask] / (v_ms[cornering_mask] ** 2)

# --- STEP 3: RENDER 5 STACKED SUBPLOTS ---
fig, (ax1, ax2, ax3, ax4, ax5) = plt.subplots(
    5,
    1,
    figsize=(14, 10),
    sharex=True,
    gridspec_kw={"height_ratios": [1.2, 1.5, 1.2, 1, 1]},
)

# Plot 1: Speed
ax1.plot(speed_dist, speed_kmh, color="#1f77b4", linewidth=1.5, label="Speed")
ax1.set_ylabel("Speed\n(km/h)", fontsize=10, fontweight="bold")
ax1.set_title(f"Curvature & Steering Location Analysis — {filename}", fontsize=12, pad=12)
ax1.grid(True, linestyle="--", alpha=0.6)
ax1.legend(loc="upper right")

# Plot 2: Trajectory Curvature (Spans entire 0-6000m)
ax2.plot(speed_dist, curvature, color="#d62728", linewidth=1.5, label="Curvature r (|G_lat| / V²)")
ax2.set_ylabel("Curvature r\n(1/m)", fontsize=10, fontweight="bold")
ax2.set_ylim(bottom=0, top=max(curvature) * 1.15 if np.max(curvature) > 0 else 0.05)
ax2.grid(True, linestyle="--", alpha=0.6)
ax2.legend(loc="upper right")

# Plot 3: Steering Angle
ax3.plot(speed_dist, steer_smoothed, color="#7f7f7f", linewidth=1.5, label=f"Steering Angle ({steer_col})")
ax3.set_ylabel("Steering\n(deg)", fontsize=10, fontweight="bold")
ax3.grid(True, linestyle="--", alpha=0.6)
ax3.legend(loc="upper right")

# Plot 4: Throttle
ax4.plot(speed_dist, throttle_aligned, color="#2ca02c", linewidth=1.5, label="Throttle")
ax4.set_ylabel("Throttle\n(%)", fontsize=10, fontweight="bold")
ax4.set_ylim(-5, 105)
ax4.grid(True, linestyle="--", alpha=0.6)
ax4.legend(loc="upper right")

# Plot 5: Brake
ax5.plot(speed_dist, brake_aligned, color="#ff7f0e", linewidth=1.5, label="Brake")
ax5.set_ylabel("Brake\n(%)", fontsize=10, fontweight="bold")
ax5.set_xlabel("Lap Distance (m)", fontsize=11, fontweight="bold")
ax5.set_ylim(-5, 105)
ax5.grid(True, linestyle="--", alpha=0.6)
ax5.legend(loc="upper right")

plt.tight_layout()
fig.canvas.manager.set_window_title("Curvature & Steering Location Test")
plt.show()