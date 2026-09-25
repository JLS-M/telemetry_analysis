import matplotlib.pyplot as plt

# Import comparative analysis runners
from brake_analysis_plots import run_brake_analysis
from coasting_analysis_plot import run_coasting_analysis
from my_tools.data_processing.signal_utils import get_outing_files
from steering_analysis_plots import run_steering_analysis
from throttle_analysis_plots import run_throttle_analysis


def main():
    print("==================================================")
    print("      OUTING COMPARATIVE TELEMETRY ANALYSIS       ")
    print("==================================================")

    # 1. Prompt for files ONCE per outing
    outing1_files = get_outing_files("Outing 1")
    if not outing1_files:
        print("\nNo files selected for Outing 1. Exiting.")
        return

    outing2_files = get_outing_files("Outing 2")
    if not outing2_files:
        print("\nNo files selected for Outing 2. Exiting.")
        return

    # 2. Execute comparative analysis runners sequentially
    print("\n[1/4] Running Throttle Analysis...")
    run_throttle_analysis(outing1_files, outing2_files)

    print("[2/4] Running Coasting Analysis...")
    run_coasting_analysis(outing1_files, outing2_files)

    print("[3/4] Running Brake Dynamics Analysis...")
    run_brake_analysis(outing1_files, outing2_files)

    print("[4/4] Running Steering & Curvature Analysis...")
    run_steering_analysis(outing1_files, outing2_files)

    # 3. Render all open comparative figures simultaneously
    plt.show()


if __name__ == "__main__":
    main()