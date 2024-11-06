import sys
sys.path.insert(0, '../scripts')

import numpy as np 
import pandas as pd 
import time
import csv
import datetime
import _util as util
import _preprocessing as preprocessing
import _stopsAndTransitions as stopsAndTransitions

currentDT = datetime.datetime.now()
folderName = currentDT.strftime("%Y-%m-%d_%H:%M:%S")
folderName

'''GET METRICS STOPS AND TRANSITIONS'''
#Load PRE-PROCESSED DATASET
df_preprocessed=util.open_csv("sample_output_files/PartialDatasets_NOTEBOOK1_classroom_data_V2_2020-08-11-09-56.csv", ['timestamp'])
print (df_preprocessed)

df_stops_transitions=stopsAndTransitions.stops_transitions(df_preprocessed)

filename = time.strftime('Output_NOTEBOOK3_classroom_data2_stop_transitions_%Y-%m-%d-%H-%M.csv')
df_stops_transitions.to_csv(filename, date_format="%d/%m/%Y %H:%M:%S")

print ("DONE")

