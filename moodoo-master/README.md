# How to install 

### Project dependencies

1. python 3.8
2. pip3

How to install python3.8
- For mac `brew install python@3.8`

Create virtual environment 
- Using pycharm to create virtual environment


Install pip
`curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py`
`python get-pip.py`

## Install dependencies

`pycairo` library needs`pkg-config` and `cairo` instaled

### For mac 

Install `pkg-congig`
- `brew install pkg-config`

Install `Cairo`
- `brew install --cc=clang cairo`

Install pip requirements 
- `pip3 install -r requirements.txt`


### How to run script

To run all the files using the test dataset run the script test\demoMAIN.py:
`python demoMAIN.py --all`
(NOTE: It can take some time to complete the analysis)

To test the functions in each script and generate intermediate output files, 
run the files l demo1-5 in the following order:
	test\demo1_preprocessing.py
	test\demo2_stopsAndTransitions.py
	test\demo3_fixedPoints.py
	test\demo4_entropy.py
	test\demo5_generateMetrics.py
	
The file info.ini contains important parameters that are used by the scripts.

To analyse your own data, example files are in the folder test\Merged dataset 2018-2019\. 
Please, format your data using these samples as a reference. 
This folder contains the following csv files:

	demo_dataset_2019.csv - which contains the indoor positioning datapoints. 
		The positioning system POZYX was used to generate this file but similar x and y positions can be formatted 
		according to this example. Refer to the script _preprocessing.py for a description of the columns of this file.
	
	demo_fixed_points_2019.csv - which contains datapoints of fixed objects. These can be of type 'student' 
		(used, for example, to refer to tables where there are students and tables don't move) or 'zones'
		(used, for example, to point particular classroom areas or objects such as whiteboards, benches, the 
		teacher's computer, etc).
		
	demo_phases_2019.csv - which contains information about the phases of each session in the dataset. Phases are
		used to trim the dataset to consider only datapoints within phases and to generate metrics per phase. 
		If there are no phases in your dataset, at least, create one phase per session indicating the 
		beginning and the end of such session (e.g. the first and last datapoint of each session).  
		

