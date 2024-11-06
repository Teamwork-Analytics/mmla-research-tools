"""Scripts to generate and merge ALL metrics 

This script allows the user to generate and merge all the metrics froom indoor localisation data


This script requires that `pandas` be installed within the Python
environment you are running this script in.

This file can also be imported as a module and contains the following functions:  
    * get_metrics (main function)- It extracts and merges all the metrics from the outputs of other scripts.
"""
import configparser
import numpy as np 
import pandas as pd 
#from sklearn import preprocessing
#from scipy.stats import entropy
#from scipy.spatial import Voronoi, voronoi_plot_2d
#import matplotlib.pyplot as plt
import csv
import math
import time
import datetime
import _util as util
#load parameters
config = configparser.ConfigParser()
config.read('../info.ini')



def get_metrics(df_fs,df_points,df_entropy,df_giniT,df_giniSession,df_phases,selectedPhase):
	"""This function generates a data frame that clusters data points according to their distance.  
		The parameter "distance" is read from the config file and it is used to create a new cluster 
		if the distance between two consecutive datapoints is higher than the parameter 'distance'
	
	Parameters
	----------
	df_fs : Pandas Data Frame
		Data frame of stops and transitions returning from _stopsAndTransitions.stops_transitions()
	df_points : Pandas Data Frame
		Data frame of fixed_points_stats returning from _stopsAndTransitions.generate_fixed_points_stats()
	df_entropy : Pandas Data Frame
		Data frame of entropy values returning from _entropy.calculate_entropy_session_tracker_phase()
	df_giniT : Pandas Data Frame
		Data frame of gini indices per tracker returning from _classroomObjects.calculate_gini_by_tracker()
	df_giniSession : Pandas Data Frame
		Data frame of gini indices for trackers together returning from _classroomObjects.calculate_gini_trackers_together()	
	
	df_phases : Pandas Data Frame
		a Data Frame with the following columns: 
			session : string
			phase : int
			start : datetime
			end  : datetime
			comment : string (optional, not used by this script)
		Phases have to be numbered starting from 1. Phase 0 will be ignored.
	
	selectedPhase : (int)
		if results from all the phases are to be included set to -99, otherwise, indicate the particular phase of interest (e.g. 1, 2, 3...)
	
	Returns
	-------
	Output
		returns a data frame with the following metrics columns (TBC):
			group - the cluster id (a self incremental intiger that starts from 1)
			base_dist - distance from a datapoint to the first datapoint in the cluster
			intra_dist - distance to the previous data point
			time_diff - time difference from the previous data point

	"""
	print ("Calculating metrics.")
	#ADD COLUMN STOP DURATIONS IN MINUTES
	durations= []
	for index, row in df_fs.iterrows():
		##Add derived column of duration in seconds
		dur_in_seconds=pd.to_timedelta(row['max_duration'])
		durations.append(dur_in_seconds.total_seconds()/60)
	df_fs['duration_minutes'] = durations
	#df_fs.head(5)


	############ Extract metrics related to STOPS ############
	df_stops=df_fs.loc[(df_fs['type'] == 'stop')].groupby(['session','tracker','phase']).agg(
	   Number_of_stops=pd.NamedAgg(column='duration_minutes', aggfunc='count'),
	   Stopping_time_mins=pd.NamedAgg(column='duration_minutes', aggfunc=sum),
	   Max_stop_mins=pd.NamedAgg(column='duration_minutes', aggfunc=max),
	   Avg_stopping_time=pd.NamedAgg(column='duration_minutes', aggfunc='mean'),
	   Median_stopping_time=pd.NamedAgg(column='duration_minutes', aggfunc='median'),
	   Std_stopping_time=pd.NamedAgg(column='duration_minutes', aggfunc='std')
	)



	############ Extract metrics related to TRANSITIONS ############

	#Add a column to calculate euclidean distance to the previous data point in a transition (to calculate distance walked and speed)
	df_fs.sort_values(by=['session','tracker','block'], inplace=True)
	distances= []
	speed=[] 
	prevRow=[]
	for index, row in df_fs.iterrows():
		if (len(prevRow)==0):
		#First row of the dataset
			prevRow=row
			distances.append(0)
		else:
			if ((prevRow['session']==row['session']) 
				& (prevRow['tracker']==row['tracker'])):
				#CALCULATE DISTANCE
				distances.append((np.sqrt((prevRow['x'] - row['x']) ** 2 + (prevRow['y'] - row['y']) ** 2))/1000)
				prevRow=row
			else:
				#It is a new session or tracker
				distances.append(0)
				prevRow=row
	df_fs['distance_previous_point_meter'] = distances

	#Extract metrics
	transitions=df_fs.loc[(df_fs['type'] == 'transition')].groupby(['session','tracker','phase','block']).agg(
	   Distance_walked=pd.NamedAgg(column='distance_previous_point_meter', aggfunc=sum),
	   Speed_meter_per_sec=pd.NamedAgg(column='distance_previous_point_meter', aggfunc='mean')
	)
	transitions.reset_index(inplace=True)

	df_transitions=transitions.groupby(['session','tracker','phase']).agg(
	   Number_of_transitions=pd.NamedAgg(column='block', aggfunc='count'),
	   Distance_walked=pd.NamedAgg(column='Distance_walked', aggfunc=sum),
	   Speed_meter_per_sec=pd.NamedAgg(column='Speed_meter_per_sec', aggfunc='mean')
	)


	############ Extract metrics related to fixed points (students and objects/zones)

	#Calculate derived auxiliar columns
	df_points.sort_values(by=['session','obj_type'], inplace=True)
	df_points['time_per_stop_min'] = df_points['sum']/df_points['count']/60
	df_points['total_attention_time_min'] = df_points['sum']/60

	#Extract metrics related to student fixed positions
	df_students=df_points.loc[(df_points['obj_type'] == 'student')].groupby(['session','tracker','phase']).agg(
	  Total_attention_time_min=pd.NamedAgg(column='total_attention_time_min', aggfunc=sum),
	  Total_number_visits=pd.NamedAgg(column='count', aggfunc=sum),
	  Average_attention_time_per_visit=pd.NamedAgg(column='time_per_stop_min', aggfunc='mean'),
	  STD_attention_time_per_visit=pd.NamedAgg(column='time_per_stop_min', aggfunc='std'),
	  Average_visits_per_student=pd.NamedAgg(column='count', aggfunc='mean'),
	  STD_visits_per_student=pd.NamedAgg(column='count', aggfunc='std') 
	)

	#Extract metrics related to object/zone fixed positions
	df_objs=df_points.loc[(df_points['obj_type'] == 'zone')].groupby(['session','tracker','phase','tag']).agg(
	  Total_attention_time_min=pd.NamedAgg(column='total_attention_time_min', aggfunc=sum),
	  Total_number_visits=pd.NamedAgg(column='count', aggfunc=sum),
	)
	#Pivot table to create columns for each zone/object
	df_objects = df_objs.pivot_table(
			index=['session', 'tracker','phase'], 
			 columns='tag', 
			 values=["Total_attention_time_min","Total_number_visits"]).reset_index()

	############ Extract metrics related to distance between moving trackers (pending) ############ TBC ############ 








	############ Extract metrics related to ENTROPY ############ 
	df_entropy=df_entropy.groupby(['session','tracker','phase']).agg(
	  Entropy=pd.NamedAgg(column='entropy', aggfunc=sum)
	)

	############ Extract metrics related to DISPERSION (GINI INDEX) ############ 
	df_giniT=df_giniT.groupby(['session','tracker','phase']).agg(
	  gini=pd.NamedAgg(column='gini', aggfunc=sum)
	)
	df_giniT= df_giniT.rename({'gini': 'gini_per_tracker'}, axis=1)
	############ Extract metrics related to DISPERSION (GINI INDEX) all trackers together ############ 
	df_giniSession=df_giniSession.groupby(['session','phase']).agg(
	  gini=pd.NamedAgg(column='gini', aggfunc=sum)
	)
	df_giniSession= df_giniSession.rename({'gini': 'gini_per_session'}, axis=1)


	#############MERGE ALL######################
	merge1 = pd.merge(df_stops, df_transitions, on=['session','tracker','phase'])
	merge2 = pd.merge(df_students, df_objects, on=['session','tracker','phase'])
	merge3 = pd.merge(df_entropy, df_giniT, on=['session','tracker','phase'])

	Merge4 = pd.merge(merge1, merge2, on=['session','tracker','phase'])
	Merge5 = pd.merge(Merge4, merge3, on=['session','tracker','phase'])

	Merge5= pd.merge(Merge5, df_giniSession, on=['session','phase'])

	#remove the following line if interested in other phases
	if (selectedPhase!=-99):
		Output=Merge5.loc[(Merge5['phase'] == selectedPhase)]
	else:
		Output=Merge5		

		
	weighted= int(config.get('parameters','weighted'))		
	#Normalising output (wheightning)
	if (weighted==1):
		#Calculate duration of each phase in  seconds
		df_phases['diff'] = (pd.to_datetime(df_phases['end']) - pd.to_datetime(df_phases['start'])).dt.total_seconds()/60

		#Identify minimum phase duration to trim other session and present results normalised based on the shortest phase
		df_phases_min= df_phases.groupby(['phase']).agg(
		  duration=pd.NamedAgg(column='diff', aggfunc=min),
		  average=pd.NamedAgg(column='diff', aggfunc='mean'),
		  std=pd.NamedAgg(column='diff', aggfunc='std')
		)
		df_phases_min.reset_index(inplace=True)

		#perform normalisation
		#output_copy=Output.copy()
		i=0
		for index, row in Output.iterrows():
			## get duration of the phase of the row
			phase_duration=df_phases.loc[(df_phases['phase'] == row['phase']) & (df_phases['session'] == row['session'])]['diff']

			## get min phase duration
			min_phase_duration=df_phases_min.loc[df_phases_min['phase'] == row['phase']]['duration']

			##calculate weightening factor
			factor= (min_phase_duration.values[0] / phase_duration.values[0])

			col=3
			while col <len(Output.columns):
				Output.iloc[i, col] = row[col] * factor 
				col+=1

			i+=1
			
	print ("Metrics calculation COMPLETED")			
	return (Output)


