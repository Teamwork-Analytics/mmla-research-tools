"""Scripts to generate metrics related to entropy

This script allows the user to 
i) calculate entropy on the pre-processed positioning dataset based on the dimensions of the room

This script requires that `pandas` be installed within the Python
environment you are running this script in.

This file can also be imported as a module and contains the following
functions:
    * calculate_entropy_session_tracker_phase (main function)- ENTROPY grouped by session, tracker, phase
    * calculate_entropy_session_tracker - ENTROPY grouped by session, tracker (created in case this is needed)
	* get_entropy (auxiliar)- This function calculates entropy for a given DataFrame with a grid of proportions in column "grid".
	* plot_charts_per_tracker - This function generates Voronoi, ConvexHull and Delaunay charts in the folder "output_figures"
		per tracker.
"""
import configparser
import numpy as np 
import pandas as pd 
from scipy.stats import entropy
from scipy.spatial import Voronoi, voronoi_plot_2d, ConvexHull , convex_hull_plot_2d, Delaunay, delaunay_plot_2d
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.cm as cm
import csv
import math
import time
import _util as util
from pathlib import Path

#load parameters
config = configparser.ConfigParser()
config.read('../info.ini')


def calculate_entropy_session_tracker_phase(df_dist):
	"""This function generates a grid for each session, tracker and phase to calculate the entropy of that tracker
	in each "phase". 

	This function reads the following parameters from the configuration file:
	room_x
	room_y
	size_of_grid_cells

	Parameters
	----------
	df_dist : Pandas Data Frame
		A Localization DataFrame whith at least the following columns: 
			timestamp (datetime as "%Y-%m-%d_%H:%M:%S")
			session (identifier)
			tracker (identifier)
			x and y (coordinates)
			phase (int)
			quantile (int) Set to 1 if not interested in using this column

	Returns
	-------
	pairs_session_tracker
		returns a data frame with the following columns
			session (identifier)
			tracker (identifier)
			count (int) number of datapoints considered
			grid the m by n matrix that contains the proportion of data points in each cell. 
				the matrix is created based on the dimensions of the room and a cell size set in the configuration file.
			entropy - unidimensional entropy calculated on the values of the grid

	"""
	print ("Calculating entropy.")
	# Read room dimensions and grid size from config file
	room_x= float(config.get('parameters','room_x'))
	room_y= float(config.get('parameters','room_y'))
	size_of_grid_cells= float(config.get('parameters','size_of_grid_cells'))

	# Calculate number of columns and rows
	n_gridsquares = int(round(room_x/size_of_grid_cells,0))
	m_gridsquares = int(round(room_y/size_of_grid_cells,0))

	distinct_phase_quartile=df_dist.groupby(['session','tracker','phase']).size().reset_index().rename(columns={0:'count'})

	# Create a proportional grid for each session, tracker and phase 
	grids = []
	for index, row_pair in distinct_phase_quartile.iterrows():
		##CREATE GRID WITH ZEROS
		new_grid = [0] * m_gridsquares
		for i in range(m_gridsquares):
			new_grid[i] = [0] * n_gridsquares
		#print ('Grid created')
		
		##FILL GRID FROM THE DATASET- SUM of DATAPOINTS
		for index, row_df in df_dist.iterrows():
			x_var=int(math.floor(row_df['x']/size_of_grid_cells))
			y_var=int(math.floor(row_df['y']/size_of_grid_cells))
			if (x_var<n_gridsquares and y_var<m_gridsquares 
				and row_df['tracker']==row_pair['tracker'] 
				and row_df['session']==row_pair['session']
				and row_df['phase']==row_pair['phase']
				#and row_df['quartile']==row_pair['quartile']
			   ):
				(new_grid[y_var])[x_var] = (new_grid[y_var])[x_var]  + 1  
				
		#print ('Datapoints')
		#print (pd.DataFrame(new_grid))
		
	   
		## CALCULATE the proportion of data points for the given period 
		#print ('...calculating proportions') 
		y_index=0
		x_index=0
		for row in new_grid:
			for column in row:
				#print ((new_grid[x_index])[y_index])
				(new_grid[x_index])[y_index] = ( (new_grid[x_index])[y_index] * 100 / row_pair['count'])
				#print ((new_grid[x_index])[y_index])
				y_index+=1
			x_index+=1
			y_index=0
					 
		#print ('Proportions')         
		#print (pd.DataFrame(new_grid))
		
		grids.append(new_grid)

	##Append grids list to pairs-session_tracker structure
	distinct_phase_quartile['grid'] = grids

	#Calculate entropies
	distinct_phase_quartile=get_entropy(distinct_phase_quartile)
	print ("Entropy calculation per phase COMPLETED")
	return (distinct_phase_quartile)



def calculate_entropy_session_tracker(df_dist):
	"""This function generates a grid for each session and tracker to calculate the entropy of that tracker
	for the whole dataset. 

	This function reads the following parameters from the configuration file:
	room_x
	room_y
	size_of_grid_cells

	Parameters
	----------
	df_dist : Pandas Data Frame
		A Localization DataFrame whith at least the following columns: 
			timestamp (datetime as "%Y-%m-%d_%H:%M:%S")
			session (identifier)
			tracker (identifier)
			x and y (coordinates)
			phase (int)
			quantile (int) Set to 1 if not interested in using this column

	Returns
	-------
	pairs_session_tracker
		returns a data frame with the following columns
			session (identifier)
			tracker (identifier)
			count (int) number of datapoints considered
			grid the m by n matrix that contains the proportion of data points in each cell. 
				the matrix is created based on the dimensions of the room and a cell size set in the configuration file.
			entropy - unidimensional entropy calculated on the values of the grid

	"""
	print ("Calculating entropy.")
	# Read room dimensions and grid size from config file
	room_x= float(config.get('parameters','room_x'))
	room_y= float(config.get('parameters','room_y'))
	size_of_grid_cells= float(config.get('parameters','size_of_grid_cells'))

	# Calculate number of columns and rows
	n_gridsquares = int(round(room_x/size_of_grid_cells,0))
	m_gridsquares = int(round(room_y/size_of_grid_cells,0))

	df_block = df_dist.copy()

	# Get unique trackers and sessions
	tracker = df_block.tracker.unique()
	session = df_block.session.unique()

	# Get session tracker pairs
	pairs_session_tracker=df_dist.groupby(['session','tracker']).size().reset_index().rename(columns={0:'count'})


	# Create a grid for each session and tracker 
	grids = []
	for index, row_pair in pairs_session_tracker.iterrows():
		##CREATE GRID WITH ZEROS
		new_grid = [0] * m_gridsquares
		for i in range(m_gridsquares):
			new_grid[i] = [0] * n_gridsquares
		#print ('Grid created')
		
		##FILL GRID FROM THE DATASET- SUM of DATAPOINTS
		for index, row_df in df_dist.iterrows():
			x_var=int(math.floor(row_df['x']/size_of_grid_cells))
			y_var=int(math.floor(row_df['y']/size_of_grid_cells))
			if x_var<n_gridsquares and y_var<m_gridsquares and row_df['tracker']==row_pair['tracker'] and row_df['session']==row_pair['session']:
				(new_grid[y_var])[x_var] = (new_grid[y_var])[x_var]  + 1  
				
		#print ('Datapoints')
		#print (pd.DataFrame(new_grid))
		
	   
		## CALCULATE the proportion of data points for the given period 
		#print ('...calculating proportions') 
		y_index=0
		x_index=0
		for row in new_grid:
			for column in row:
				#print ((new_grid[x_index])[y_index])
				(new_grid[x_index])[y_index] = ( (new_grid[x_index])[y_index] * 100 / row_pair['count'])
				#print ((new_grid[x_index])[y_index])
				y_index+=1
			x_index+=1
			y_index=0
					 
		#print ('Proportions')         
		#print (pd.DataFrame(new_grid))
		
		grids.append(new_grid)

	##Append grids list to pairs-session_tracker structure
	pairs_session_tracker['grid'] = grids

	#Calculate entropies
	pairs_session_tracker=get_entropy(pairs_session_tracker)

	print ("Entropy calculation per tracker COMPLETED")
	return (pairs_session_tracker)
    

def get_entropy(df):
	"""This function calculates entropy for a given DataFrame with a grid of proportions in column "grid".
		
		
	Parameters
	----------
	df : Pandas Data Frame
		This df MUST contain a column labelled as "grid" 
		This columns should contain an m by n matrix with a proportion value from 0 to 1 in each cell. 		

	Returns
	-------
	df
		returns a data frame with the following additional columns
			entropy - (float) indicating the calculated entropy for each grid
	"""

	shannon_entropy_list = []
	for index, row_pair in df.iterrows():
		flat_grid = []
		for sublist in row_pair['grid']:
			for item in sublist:
				flat_grid.append(item)
		#print ('flat grid')
		#print (flat_grid)
		e = entropy(flat_grid, base=2)
		shannon_entropy_list.append(e)
		#print (e)
		   # print ('entropy for session '+ str(row_pair['session']) +" tracker: " + str(row_pair['tracker']) +' is %.3f bits' % e)

	##Append entropy values to pairs-session_tracker structure
	df['entropy'] = shannon_entropy_list
	return df
	
	
def plot_charts_per_tracker(df_stops_transitions):
	"""This function generates Voronoi, ConvexHull and Delaunay charts in the folder "output_figures"
		per tracker.
		
		
	Parameters
	----------
	df_stops_transitions : Pandas Data Frame
		The output from _stopsAndTransitions.get_stops_and_transitions() function
		This is: a data frame of stops and transitions	

	Returns
	-------
	df
		returns a data frame with the following additional columns
			entropy - (float) indicating the calculated entropy for each grid
	"""
	print ("Plotting charts started")
	#Load room dimensions
	room_x= float(config.get('parameters','room_x'))
	room_y= float(config.get('parameters','room_y'))

	#Load position of the coordinate 0,0
	HorizonalZero= str(config.get('parameters','HorizonalZero'))
	VerticalZero= str(config.get('parameters','VerticalZero'))

	# Create structure with stops only
	stops = df_stops_transitions.loc[(df_stops_transitions['type'] == 'stop')][['session','phase','quantile','tracker','x','y','max_duration_sec']]

	##CREATE STRUCTURE THAT WILL HOLD THE DIAGRAMS PER PHASE
	distinct_sessions_partitions=stops.groupby(['session','tracker','phase']).size().reset_index().rename(columns={0:'count'})
	#distinct_sessions_partitions.head(6)


	#Create output folder for the diagramas if it doesn't exist
	Path("output_figures").mkdir(parents=True, exist_ok=True)



	# find min/max values for normalization
	minima = 0#stops['max_duration_sec'].min()
	maxima = stops['max_duration_sec'].max()

	arrays = []
	for index, row_pair in distinct_sessions_partitions.iterrows():
		##Extract sub-data frame (as an array - see .values) for the Session/tracker/phase
		#print (row_pair)
		sub_fixations_coordinates = stops.loc[(stops['session'] == row_pair['session']) & (stops['tracker'] == row_pair['tracker']) & (stops['phase'] == row_pair['phase'])][['x','y']].values
		
		#print ("SUB FIXATIONS COORDINATES")
		#print (sub_fixations_coordinates)

		durations = stops.loc[(stops['session'] == row_pair['session']) & (stops['tracker'] == row_pair['tracker']) & (stops['phase'] == row_pair['phase'])]['max_duration_sec'].values
		
		#print ("DURATIONS")
		#print (durations)

		##CREATE new array for the voroni chart
		arrays.append(sub_fixations_coordinates)
		if(len(sub_fixations_coordinates)>2):
			##CREATE VORONOI DIAGRAMS AND PLOT THEM
			vor = Voronoi(sub_fixations_coordinates)    
			voronoi_plot_2d(vor, show_vertices = False, line_colors='gray',
					line_width=2, line_alpha=0.6, point_size=4)
			

			if (HorizonalZero=='right'):
				plt.xlim(room_x,0)
			else:
				plt.xlim(0, room_x)
			if (VerticalZero=='down'):
				plt.ylim(0, room_y)
			else:
				plt.ylim(room_y, 0)
			plt.savefig('output_figures/Session_'+str(row_pair['session'])+'-Tracker_'+str(row_pair['tracker'])+'-Phase_'+str(row_pair['phase'])+'_VORONOI.png', transparent=True)

			
			
			##CREATE COLOURED VORONOI DIAGRAMS - MAX colour by
			# find min/max values for normalization
			#UNCOMMENT THE FOLLOWING TWO LINES TO CALCULATE THE LOCAL MAXIMA AND MINIMA FOR A PARTICULAR TRACKER EN PHASE
			minima = min(durations)
			print ('minima')
			print (minima)
			maxima = max(durations)
			print ('maxima')
			print (maxima)	
			
			# normalize chosen colormap
			norm = mpl.colors.Normalize(vmin=minima, vmax=maxima, clip=True)
			mapper = cm.ScalarMappable(norm=norm, cmap=cm.Blues_r)

			# plot Voronoi diagram, and fill finite regions with color mapped from speed value
			voronoi_plot_2d(vor, show_vertices = False, line_colors='gray',
					line_width=2, line_alpha=0.6, point_size=4)
			for r in range(len(vor.point_region)):
				region = vor.regions[vor.point_region[r]]
				if not -1 in region:
					polygon = [vor.vertices[i] for i in region]
					plt.fill(*zip(*polygon), color=mapper.to_rgba(durations[r]))
			if (HorizonalZero=='right'):
				plt.xlim(room_x,0)
			else:
				plt.xlim(0, room_x)
			if (VerticalZero=='down'):
				plt.ylim(0, room_y)
			else:
				plt.ylim(room_y, 0)
			plt.savefig('output_figures/Session_'+str(row_pair['session'])+'-Tracker_'+str(row_pair['tracker'])+'-Phase_'+str(row_pair['phase'])+'_VORONOI_COLOURED.png', transparent=True)
		   
			
			##CREATE CONVEX HULL DIAGRAMS AND PLOT THEM
			ch = ConvexHull(sub_fixations_coordinates)
			convex_hull_plot_2d(ch)
			
			if (HorizonalZero=='right'):
				plt.xlim(room_x,0)
			else:
				plt.xlim(0, room_x)
			if (VerticalZero=='down'):
				plt.ylim(0, room_y)
			else:
				plt.ylim(room_y, 0)
			plt.savefig('output_figures/Session_'+str(row_pair['session'])+'-Tracker_'+str(row_pair['tracker'])+'-Phase_'+str(row_pair['phase'])+'_CONVEXHULL.png', transparent=True)

			##CREATE DELAUNAY DIAGRAMS AND PLOT THEM
			delaunay = Delaunay(sub_fixations_coordinates)
			delaunay_plot_2d(delaunay)
			
			if (HorizonalZero=='right'):
				plt.xlim(room_x,0)
			else:
				plt.xlim(0, room_x)
			if (VerticalZero=='down'):
				plt.ylim(0, room_y)
			else:
				plt.ylim(room_y, 0)
			plt.savefig('output_figures/Session_'+str(row_pair['session'])+'-Tracker_'+str(row_pair['tracker'])+'-Phase_'+str(row_pair['phase'])+'_DELAUNAY.png', transparent=True)
			
	##Append grids list to pairs-session_tracker structure
	distinct_sessions_partitions['arrays'] = arrays
	#print (distinct_sessions_partitions)
	print ("CHARTS GENERATED IN output_figures folder")
	
