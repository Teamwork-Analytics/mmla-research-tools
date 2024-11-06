"""Scripts to generate metrics related to stops and transitions

This script allows the user to 
i) generate metrics related to stops, a stop can be defined as a sequence of positioning data points that 
	are short distance apart in space and time. If a teacher is being followed, according to the notion of 
	Spatial Pedagogy, this can denote a period in which the teacher is "positioned to conduct formal teaching" 
	or stands "alongside the students' desk or between rows" of seats to interact with students
ii) generate metrics related to transitions between stops

This script requires that `pandas` be installed within the Python
environment you are running this script in.

This file can also be imported as a module and contains the following functions:
    * stops_transitions (main) - this function calls the three functions below to get a new data frame of stops and transitions  
	* generate_positioning_clusters - This function generates a data frame that clusters data points 
		according to their distance.
	* tag_clusters - This function generates a data frame that identifies clusters 
		(the output from function generate_positioning_clusters) as stops or transitions.
	* get_stops_and_transitions - This function generates a data frame that contains meta data about stops  (one per line) and transitions (all the lines 
		to enable further modelling of the trajectory itself)
 
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

def stops_transitions(df_preprocessed):
	"""This functions calls the following functions to model the preprocessed dataset as stops and transitions: 
	1) add_phases
	2) add_quantiles
	3) add_rotation
	4) sampling_and_interpolating
	
	Use these functions separately if you need to skip any pre-procesisng step. 

	Parameters
	----------
	df_preprocessed : Pandas Data Frame
		A Localization DataFrame whith at least the following columns: 
			timestamp (datetime as "%Y-%m-%d_%H:%M:%S")
			session (identifier)
			tracker (identifier)
			x and y (coordinates)
			phase (int)
			quantile (int) Set to 1 if not interested in using this column


	Returns
	-------
	df : Pandas Data Frame
		returns a data frame with information about stops (one line/row) and transitions (one line/row
			per datapoint in the with the following additional columns
			group - the cluster id (a self incremental intiger that starts from 1)
			base_dist - distance from a datapoint to the first datapoint in the cluster
			intra_dist - distance to the previous data point
			time_diff - time difference from the previous data point
			type - (string) indicating if the data point belongs to a "stop" or a "transition"
			x, y - point at the centroids of the stops 
			x_stdev, y_stdev - standard deviation of the points within a stop. (for transitions the value is zero)

	"""
	#Cluster datapoints as stops and transitions
	df=generate_positioning_clusters(df_preprocessed)
	print ("Generating clusters completed")
	
	#Tag clusters as stops or transition
	df=tag_clusters(df)
	print ("Clusters tagged")
	
	#Generate data frame with information about stops and transitions to be further processed to generate metrics
	df=get_stops_and_transitions(df)
	print ("Data frame of stops and transitions generated")
	
	print ("Processing stops and transitions COMPLETED")
	return (df)


def generate_positioning_clusters(df):
	"""This function generates a data frame that clusters data points according to their distance.  
		The parameter "distance" is read from the config file and it is used to create a new cluster 
		if the distance between two consecutive datapoints is higher than the parameter 'distance'
	
	Parameters
	----------
	df : Pandas Data Frame
		A Localization DataFrame whith at least the following columns: 
			timestamp (datetime as "%Y-%m-%d_%H:%M:%S")
			session (identifier)
			tracker (identifier)
			x and y (coordinates)
			phase (int)
			quantile (int) Set to 1 if not interested in using this column

	Returns
	-------
	data1
		returns a data frame with the following additional columns
			group - the cluster id (a self incremental intiger that starts from 1)
			base_dist - distance from a datapoint to the first datapoint in the cluster
			intra_dist - distance to the previous data point
			time_diff - time difference from the previous data point

	"""
	#CALCULATE DISTANCE BETWEEN TWO SUBSEQUENCED DATA POINTS
	df_dist = pd.DataFrame()
		  
	list_tracker = df.tracker.unique()
	list_session = df.session.unique()

	for x,i in enumerate(list_tracker):
			
		## Loop through unique tracker and session       
		#df = df.copy()
		tracker2 = i
		tracker_df = df[df['tracker'] == tracker2]
			
		for y,j in enumerate(list_session):
			
			session2 = j
			session_df = tracker_df[tracker_df['session'] == session2]

			# Shift x and y to get the coordinates of the previous positioning datapoint
			session_df['x_shifted'] = session_df.groupby(['session'])['x'].shift(1)
			session_df['y_shifted'] = session_df.groupby(['session'])['y'].shift(1)
			
			# Remove first row of every session (shifted = nan)
			session_df = session_df.dropna()
			
			# Calculate distance between two points
			session_df['dist'] = np.sqrt((session_df['x_shifted'] - session_df['x']) ** 2 + (session_df['y_shifted'] - session_df['y']) ** 2)
			
			# Append Distance column
			df_dist = df_dist.append(session_df) 


	#CREATE CLUSTERS OF DATA POINTS (STOPS) according to Distance and Duration parameters


	#Load parameter that is used to create a new cluster if the distance between two consecutive datapoints is
	#higher than the parameter 'distance'
	distance= float(config.get('parameters','distance'))

	#sequential numbering of clusters of positioning datapoints (called in this code "group or grouping")
	fix_seq = 1      #fixation sequence, starts at 1 (then adds +1) --> to create group numbering

	data1 = [] #this will be used to save clusters 


	## Loop through unique tracker and session
	
	previous_row = None
	for x,i in enumerate(list_tracker):

		tracker = i
		tracker_df = df[df['tracker'] == tracker]
		
		for y,j in enumerate(list_session):
			count=0
			session = j
			session_df = tracker_df[tracker_df['session'] == session]
			
			# print details of each tracker and seesion while code is running (useful in identifying if code breaks) 
			#print(tracker, session, len(session_df))
			
			# Convert dataframe to list 
			#data = session_df.values.tolist()
			data = session_df
			
			## Loop through each row
			# if row (k) > 0; if <= t_hold then calculate distance to base point, and add to time 
			#                if > t_hold - then redefine base point and start calculating distance to base point and add time
			# if row (k) = 0; then use the values as is (see elif k == 0)
			
			for k, row_pair in data.iterrows():
				count=count+1
			#for k, i in enumerate(data[0:]):
				if count > 1: 
					p_time = row_pair["timestamp"]
			
					# x = column [5]; y = column [6]
					x2 = float(row_pair["x"]) # current row value 
					x1 = float(previous_row["x"]) # previous row value 
					y2 = float(row_pair["y"])
					y1 = float(previous_row["y"]) 
					phase = int(row_pair["phase"])
					quantile = int(row_pair["quantile"])
			
					# calculate the distance from previous point
					dist_p = math.sqrt((x2-x1)**2+(y2-y1)**2) 
					# calculate the distance from base point (the first point in the group/cluster)
					dist_b = math.sqrt((x2-b_x1)**2+(y2-b_y1)**2) 
					#caluclate the time delta from base point
					t_diff = p_time - b_time 

					if dist_b <= distance:  
						# if distance from current point to centroid is lower than threshold (distance = 1000mm - 1m), 
						# it means that the person/object is covering a short distance - the point is inside the cluster
						# add to list with current cluster/group number
						data1.append([fix_seq, tracker, session, phase, quantile, str(p_time), x2, y2, dist_b, dist_p, t_diff])
						
					elif dist_b > distance:
						# if distance from current point to centroid is higher than threshold (distance = 1000mm - 1m), 
						# it means that the person/object is in another cluster - then change centroid info
						#Create new cluster or grouping
						b_time = row_pair["timestamp"]
						b_x1 = float(row_pair["x"])
						b_y1 = float(row_pair["y"])                    
						phase = int(row_pair["phase"])
						quantile = int(row_pair["quantile"])
				
						fix_seq = fix_seq + 1 # coordinate grouping according to distance threshold 
						data1.append([fix_seq, tracker, session, phase, quantile, b_time, b_x1, b_y1, dist_b, dist_p])
						# don't add t_diff as 0; leaving blank will introduce NaT (which will identify the column as timedate type) 

					t_diff = p_time - b_time
					previous_row=row_pair

				elif count == 1:
					previous_row=row_pair
					b_time = row_pair["timestamp"]
					b_x1 = float(row_pair["x"])
					b_y1 = float(row_pair["y"])
					phase = int(row_pair["phase"])
					quantile = int(row_pair["quantile"])
					data1.append([fix_seq, tracker, session, phase, quantile, b_time, b_x1, b_y1, 0, 0])
					# don't add t_diff as 0; leaving it blank will introduce NaT (which will identify the column as timedate type) 

	df2 = pd.DataFrame (data1,columns=['group','tracker','session','phase','quantile','timestamp','x','y','base_dist','intra_dist','time_diff'])
	return (df2)
	
def tag_clusters(df_dist):
	"""This function generates a data frame that identifies clusters as stops or transitions.   
		The parameter "duration" is read from the config file and it is used to identify if a cluster 
		is a stop if the dureation of that stop is larger than the time indicated in the parameter (e.g. 10 seconds)
	
	Parameters
	----------
	df_dist : Pandas Data Frame
		This df has to be the Data frame returned by the function: generate_positioning_clusters(df)
		It has to contain the following columns:
			group - the cluster id (a self incremental intiger that starts from 1)
			base_dist - distance from a datapoint to the first datapoint in the cluster
			intra_dist - distance to the previous data point
			time_diff - time difference from the previous data point
			------------------plus the original columns of the dataset:
			timestamp (datetime as "%Y-%m-%d_%H:%M:%S")
			session (identifier)
			tracker (identifier)
			x and y (coordinates)
			phase (int)
			quantile (int) Set to 1 if not interested in using this column		

	Returns
	-------
	df_new
		returns a data frame with the following additional columns
			type - (string) indicating if the data point belongs to a "stop" or a "transition"

	"""
	# Extract the number of seconds component from column "time_diff"
	df_dist[['time_diff']] = df_dist[['time_diff']].astype(str)
	# Get seconds from the time difference
	df_dist['time_diff2'] = df_dist['time_diff'].str.extract('(..:..:..)', expand=True)
	df_dist = df_dist.fillna('00:00:00')
	df_dist['time_diff2'] = pd.to_timedelta(df_dist['time_diff2'])
	df_dist = df_dist[['group', 'tracker', 'session', 'phase', 'quantile', 'timestamp', 'x', 'y', 'base_dist', 'intra_dist', 'time_diff2']]
	
	# create 'max_duration' column  - to use it to further define stops and transitions
	df_dist['max_duration'] = df_dist.groupby(['group'])['time_diff2'].transform(max)
	df_dist['max_duration'] = pd.to_timedelta(df_dist['max_duration'])	

	#Add Type (Stop and Transition) column
	#Assign stop and transition labels according to parameter duration 

	#get parameter from config file
	duration= str(config.get('parameters','duration'))
	
	# Tag clusters as stops or transitions
	type = []
	stop = pd.Timedelta(duration)

	for row in df_dist['max_duration']:
		if row >= stop:
			type.append('stop')
		else:
			type.append('transition')
			
	# Add a column to the data frame from the list 'type'
	df_dist['type'] = type

	#The following code fixes the "group" column by setting the same ID for all the consecutive datapoints 
	#labelled as transition (including clusters with less datapoints than the parameter 'duration'). 
	# Fuller explanation: A Transition (sequential) can be made of several 'clusters' (due to distance with base 
	#exceeding threshold set (e.g. 1m)), this is because when distance exceeds 1m, the numbering resets for the 
	#column "group", therefore starting with a new group or cluster of datapoints. This means that the 
	#'group' column would have several groups which belong to the same transition. Since in actuality 
	#these transitions belong to a single transition. Consequently, this step is required so that these 
	#transitions are labelled to belong to the same one transition. 
	
	#A new column "block" is added to uniquely identify the stop or transition. A block can contain multiple 'groups'

	df_group = df_dist.copy()
	df_new_group = pd.DataFrame()
	list_tracker = df_group.tracker.unique()
	list_session = df_group.session.unique() 

	## Loop through unique group
	for x,i in enumerate(list_tracker):
		
		df = df_group.copy()
		tracker = i
		tracker_df = df[df['tracker'] == tracker]
		tracker_df
	   
		for y,j in enumerate(list_session):
			
			session = j
			session_df = tracker_df[tracker_df['session'] == session]
			  
			session_df['block'] = (session_df.type.shift(1) != session_df.type).astype(int).cumsum()
		
			# SAVE
			df_new_group = df_new_group.append(session_df)
			
	#Duration between each point (by block)
	#Since sequential transitions are relabelled as belonging to a single group. 
	#The duration between each point needs to be recalculated as well (this since, duration resets to
#	'00:00:00' with the distance calculation performed in function generate_positioning_clusters(df))
	df_dur = df_new_group.copy()

	tracker = df_dur.tracker.unique()

	session = df_dur.session.unique()

	block = df_dur.block.unique()

	df_new = pd.DataFrame()

	list_tracker = tracker
	list_session = session
	list_block = block 

	for x,i in enumerate(list_tracker):
		
		df = df_dur.copy()
		tracker = i
		tracker_df = df[df['tracker'] == tracker]
		tracker_df
	   
		for y,j in enumerate(list_session):
			
			session = j
			session_df = tracker_df[tracker_df['session'] == session]

			for z,k in enumerate(list_block):
		
				block = k
				block_df = session_df[session_df['block'] == block]
		 
		
				block_df['delta'] = (block_df['timestamp'] - block_df['timestamp'].shift()).fillna(pd.Timedelta('0 days'))
		
				# SAVE
				df_new = df_new.append(block_df)
		
	return (df_new)
	
def get_stops_and_transitions(df_dist):
	"""This function generates a data frame that contains meta data about stops  (one per line) and transitions (all the lines 
	to enable further modelling of the trajectory itself)
	
	Parameters
	----------
	df_dist : Pandas Data Frame
		This df has to be the Data frame returned by the function: tag_clusters(df)
		It has to contain the following columns:
			type - (string) stop or transition
			block - (int) the unique identifier of the stop or transition
			------------------plus the original columns of the dataset, for example:
			timestamp (datetime as "%Y-%m-%d_%H:%M:%S")
			session (identifier)
			tracker (identifier)
			x and y (coordinates)
			phase (int)
			quantile (int) Set to 1 if not interested in using this column		

	Returns
	-------
	merge
		returns a data frame with the following additional columns
			x, y - point at the centroids of the stops 
			x_stdev, y_stdev - standard deviation of the points within a stop. (for transitions the value is zero)

	"""

	list_tracker = df_dist.tracker.unique()
	list_session = df_dist.session.unique()
	list_block = df_dist.block.unique()

	#### 1) Max duration
	#Once the sequential saccades are assign to a block, the max duration for each block is derived
	df_max_duration = pd.DataFrame()

	for x,i in enumerate(list_tracker):
		
		df = df_dist.copy()
		tracker = i
		tracker_df = df[df['tracker'] == tracker]
		tracker_df
	   
		for y,j in enumerate(list_session):
			
			session = j
			session_df = tracker_df[tracker_df['session'] == session]
		  
			session_df['max_duration'] = session_df.groupby('block')['timestamp'].transform(lambda x: x.iat[-1] - x.iat[0])
			print(session_df['max_duration'])
			#session_df.groupby('block')['timestamp'].transform(lambda x: x.iat[-1] - x.iat[0]).to_timedelta().total_seconds()

				# SAVE
			df_max_duration = df_max_duration.append(session_df)
			
	#GET STOPS
	df_dur_fixation = df_max_duration[df_max_duration['type'] == 'stop'] # filter only stops

	#GET TRANSITIONS
	df_dur_saccades = df_max_duration[df_max_duration['type'] == 'transition'] # filter only transitions

	# Extract just the block and max duration, and remove duplicate rows
	df_duration = df_dur_fixation[['tracker', 'session', 'block', 'phase','quantile', 'max_duration', 'type']] 
	df_duration = df_duration.drop_duplicates()
	df_duration.sort_values(by=['tracker','session','block'], inplace=True)

	df_duration = df_duration.groupby(['tracker', 'session', 'block', 'max_duration',  'type']).agg(
		{
			 'phase':min,   
			 'quantile': 'first'  # get the first date per group
		}
	)
	df_duration.reset_index(inplace=True)
	df_duration.sort_values(by=['tracker','session','block'], inplace=True)
	



	#### 2) Get first and last timestamp value for each block
	# Timestamp - start and end (for entire dataset - fixation and saccades)
	df = df_max_duration.copy()
	df = df.groupby(['tracker', 'session', 'block'])['timestamp'].agg(['first','last'])
	df.index = df.index.set_names(['tracker', 'session', 'block'])
	df.reset_index(inplace=True)
	df.rename(columns={'first':'timestamp'}, inplace=True)


	#### 3) Centroid (x,y)
	#Calculate centroid (mean of x and y coordinate by blocks) - only for fixation
	test = df_dur_fixation.copy()

	test2_centroid = test.groupby(['tracker', 'session', 'block'])['x','y'].agg(['mean'])
	test2_centroid.columns = ['x', 'y'] # relabel column (x,y)
	test2_centroid.index = test2_centroid.index.set_names(['tracker', 'session', 'block'])
	test2_centroid.reset_index(inplace=True)
	test2_centroid.head()

	#### 4) Stdev (x,y) - only for fixation
	test2_stdev = test.groupby(['tracker', 'session', 'block'])['x','y'].agg(['std'])
	test2_stdev.columns = ['x_stdev', 'y_stdev'] # relabel column (x,y)
	test2_stdev.index = test2_stdev.index.set_names(['tracker', 'session', 'block'])
	test2_stdev.reset_index(inplace=True)
	test2_stdev.head()

	#### 5) Tracker and Session info
	df_tracker = df_dist.copy()
	df_tracker = df_tracker[['block','tracker', 'session']]
	df_tracker = df_tracker.drop_duplicates()
	df_tracker.head()

	### 7) Merge 
	#Create dataframe with additional information for the blocks (max duration, centroid, stdev)

	#remove phase and quartile; add timestamp (start time and end time)  <--------------------------------avoid doing this!
	merge = pd.merge(pd.merge(test2_centroid,test2_stdev,on=['tracker','session','block']),df_duration,on=['tracker','session','block'])

	#Merge with start and end timestamp
	merge = pd.merge(merge,df,on=['tracker','session','block'])

	#merge with transitions
	merge = merge.append(df_dur_saccades)
	# order by block
	merge = merge.sort_values(['tracker','session', 'block','timestamp'])
	merge = merge.fillna(0)
	merge['max_duration_sec'] = merge['max_duration'].dt.total_seconds()

	return (merge)