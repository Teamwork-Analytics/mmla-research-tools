import sys
sys.path.insert(0, '../scripts')

import configparser
import numpy as np 
import pandas as pd 
import csv
import math
import time
import datetime
import _util as util
import _metricsMain as main

#load parameters
config = configparser.ConfigParser()
config.read('../info.ini')

currentDT = datetime.datetime.now()
folderName = currentDT.strftime("%Y-%m-%d_%H:%M:%S")
folderName

#LOAD DATASET
###Load phases dataset
df_phases=util.open_csv("Merged dataset 2018-2019/demo_phases_2019.csv", ['start','end'])


#LOAD OUTPUT FILES FROM PREVIOUS demo# files
###Load stops and transitions
df_fs=util.open_csv("sample_output_files/Output_NOTEBOOK3_classroom_data2_stop_transitions_2020-08-11-15-49.csv", ['timestamp'])

###Load metrics related to fixed positions (students and zones/objects in the classroom)
df_points=util.open_csv("sample_output_files/Output_NOTEBOOK9_fixed_trackers_stats_2020-08-13-10-59.csv", [])

###Load entropy metrics
df_entropy=util.open_csv("sample_output_files/Output_NOTEBOOK7_entropy_BY_PHASE_grouping_gridsize_1000.0mm_2020-08-11-17-39.csv", [])

###Load dispersion metrics
df_giniT=util.open_csv("sample_output_files/Output_NOTEBOOK9_gini_grouping_by_tracker_2020-08-13-16-00.csv", [])
df_giniSession=util.open_csv("sample_output_files/Output_NOTEBOOK9_gini_grouping_by_session_2020-08-13-16-00.csv", [])

###Parameters to generate the metrics
selectedPhase=-99 #if results from all the phases are to be included set to -99, otherwise, indicate the particular phase of interest (e.g. 1, 2, 3...)
weighted=1 #if weighted is set to 1, all the metrics are normalised with reference to the shortest duration of each phase. Set to 0 to get the metrics for each session/phase of variable durations.


###GENERATE THE METRICS
Output=main.get_metrics(df_fs,df_points,df_entropy,df_giniT,df_giniSession,df_phases,selectedPhase)

if(weighted==1):
    file = time.strftime('Output_NOTEBOOK10_metrics_per_tracker_WEIGHTED_%Y-%m-%d-%H-%M.csv')
else:
    file = time.strftime('Output_NOTEBOOK10_metrics_per_tracker_%Y-%m-%d-%H-%M.csv')
Output.to_csv(file)

print ("DONE")
