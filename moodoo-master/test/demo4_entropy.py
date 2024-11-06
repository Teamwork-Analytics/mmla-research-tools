import sys
sys.path.insert(0, '../scripts')

import numpy as np 
import pandas as pd 
import time
import csv
import datetime
import _util as util
#import _preprocessing as preprocessing
import _entropy as entropy

import configparser
#load parameters
config = configparser.ConfigParser()
config.read('../info.ini')

currentDT = datetime.datetime.now()
folderName = currentDT.strftime("%Y-%m-%d_%H:%M:%S")
folderName

###CALCULATE ENTROPY
#Load preprocessed dataset
df=util.open_csv("sample_output_files/PartialDatasets_NOTEBOOK1_classroom_data_V2_2020-08-11-09-56.csv", ['timestamp'])


print ("Calculate entropy by session and tracker and phase")
#Calculate entropy by session and tracker
df3=entropy.calculate_entropy_session_tracker_phase(df)

#Get the size of the cell to include in the file name
size_of_grid_cells= float(config.get('parameters','size_of_grid_cells'))

print ("Saving files")
filename = time.strftime('Output_NOTEBOOK7_entropy_BY_PHASE_grouping_gridsize_'+str(size_of_grid_cells)+'mm_%Y-%m-%d-%H-%M.csv')
df3.to_csv(filename, date_format="%d/%m/%Y %H:%M:%S")

###GENERATE CHARTS FROM STOPS AND TRANSITIONS
print ("Generating charts - VORONOI, ConvexHull and Delaunay")
#Load stops and transitions
df_st=util.open_csv("sample_output_files/Output_NOTEBOOK3_classroom_data2_stop_transitions_2020-08-11-15-49.csv", ['timestamp'])
print (df_st)
entropy.plot_charts(df_st)


print ("DONE")

