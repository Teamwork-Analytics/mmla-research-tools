"""Data preprocessing scripts

This script allows the user to 
i) Downsample the positioning dataset to 1HZ (1 data point per second), 
ii) to interpolate the dataset to fill gaps in positioning sensing for more than 1 second, 
iii) calculate rotation in degrees if 3D rotation information is provided (in radians),
iv) add information about "phases" if a phases Data frame is provided, 
v) divide each phase into a an arbitrary number of sections (quantiles) of equal duration. 

This script requires that `pandas` be installed within the Python
environment you are running this script in.

This file can also be imported as a module and contains the following functions:

	* preprocessing (main) - this functions calls all the functions below to preprocess the positioning dataset 
    * sampling_and_interpolating - for (down) smapling and interpolating a positioning dataset
	* add_rotation - this function adds a new column 'rotation' in degrees from pitch,roll or yaw in radians 
	* calculate_rotation (auxiliar) - this function accepts angle in radians and generates the angle in degrees
	* add_phases - for adding a new column with Phase information based on a PHASES Data Frame
	* add_quantiles - for adding a new column with "quantile" information: quantiles are artifitial divisions of data points within 
		a phase in X number of equal parts according to their timestamp

"""
import configparser
import pandas as pd
import math
import numpy as np 
#load parameters
config = configparser.ConfigParser()
config.read('../info.ini')

def preprocessing(df,dfPhases,_fill_NaN_Values,_include_all_data):
	"""This functions calls all the functions to preprocess the positioning dataset in the following order. 
	1) add_phases
	2) add_quantiles
	3) add_rotation
	4) sampling_and_interpolating
	
	Use these functions separately if you need to skip any pre-procesisng step. 

	Parameters
	----------
	df : Pandas Data Frame
		A Localization DataFrame whith at least the following columns: 
			timestamp (datetime as "%Y-%m-%d_%H:%M:%S")
			session (identifier)
			tracker (identifier)
			x and y (coordinates)

	dfPhases : Pandas Data Frame
		a Data Frame with the following columns: 
			session : string
			phase : int
			start : datetime
			end  : datetime
			comment : string (optional, not used by this script)
		Phases have to be numbered starting from 1. Phase 0 will be ignored.
	include_all_data : int
		If a value of "1" is provided all the dataset will be returned. 
		If "0" is provided, all the datapoints that do not belong to a Phase will be excluded

	_fill_NaN_Values: int
		If Fill NaN Values= 1 the rows that will be added as a result of interpolating x and y data
		will be filled with data from previous rows. In doubt, set it to 1

	Returns
	-------
	df2 : Pandas Data Frame
		a downsampled Pandas dataset (to 1 hz). If other columns are present the new rows created as a result 
		of the interpolation copy the same values as the previous row. 
		
		New columns: 
			interpolated : int (A new Interpolated column is added to indicate with 1 if a row was inserted; 
				and 0 if the row was in the original dataset)
			rotation : float (rotation of the tracker in degreed (it can contain negative values with reference 
				to the UPPER direction in the floorplan) 
			phase : int 
			quantile : int

	"""
	print ("Commencing preprocessing......")
	#Add Phase column
	df=add_phases(df,dfPhases,_include_all_data)
	print ("Phases added...")
	
	#Add Quantiles column
	df=add_quantiles(df,dfPhases)
	print ("Quantiles added...")

	#Add column rotation to the DataFrame
	df=add_rotation(df)
	print ("Rotation in deggrees calculated...")

	#Downsampling and interpolating
	df2=sampling_and_interpolating(df,_fill_NaN_Values)
	print ("Downsampling and interpolation completed")

	print ("Preprocessing COMPLETED")
	return (df2)

def sampling_and_interpolating(df,_fill_NaN_Values):
	"""This function does the following:
	1) SAMPLING: It normalises the sampling frequency of the positioning data to 1Hz (
	exactly one datapoint per second per tracker)
	2) INTERPOLATION: It interpolates missing values for each tracker to have exactly 60 
	data points per second. 

	Parameters
	----------
	df : Pandas Data Frame
		A Localization DataFrame whith at least the following columns: 
			timestamp (datetime as "%Y-%m-%d_%H:%M:%S")
			session (identifier)
			tracker (identifier)
			x and y (coordinates)
	_Fill_NaN_Values: int
		If Fill NaN Values= 1 the rows that will be added as a result of interpolating x and y data
		will be filled with data from previous rows. In doubt, set it to 1

	Returns
	-------
	df2 : Pandas Data Frame
		a downsampled Pandas dataset. If other columns are present the new rows created as a result 
		of the interpolation copy the same values as the previous row. 
		A new Interpolated column is added to indicate with 1 if a row was inserted; 
		and 0 if the row was in the original dataset.)

	"""
	Fill_NaN_Values=_fill_NaN_Values

	#output data frame
	df2 = pd.DataFrame()
	# Add a signal to the input dataset that indicates if each row was contained in the original dataset (0) or whether t is interpolated to fill gaps (1)
	df['interpolated'] = '0'

	# get unique 'tracker' valuea for the loop
	list_tracker = df.tracker.unique()
	# get unique 'session' value for the loop
	list_session = df.session.unique()

	session_tracker=df.groupby(['session','tracker']).size().reset_index().rename(columns={0:'count'})

	for index, row_pair in session_tracker.iterrows():
			#GET sub dataframe for a particular tracker
			session_df = df[(df['tracker'] == row_pair['tracker']) & (df['session'] == row_pair['session'])]
			
			## Create new dataframe with 60 data points per second for each session using start and end time from classroom dataset
			# get first value in timestamp 
			first = session_df['timestamp'].iloc[0]
			# last value
			last = session_df['timestamp'].iloc[-1]
			# create time range for new dataframe 
			df_time = pd.date_range(start = first, end = last, freq='S') 
			
			## MERGE classroom dataframe to new dataframe with 60 data points 
			session_df = session_df.set_index('timestamp') # need to index timestamp 
			merge = pd.merge(df_time.to_frame(), session_df, left_index = True, right_on = 'timestamp', how ='left')#.fillna(method='ffill')
					
				
			## FILL MISSING VALUES - interpolate values 
			# forward-fill (using existing values to fill)
			m = merge.copy()
			
			# fill x and y using linear interpolation
			m[['x', 'y']] = m[['x', 'y']].interpolate(method='linear', axis=0).ffill().bfill()
			
			# SAVE
			df2 = df2.append(m)
			df2.reset_index(drop=True, inplace=True)

	#Flag added rows as a result of interpolation        
	df2['interpolated'] = df2['interpolated'].fillna('1')
	#copy NaN values from previous rows 
	df2.fillna(method='ffill', inplace=True)
	return df2

def add_rotation(df):
	"""This function adds a new column 'rotation' in degrees from pitch,roll or yaw in radians 

	Parameters
	----------
	df : Pandas Data Frame
		a Localization Data Frame that contains the columns 
		pitch : float (rotation in radians)
		roll : float (rotation in radians) 
		yaw : float (rotation in radians)
	_rotation_variable: string
		a string value that indicates which rotation variable will be used to calculate the rotation of 
		the sensor on the floorplan. It can ONLY take the values: 
		'yaw', 'roll' or 'pitch'
	_north : float
		the rotation in radians facing north (UPPER direction in the floor plan)
			

	Returns
	-------
	df : Pandas Data Frame
		the same Data Frame with the new column "rotation" added

	"""

	target_column= config.get('parameters','target_column')
	north= float(config.get('parameters','north'))

	df['rotation'] = calculate_rotation(df[target_column],north)
	return df

def calculate_rotation(radians, north):
	"""This function accepts angle in radians and generates the angle in degrees

	Parameters
	----------
	radians : float
		angle in radians
	north : float
		the rotation in radians facing north (UPPER direction in the floor plan)
			
	Returns
	-------
	result: float
		angle in which zero degreees is facing north in the floor plan

	"""
	return radians * 57.2958 - (north * 57.2958) 

def add_phases(df,dfPhases,_include_all_data):
	"""This function adds a new column 'PHASE' to the main dataset based on a Phase Data frame. 

	Parameters
	----------
	df : Pandas Data Frame
		a Localization Data Frame with timestamp information
	dfPhases : Pandas Data Frame
		a Data Frame with the following columns: 
			session : string
			phase : int
			start : datetime
			end  : datetime
			comment : string (optional, not used by this script)
		Phases have to be numbered starting from 1. Phase 0 will be ignored.
	_include_all_data : int
		If a value of "1" is provided all the dataset will be returned. 
		If "0" is provided, all the datapoints that do not belong to a Phase will be excluded

	Returns
	-------
	df : Pandas Data Frame
		the same Data Frame with the new column "phase" added

	"""
	phases = []
	#add Phase number to each data point
	for index, row_pair in df.iterrows():
		res=dfPhases.loc[(row_pair['session'] == dfPhases['session']) & (row_pair['timestamp'] >= dfPhases['start']) & (row_pair['timestamp'] <= dfPhases['end']) & (dfPhases['phase']!=0)]

		if (len(res)>0):
			phases.append(res['phase'].values[0])

		else: 
			phases.append(-100)

	#add new Phase column to Data Frame
	df['phase'] = phases 
	#remove datapoints out of the phase with value -100
	if (_include_all_data==0):
		df = df[df.phase != -100]
	return df


def add_quantiles(df,dfPhases):
	"""This function adds a new column 'quantile' to the main dataset. The function equally splits EACH phase
	in X parts of equal duration. X = NumberOfQuantiles. Each data point is marked with the number of the part 
	from 1 to X. 

	Parameters
	----------
	df : Pandas Data Frame
		a Localization Data Frame with timestamp information
	dfPhases : Pandas Data Frame
		a Data Frame with the following columns: 
			session : string
			phase : int
			start : datetime
			end  : datetime
			comment : string (optional, not used by this script)
		Phases have to be numbered starting from 1. Phase 0 will be ignored.
	_numberOfQuantiles	: int
		Number of parts in which the data within each phase will be divided based on their timestamps. 
		4 for quantiles but it can be another number

	Returns
	-------
	df : Dataframe
		the same Data Frame with the new column "quantile" added

	"""
	
	_numberOfQuantiles = float(config.get('parameters','numberOfQuantiles'))
	#CALCULATE QUANTILE DURATION
	dfPhases['quantile_duration']= ((dfPhases['end'] - dfPhases['start']) /np.timedelta64(1,'s') )/ _numberOfQuantiles
	

	#ADD Quantile INFORMATION TO COLUMN
	quantiles = []
	for index, row_pair in df.iterrows():
		res=dfPhases.loc[(row_pair['session'] == dfPhases['session']) & (row_pair['phase'] == dfPhases['phase'])]
		if (len(res)>0):
			q= math.floor( (((row_pair['timestamp'] - res['start']) /np.timedelta64(1,'s')) / res['quantile_duration'])+1)
			if (q>_numberOfQuantiles):
				q=_numberOfQuantiles
		else:
			q=-100
		quantiles.append(q) 
		
	df['quantile'] = quantiles   
	return df


