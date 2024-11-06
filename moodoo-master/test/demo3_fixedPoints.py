import sys
sys.path.insert(0, '../scripts')

import numpy as np 
import pandas as pd 
import time
import csv
import datetime
import _util as util
#import _preprocessing as preprocessing
import _classroomObjects as classroomObjects

currentDT = datetime.datetime.now()
folderName = currentDT.strftime("%Y-%m-%d_%H:%M:%S")
folderName


#Load stops and transitions
df_stops=util.open_csv("sample_output_files/Output_NOTEBOOK3_classroom_data2_stop_transitions_2020-08-11-15-49.csv", ['timestamp'])
print (df_stops)
#Load fixed points (OBJECTS and GROUPS)
df_fixed_points=util.open_csv("Merged dataset 2018-2019/demo_fixed_points_2019.csv", ['time_start'])
print (df_fixed_points)


#Generate Fixed points stats
fixed_points_stats=classroomObjects.generate_fixed_points_stats(df_stops,df_fixed_points)
filename = time.strftime('Output_NOTEBOOK9_fixed_points_stats_%Y-%m-%d-%H-%M.csv')
fixed_points_stats.to_csv(filename)

##Calculate GINI index per tracker
gini_output_separate_trackers=classroomObjects.calculate_gini_by_tracker(fixed_points_stats)
filename = time.strftime('Output_NOTEBOOK9_gini_grouping_by_tracker_%Y-%m-%d-%H-%M.csv')
gini_output_separate_trackers.to_csv(filename)

##Calculate GINI index all trackers together
gini_output_joint_trackers=classroomObjects.calculate_gini_trackers_together(fixed_points_stats)
filename = time.strftime('Output_NOTEBOOK9_gini_grouping_by_session_%Y-%m-%d-%H-%M.csv')
gini_output_joint_trackers.to_csv(filename)

print ("DONE")

