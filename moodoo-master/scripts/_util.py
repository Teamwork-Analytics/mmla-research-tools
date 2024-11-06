"""Utility scripts

This script provides general functions  
i) to open and read files and create Pandas Data Frames

This script requires that `pandas` be installed within the Python
environment you are running this script in.

This file can also be imported as a module and contains the following
functions:

    * sampling_and_interpolating - for (down) smapling and interpolating a positioning dataset
    * calculate_rotation - for adding a new column Rotation in degrees if the dataset contains rotation information in radians
	* add_phases - for adding a new column with Phase information based on a PHASES Data Frame
	* add_quantiles - for adding a new column with "quantile" information: quantiles are artifitial divisions of data points within 
	a phase in X number of equal parts according to their timestamp
"""

from PyQt5.QtWidgets import QFileDialog
import pandas as pd 

def open_csv_gui():
	"""This function opens a CSV file selected by a user using an open dialogue. 
		Timestamps MUST be formatted as "%d/%m/%Y %H:%M:%S" 	
			
	Returns
	-------
	df
		a data frame with the content of the CSV file

	"""
	source_file=gui_open_file()
	mydateparser = lambda x: pd.datetime.strptime(x, "%d/%m/%Y %H:%M:%S")
	df = pd.read_csv(source_file, low_memory=False, parse_dates=['timestamp'], date_parser=mydateparser)
	return df

def open_csv(source_file, list_of_date_columns):
	"""This function opens a CSV file selected by a user using an open dialogue. 
		Timestamps MUST be formatted as "%d/%m/%Y %H:%M:%S"
	Parameters
	----------
	source_file : string
		full filename of the csv file to be opened: e.g. "D:/moodoo/Dataset_Study-layers-2019-2_PHASES_2019_FIXED.csv"
	list_of_date_columns: list of strings
		list of names of columns with datetime data: e.g.  ['start', 'end']. Timestamps MUST be formatted as "%d/%m/%Y %H:%M:%S"
			
	Returns
	-------
	df
		a data frame with the content of the CSV file

	"""

	mydateparser = lambda x: pd.datetime.strptime(x, "%d/%m/%Y %H:%M:%S")
	df = pd.read_csv(source_file, low_memory=False, parse_dates=list_of_date_columns, date_parser=mydateparser)
	return df


def gui_open_file(dir=None):
	"""This function enables the user to select a file via a dialog and return the file name
		Timestamps MUST be formatted as "%d/%m/%Y %H:%M:%S"
	Parameters
	----------
	dir : string
		directory where to pick a file (optional)
		
	Returns
	-------
	fname
		filename picked by the user

	"""
	if dir is None: dir ='./'
	fname = QFileDialog.getOpenFileName(None, "Select data file...", 
				dir, filter="All files (*);; SM Files (*.sm)")
	return fname[0]
	

