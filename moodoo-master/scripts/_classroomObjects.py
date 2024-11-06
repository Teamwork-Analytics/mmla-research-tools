"""Scripts to generate metrics related to "fixed" objects in a classroom 


This script allows the user to 
i) calculate distances between moving trackers and fixed coordinates (zones/objects or students) in the classroom.
2) Calculate the index of dispersion between the moving trackers and fixed points tagged as "students"

This script requires that `pandas` be installed within the Python
environment you are running this script in.

This file can also be imported as a module and contains the following
functions:
    * generate_fixed_points_stats (main) - to create a data frame (time each trackers was close to 
		'student' or 'zone' fixed points) that can be used to calculate the gini index and also used to generate 
		general stats relative to fixed points
	* calculate_gini_by_tracker (main) - processes the data frame returned by the function 
		generate_fixed_points_stats and calculates the index of dispersion by tracker
	* calculate_gini_trackers_together (main) - processes the data frame returned by the function 
		generate_fixed_points_stats and calculates the index for all trackers together
	* gini (auxiliar)- function to calculate gini index of a SERIES  - numpy array
	* get_closer_fixedpoint_stop - auxiliar function to identify which fixed point is the closest to a stop
"""
import configparser
import numpy as np 
import pandas as pd 
import math
import datetime
from dateutil import parser
import time
import _util as util
#load parameters
config = configparser.ConfigParser()
config.read('../info.ini')

def generate_fixed_points_stats(df_stops_transitions,df_fixed_points):
	"""This function creates a data frame with the time each tracker was close to a fixed point
		This can be used to calculate the gini index if only student fixed points are selected.
		This can also serve to generate metrics about fixed points in the classroom.
	
	This function reads the following parameters from the configuration file:
	distance_tracker_fixed_point
	
	Parameters
	----------
	df_stops_transitions : Pandas Data Frame
		The output from _stopsAndTransitions.get_stops_and_transitions() function
		This is: a data frame of stops and transitions
		
	df_fixed_points : Pandas Data Frame 
		Containing the coordinates of fixed objects in the classroom for each particular session.
		It must contain the following columns:
		session (identifier)
		tag (string) name of the fixed object or position
		x,y (coordinates)
		
		It can contain the following columns (not yet used in the calculations)
		time_start (datetime as "%Y-%m-%d_%H:%M:%S")
		obj_type (string) type of fixed object or position (e.g. "zone") The output from _stopsAndTransitions.get_stops_and_transitions() function
		

	Returns
	-------
	df_fixed_points_stats 
		returns a data frame with the stops close to any fixed point (student, zone, etc),
		with the following columns:
			block - (int) the unique identifier of the stop 
			session (identifier)
			tracker (identifier)
			x and y (coordinates)
			tag (string) name of the fixed object or position
			dist_student (distance between the stop and the object in milimeters)
			timestamp (datetime as "%Y-%m-%d_%H:%M:%S")
			max_duration_sec (float) duration of the stop in secons
			phase (int)
			quantile (int)
			obj_type (string) "student" and "zone"
			type (string) "stop" in all cases
	"""
	print ("Generating fixed-points related stats...")
	#Select  only stops from the df_stops_transitions dataframe
	df1_fix = df_stops_transitions[['tracker', 'session','block','x','y','x_stdev','y_stdev','max_duration','type','timestamp']] # select columns
	df1_fix = df1_fix.rename({'x': 'x_mean', 'y': 'y_mean'}, axis='columns')
	df1_fix = df1_fix[df1_fix['type'] == 'stop']

	#Merge datasets to obtain all the potential combinations between stops and fixed objects
	merge = pd.merge(df1_fix, df_fixed_points, on='session')

	#Calculate euclidian distances
	merge['dist_student'] = np.sqrt((merge['x_mean'] - merge['x']) ** 2 + (merge['y_mean'] - merge['y']) ** 2)

	#Simplifying output data frame
	merge = merge[['block', 'tracker', 'session', 'tag', 'dist_student', 'timestamp']]
	obj_types = []
	for index, row_df in merge.iterrows():
		data=df_fixed_points.loc[(df_fixed_points['session'] ==row_df['session']) & (df_fixed_points['tag'] == row_df['tag'])]
		obj_types.append(data['obj_type'].values[0])
	merge['obj_type'] = obj_types
	
	df_dist=merge
	#df_dist includes distances between each  "stop" (associated to each tracker) 
	#	and each fixed object (coordinate). It contains the following columns:
	#		block - (int) the unique identifier of the stop 
	#		session (identifier)
	#		tracker (identifier)
	#		x and y (coordinates)
	#		tag (string) name of the fixed object or position
	#		dist_student (distance between the stop and the object in milimeters)
	#		time_start (datetime as "%Y-%m-%d_%H:%M:%S")
	
	df_stops_transitions.sort_values(by=['session'], inplace=True)
	
	# Create structure with stops only
	stops = df_stops_transitions.loc[(df_stops_transitions['type'] == 'stop')][['block','session','tracker','timestamp','phase','quantile','max_duration_sec','x','y','type']]
	stops.set_index("block", inplace = True) 
	stops.sort_values(by=['session'], inplace=True)
	stops

	# identify closest fixed point to each stop
	df_min_dis=get_closer_fixedpoint_stop(df_dist,stops)


	# Remove distances over the parameter distance_tracker_fixed_point
	distance_tracker_fixed_point= float(config.get('parameters','distance_tracker_fixed_point'))
	df_min_dis = df_min_dis.loc[(df_min_dis['dist_student'] <= distance_tracker_fixed_point)]

	# Calculate total time dedicated to each group of stduents
	summary=df_min_dis.groupby(['session','tracker','phase','tag'])['max_duration_sec'].agg(['sum','count'])
	summary.reset_index(inplace=True)

	# Select only "student" points from the list of ALL fixed ppints
	#df_fixed_points = df_fixed_points.loc[(df_fixed_points['obj_type'] == 'student')]

	##Create structure that will hold SUMMARY data frame plus the fixed trackers that were never visited. 
	col_names =  ['session', 'tracker', 'phase', 'tag', 'sum','count','type']
	df_fixed_points_stats  = pd.DataFrame(columns = col_names)

	summary.reset_index(drop=True)
	for index_fix, row_fixed in df_fixed_points.iterrows():
		phases= summary.loc[(summary['session'] == row_fixed['session'])]['phase'].drop_duplicates()
		trackers= summary.loc[(summary['session'] == row_fixed['session'])]['tracker'].drop_duplicates()
		
		for i1, ph in phases.items():
			for i2, tr in trackers.items():
				df_fixed_points_stats=df_fixed_points_stats.append({'session':row_fixed['session'],'tracker':tr,'phase':ph,'tag':row_fixed['tag'],'sum':0.0,'count':0.0,'obj_type':row_fixed['obj_type']}, ignore_index=True)

	for index_sum, r_sum in summary.iterrows():    
		for index_g, r_gini in df_fixed_points_stats.iterrows(): 
			if (r_sum['session']==r_gini['session'] and r_sum['tracker']==r_gini['tracker'] and 
			   r_sum['phase']==r_gini['phase'] and 
				r_sum['tag']==r_gini['tag']):
				df_fixed_points_stats.loc[index_g, 'sum'] = r_sum['sum']
				df_fixed_points_stats.loc[index_g, 'count'] = r_sum['count']
				r_gini['sum']=r_sum['sum']
				r_gini['count']=r_sum['count']
				
	print ("Fixed points stas generation COMPLETED")
	return (df_fixed_points_stats)

def calculate_gini_by_tracker(df_fixed_points_stats):
	"""This function processes the data frame returned by the function 
		generate_fixed_points_stats and calculates the index of dispersion by tracker
		
	Parameters
	----------
	df_fixed_points_stats
		returns a data frame with the following columns
			block - (int) the unique identifier of the stop 
			session (identifier)
			tracker (identifier)
			x and y (coordinates)
			tag (string) name of the fixed object or position
			dist_student (distance between the stop and the object in milimeters)
			timestamp (datetime as "%Y-%m-%d_%H:%M:%S")
			max_duration_sec (float) duration of the stop in secons
			phase (int)
			quantile (int)
			obj_type (string) student and zones
			type (string) "stop" in all cases
		
	Returns
	-------
	gini_output_separate_trackers
		returns a data frame with the following columns
			session (identifier)
			tracker (identifier)
			phase (int)
			gini (float) the final result
	"""
	print ("Calculating gini index by tracker")
	
	# Select only stops closer to a student
	df_gini = df_fixed_points_stats.loc[(df_fixed_points_stats['obj_type'] == 'student')]
	#CALCULATE GINI INDEX by session, tracker and phase
	gini_output_separate_trackers=df_gini.groupby(['session','tracker','phase'])['count'].agg([gini])
	
	print ("Gini index by tracker COMPLETED")
	return (gini_output_separate_trackers)

def calculate_gini_trackers_together(df_fixed_points_stats):
	"""This function processes the data frame returned by the function generate_fixed_points_stats
		grouped by session and phase (all trackers together)
	Parameters
	----------
	df_fixed_points_stats
		returns a data frame with the following columns
			block - (int) the unique identifier of the stop 
			session (identifier)
			tracker (identifier)
			x and y (coordinates)
			tag (string) name of the fixed object or position
			dist_student (distance between the stop and the object in milimeters)
			timestamp (datetime as "%Y-%m-%d_%H:%M:%S")
			max_duration_sec (float) duration of the stop in secons
			phase (int)
			quantile (int)
			obj_type (string) student and zones
			type (string) "stop" in all cases
		
	Returns
	-------
	gini_output_joint_trackers
		returns a data frame with the following columns
			session (identifier)
			tracker (identifier)
			gini (float) the final result
	"""
	print ("Calculating gini index all tracker together")
	
	# Select only stops closer to a student
	df_gini = df_fixed_points_stats.loc[(df_fixed_points_stats['obj_type'] == 'student')]
	#CALCULATE GINI INDEX by session and phase (all trackers together)
	gini_output_joint_trackers=df_gini.groupby(['session','phase'])['count'].agg([gini])
	
	print ("Gini index for all trackers COMPLETED")
	return (gini_output_joint_trackers)

def gini(array):
    """This function calculates the Gini coefficient of a  SERIES ####numpy array.
	
	
	Parameters
	----------
	array : series (float)		

	Returns
	-------
	gini coefficient (float)
	"""
    #Roberto added this line 
    array=array.as_matrix(columns=None)#<-------there is a warning here
    # based on bottom eq:
    # http://www.statsdirect.com/help/generatedimages/equations/equation154.svg
    # from:
    # http://www.statsdirect.com/help/default.htm#nonparametric_methods/gini.htm
    # All values are treated equally, arrays must be 1d:
    array = array.flatten()
    if np.amin(array) < 0:
        # Values cannot be negative:
        array -= np.amin(array)
    # Values cannot be 0:
    array += 0.0000001
    # Values must be sorted:
    array = np.sort(array)
    # Index per array element:
    index = np.arange(1,array.shape[0]+1)
    # Number of array elements:
    n = array.shape[0]
    # Gini coefficient:
    return ((np.sum((2 * index - n  - 1) * array)) / (n * np.sum(array)))
	
def get_closer_fixedpoint_stop(df_dist,df_stops):
	"""This function merges dataframes of stops and distances between stops and fixed points.
	It returns a list of stops with the closest fixed point to it and the distance to it.

	Parameters
	----------
	df_dist : Pandas Data Frame
		The output from calculate_distances_trackers_objects() function in this script
		This is includes distances between each  "stop" (associated to each tracker) 
		and each fixed object (coordinate). It contains the following columns:
			block - (int) the unique identifier of the stop 
			session (identifier)
			tracker (identifier)
			x and y (coordinates)
			tag (string) name of the fixed object or position
			dist_student (distance between the stop and the object in milimeters)
			time_start (datetime as "%Y-%m-%d_%H:%M:%S")
		
	df_stops : Pandas Data Frame
		This is: a data frame of stops and transitions

	Returns
	-------
	merge
		returns a data frame with the following selected columns from the merge
			block - (int) the unique identifier of the stop 
			session (identifier)
			tracker (identifier)
			x and y (coordinates)
			tag (string) name of the fixed object or position
			dist_student (distance between the stop and the object in milimeters)
			timestamp (datetime as "%Y-%m-%d_%H:%M:%S")
			max_duration_sec (float) duration of the stop in secons
			phase (int)
			quantile (int)
			obj_type (string) "student" in all cases
			type (string) "stop" in all cases
	"""
	### Select row with minimum distance to a fixed object grouped by block, tracker, session
	df_min_dis=df_dist[df_dist['dist_student'].isin(df_dist.groupby(('block','tracker','session')).min()['dist_student'].values)]
	# sort Brand - ascending order
	df_min_dis.sort_values(by=['session'], inplace=True)


	#Merge both dataframes to identify what fixed point is the closest to a stop
	merge = pd.merge(df_min_dis, df_stops, on=['tracker','session','block'])
	merge = merge[['block','session','tracker','tag','dist_student','timestamp_x','obj_type','phase','quantile','max_duration_sec','x','y','type']]
	merge = merge.rename({'timestamp_x': 'timestamp'}, axis='columns')
	return (merge)
	
	