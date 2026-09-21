import numpy as np
import pandas as pd
from external_tools.ldparser import ldData

def load_acc_telemetry(ld_file_path):
    """Loads a MoTeC .ld binary file using ldparser and extracts channels into a pandas DataFrame."""
    # 1. Safety check to parse the MoTeC binary file
    try:
        ld = ldData.fromfile(ld_file_path)
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Could not find the file at: '{ld_file_path}'. "
            "Double-check your file path inside the 'telemetry_data/' folder!"
        )
    except Exception as e:
        raise RuntimeError(f"Error parsing MoTeC binary file: {e}")

    # 2. Map desired clean DataFrame column names to MoTeC channel names.
    # If I change from ACC to another simulator I just need to change the right hand side of this dictionary.
    # Syntax:  { Key: DataFrame column : Value: MoTeC name}
    channel_map = {
        'Speed': 'SPEED',
        'Throttle': 'THROTTLE',
        'Brake': 'BRAKE',
        'Steer_Angle': 'STEERANGLE',
        'Gear': 'GEAR',
        'rpm': 'RPMS',
        'g_lat': 'G_LAT',
        'g_lon': 'G_LON',
    }

    # 3. Extract each channel and its exact time vector
    channel_data = {}
    for clean_name, motec_name in channel_map.items():
        try:
            ch = ld[motec_name]
            if ch is not None and len(ch.data) > 0:
                # Check explicitly if freq exists and is valid
                if hasattr(ch, "freq") and ch.freq is not None and ch.freq > 0:
                    channel_data[clean_name] = ch.data
                    channel_data[f"{clean_name}_Time"] = (
                            np.arange(len(ch.data)) / ch.freq
                    )
                else:
                    print(
                        f"Error: Channel '{motec_name}' ({clean_name}) is missing a valid 'freq' attribute."
                    )
        except Exception:
            print(f"Warning: Channel '{motec_name}' not found in telemetry file.")

    if not channel_data:
        raise ValueError("No valid channels were extracted from this file.")

    # 3.5 Calculate Cumulative Distance from Speed & Speed_Time
    if "Speed" in channel_data and "Speed_Time" in channel_data:
        speed_vals = channel_data["Speed"]  # m/s
        speed_times = channel_data["Speed_Time"]

        # Time step deltas
        dt = np.diff(speed_times, prepend=speed_times[0])

        # Integrate speed over time to get lap distance (meters)
        calc_dist = np.cumsum(speed_vals * dt)

        # Store Speed's distance array directly
        channel_data["Speed_Distance"] = calc_dist

        # Build 2-column Lookup Matrix [Time, Distance] for other channels
        time_dist_matrix = np.column_stack((speed_times, calc_dist))
        channel_data["Time_Distance_Matrix"] = [time_dist_matrix]

    # 4. Return as a single DataFrame (using max length padding with NaN [adds NaN
    # to the shorter arrays to complete their length])
    # This preserves EVERY raw value cleanly without modifying or interpolating any data
    df = pd.DataFrame(
        # Converts the raw NumPy array v into a Pandas Series object, which then allows for length padding with NaN
        dict([(k, pd.Series(v)) for k, v in channel_data.items()])
    )

    return df