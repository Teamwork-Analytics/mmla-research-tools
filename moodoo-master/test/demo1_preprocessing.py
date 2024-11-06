import sys
sys.path.insert(0, '../scripts')

import numpy as np 
import pandas as pd 
import time
import csv
import datetime
import _util as util
import _preprocessing as preprocessing

currentDT = datetime.datetime.now()
folderName = currentDT.strftime("%Y-%m-%d_%H:%M:%S")
folderName

#Load LOCALISATION DATASET
df=util.open_csv("Merged dataset 2018-2019/demo_dataset_2019.csv", ['timestamp'])

#Load PHASES 
dfPhases=util.open_csv("Merged dataset 2018-2019/demo_phases_2019.csv", ['start', 'end'])

'''PREPROCESSING'''
df2=preprocessing.preprocessing(df,dfPhases,1,0)

filename = time.strftime('PartialDatasets_NOTEBOOK1_classroom_data_V2_%Y-%m-%d-%H-%M.csv')
df2.to_csv(filename, date_format="%d/%m/%Y %H:%M:%S")



