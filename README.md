This is a tool capable of reading MoTeC data.
Currently it is being used to compare two sets of files, with each file corresponding to lap data exported from MoTeC (.ld).
Each lap file name must end with Lap.10.ld (10 being the corresponding lap number).
When running outing_comparative_analysis, two consecutive windows file selection screens will prompt you to select the files corresponding to each outing.
This script will then run all the analysis_plot scripts, yielding a set of graphs that compare several aspects of the driver technique for each outing.
The "vs_plot" scripts are fed with a single lap file, and they yield a speed trace followed by throttle, steering and brake traces, and a specific trace indicated in the name of the script.
This is a work in progress.
