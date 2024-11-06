'''
This demo file runs all the function on the original dataset to generate positioning metrics.
It can take a long time as it only generates one final output file. 
To test the functions and generate intermediate output files, run the files l demo1-5 in that order. 

'''

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
import _preprocessing as preprocessing
import _stopsAndTransitions as stopsAndTransitions
import _entropy as entropy
import _metricsMain as main
import _classroomObjects as classroomObjects

#LOAD PARAMETERS
config = configparser.ConfigParser()
config.read('../info.ini')

currentDT = datetime.datetime.now()
folderName = currentDT.strftime("%Y-%m-%d_%H:%M:%S")
folderName

#LOAD DATASET

#Load LOCALISATION DATASET
df=util.open_csv("Merged dataset 2018-2019/demo_dataset_2019.csv", ['timestamp'])
#Load PHASES 
dfPhases=util.open_csv("Merged dataset 2018-2019/demo_phases_2019.csv", ['start', 'end'])
#Load fixed points (OBJECTS and STUDENTS/GROUPS OF STDUENTS)
dfFixedPoints=util.open_csv("Merged dataset 2018-2019/demo_fixed_points_2019.csv", ['time_start'])



'''PREPROCESSING'''
df_preprocessed=preprocessing.preprocessing(df,dfPhases,1,0)

'''STOPS AND TRANSITIONS'''
df_stops_transitions=stopsAndTransitions.stops_transitions(df_preprocessed)

'''FIXED POINTS STATS'''
fixed_points_stats=classroomObjects.generate_fixed_points_stats(df_stops_transitions,dfFixedPoints)

'''INDEX OF DISPERSION'''
##GINI index per tracker
gini_output_separate_trackers=classroomObjects.calculate_gini_by_tracker(fixed_points_stats)

##GINI index all trackers together
gini_output_joint_trackers=classroomObjects.calculate_gini_trackers_together(fixed_points_stats)

'''ENTROPY'''
#Calculate entropy by tracker and phase
entropy_output=entropy.calculate_entropy_session_tracker_phase(df)

#Generate charts that can be associated to entropy (Voronoi, ConvexHull and Delaunay)
entropy.plot_charts_per_tracker(df_stops_transitions)

'''GET METRICS'''
###GENERATE THE METRICS
selectedPhase=-99 #if results from all the phases are to be included set to -99, otherwise, indicate the particular phase of interest (e.g. 1, 2, 3...)

Output=main.get_metrics(df_stops_transitions,fixed_points_stats,entropy_output,gini_output_separate_trackers
	,gini_output_joint_trackers,dfPhases,selectedPhase)

weighted= int(config.get('parameters','weighted'))
if(weighted==1):
    file = time.strftime('Output_NOTEBOOK10_metrics_per_tracker_WEIGHTED_%Y-%m-%d-%H-%M.csv')
else:
    file = time.strftime('Output_NOTEBOOK10_metrics_per_tracker_%Y-%m-%d-%H-%M.csv')
Output.to_csv(file)

print ("DONE")

