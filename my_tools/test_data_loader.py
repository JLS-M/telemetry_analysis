import pandas as pd
import matplotlib.pyplot as plt
from my_tools.data_loader import load_acc_telemetry

# --- TELL PANDAS TO NEVER TRUNCATE COLUMNS ---
pd.set_option("display.max_columns", None)
pd.set_option("display.width", 1000)
# --------------------------------------------

# Use '../' to step out of 'my_tools' and into the main project directory
file_path = "../telemetry_data/test_2_Silverstone-ford_mustang_gt3-25-2026.07.19-13.23.25.ld"

print("\nLoading telemetry data...")
df = load_acc_telemetry(file_path)

print("\n--- Telemetry Loaded Successfully! ---")
print("Data Shape (Rows, Columns):", df.shape)
print("\nFirst 5 rows:")
print(df.head())

# --- SPEED VS TIME PLOT ---
plt.figure(figsize=(12, 5))

# Drop NaN rows caused by length padding for plotting
speed_data = df[["Speed_Time", "Speed"]].dropna()

plt.plot(
    speed_data["Speed_Time"],
    speed_data["Speed"] * 3.6,
    color="#1f77b4",
    linewidth=1.5,
)
plt.title("Speed vs Time - Silverstone Mustang GT3")
plt.xlabel("Lap Time (s)")
plt.ylabel("Speed (km/h)")
plt.grid(True, linestyle="--", alpha=0.6)
plt.tight_layout()
plt.show()