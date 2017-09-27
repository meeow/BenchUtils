# Author: Brandon Hong
# Pre-release

import numpy, math, logging, subprocess

# @param logfile_name: file name of logfile, logs to stdout if none specified
def init_logger(logfile_name=None):
	# Log to file
	if logfile_name:
		logging.basicConfig(filename=logfile_name, level=logging.INFO,
			format='%(message)s')
	# Log to stdout
	else:
		logging.basicConfig(level=logging.INFO, format='%(message)s')

# @param filename: path to target file
def open_file(filename):
	file = open(filename, 'r').read()

	if not file:
		logging.error('Unable to read/find input file or input file empty')

	return file

# @param file: input file object 
def split_by_line(file):
	return file.split('\n')

# @param row: one unformatted row of input file that has been split by line
# @return: list containing row data
def row_to_list(row):
	row = row.split(',')

	# Strip unnecessary whitespace
	row = [item.strip() for item in row]

	# Discard timestamp
	row = row[2:]

	return row

# @param file: input file that has been split by line
# @return: list containing column names
def get_col_names(file):
	col_names = ''

	# Set col_names to the line containing column names
	for line in file:
		if 'usage' in line:
			col_names = line
			# Do not parse the rest of the file unnecessarily
			break

	# Format output
	col_names = row_to_list(col_names)

	return col_names

# @param file: input file that has been split by line
# @return: formatted GPU name (2nd line of .hml file)
def get_GPU_name(file):
	GPU_info = file[1]

	# Discard timestamp
	GPU_info = GPU_info.split(',')[2].strip()

	return GPU_info

# @param row: one unformatted row of input file that has been split by line
# @return: 1 if row is valid, else 0
def is_valid_data_point(row, num_cols):
	# 3D application was not running at this point
	if 'N/A' in row or 'usage' in row or ', 0.000' in row or ',0.000' in row:
		return 0
	elif len(row_to_list(row)) != num_cols:
		return 0

	return 1

# @param row: one unformatted row of input file that has been split by line
# @param data_points: dictionary containing a list of data for each column name
# @param col_names: formatted list of column names from get_col_names()
def map_data_points_to_dict(row, data_points, col_names):
	position = 0
	num_cols = len(col_names)

	# Format row the same way as col_names was formatted
	row = row_to_list(row)

	# Insert row data into data_points dict
	while position < num_cols:
		if col_names[position] == 'CPU clock':
			pass # Frequency correction to be implemented
		data_points[col_names[position]].append(float(row[position])) 
		position += 1

	return data_points

# @param col_names: formatted list of column names from get_col_names()
# @return: dictionary containing keys of column names and empty list values
def init_data_points_dict(col_names):
	data_points = dict()

	for col in col_names:
		data_points[col] = list()

	return data_points

# Dump statistics to logfile
# @param statistics: complete dictionary containing performance statistics for 
#	every column
# @param log_to_file: dump output to file if not empty string
# @param include_only: only log specified columns, or log all columns if empty 
# @param desired_statistics: only log specified statistics, or log all 
#	statistics if empty 
def log_data_summary(statistics, include_only=[], desired_statistics=[]):
	column_keys = statistics.keys()
	statistic_types = statistics[column_keys[0]].keys()

	# Log all targeted columns and statistics
	for key in column_keys:
		if not include_only or key in include_only:
			for statistic in statistic_types:
				if not desired_statistics or statistic in desired_statistics:
					logging.info('{} - {:<25}: {}'.format(key, statistic, 
						round(statistics[key][statistic], 2)))

	# Add newline for formatting
	logging.info('\n')

def log_bench_parameters(GPU_name, logfile_name):
	# Log GPU name
	logging.info('{} - {}'.format(GPU_name, logfile_name))

# @param data_points: complete dictionary containing performance data
# @return: dictionary with each measured metric as a key and each corresponding
#	value being a sub-dictionary containing statistics
def calculate_statistics(data_points):
	stat_dict = dict()
	keys = data_points.keys()

	for key in data_points.keys():
		raw_data = data_points[key]
		stat_dict[key] = dict()

		# Calculate and store basic statistics
		stat_dict[key]['Mean'] = numpy.mean(raw_data)
		stat_dict[key]['Median'] = numpy.median(raw_data)
		stat_dict[key]['First_Quartile'] = numpy.percentile(raw_data, 25) 
		stat_dict[key]['Third_Quartile'] = numpy.percentile(raw_data, 75)
		stat_dict[key]['1_Pct_Low'] = numpy.percentile(raw_data, 1)
		stat_dict[key]['Standard_Deviation'] = numpy.std(raw_data)
		stat_dict[key]['Max'] = max(raw_data)
		stat_dict[key]['Min'] = min(raw_data)

		# Abstractions based on basic statistics
		# Percent that the mean is greater than the median
		stat_dict[key]['Mean_Median_Delta_Pct'] = 100 * ((stat_dict[key]['Mean'] 
			- stat_dict[key]['Median']) / stat_dict[key]['Median'])
		stat_dict[key]['Interquartile_Range'] = (stat_dict[key]['Third_Quartile']
			- stat_dict[key]['First_Quartile'])

	return stat_dict

# Discard values greater than (1.5x) IQR outside 1st or 3rd quartile
# @param data_points: complete dictionary containing performance data
# @param accept_outliers: list containing keys this function shall ignore
# @param threshold: number of times the IQR an outlier must lie outside the 
# 	first or third quartile.
#	Outlier - threshold = 1.5 | Extreme Outlier - threshold = 3.0
# @param upper_bound_only: only discard the high value outliers for these keys
# @return input dictionary, except with outlier values removed
def discard_outliers(data_points, accept_outliers=[], threshold=3.0,
	upper_bound_only=[]):
	keys = data_points.keys()

	processed_data_points = dict()

	first_quartile, third_quartile = 0, 0
	interquartile_range = 0

	for key in keys:
		# Skip columns that user specified not to filter
		if key in accept_outliers: 
			continue

		outliers, not_outliers = list(), list()

		# Calculate cutoffs for outlier status
		first_quartile = numpy.percentile(data_points[key], 25)
		third_quartile = numpy.percentile(data_points[key], 75)
		interquartile_range = third_quartile - first_quartile
		lower_threshold = first_quartile - (threshold * interquartile_range)
		higher_threshold = third_quartile + (threshold * interquartile_range)

		# Filter out outliers from non outliers
		for data_point in data_points[key]:
			if key in upper_bound_only:
				if data_point > higher_threshold:
					outliers.append(data_point)
				else: 
					not_outliers.append(data_point)
			elif data_point < lower_threshold or data_point > higher_threshold:
				outliers.append(data_point)
			else:
				not_outliers.append(data_point)

		# Print outliers (debug)
		#print 'Outliers found in', key, outliers
		#print 'Low bound, high bound: ', lower_threshold, higher_threshold

		# Save non outliers
		processed_data_points[key] = not_outliers

	return processed_data_points

# Run benchmarks which have CLI options
# [Under development]
# @param res: resolution to run tests at (string, W x H) 
#	e.g. '1920x1200'
def run_benches(res):
	def start_afterburner():
		pass

	# Unable to test this due to not having advanced edition
	def superposition_CLI():
		# Debug
		superposition_path = r'D:\Benches\GPU\Superposition Benchmark\bin'

		CLI = [superposition_path + '\superposition_cli','-api directx', 
			'-fullscreen 0', '-resolution ' + res, '-sound 1', '-mode default',
			'-iterations 1', '-quality extreme']

		return CLI

	CLI_queue = list()
	CLI_queue.append(superposition_CLI())

	for CLI in CLI_queue:
		instance = subprocess.Popen(CLI, shell=True)
		instance.communicate()
		print 'Ran', ' '.join(CLI)


def main():
	# <= User configure (This will be moved to config file once implemented)
	logfile_name = 'analysis.txt'

	input_filename = '10603G_stock_heaven.hml'
	#input_filename = '1050_stock_heaven.hml'
	#input_filename = '460_stock_heaven.hml'
	#input_filename = '10606G_stock_heaven.hml'
	input_filename = '4804G_stock_heaven.hml'
	input_filename = '4804G_stock_FFXIV.hml'
	input_filename = '1080ti_stock_FFXIV_1440p.hml'
	
	# Ignore outliers for these columns
	accept_outliers = ['FB usage', 'Memory usage', 'RAM usage', 'CPU usage']

	# Include only these columns in the logfile
	include_only = ['Framerate']

	# Only drop high outliers
	upper_bound_only = ['Framerate']

	# Only log these statistics
	desired_statistics = ['Mean', 'Median', '1_Pct_Low', 'Standard_Deviation',
		'Mean_Median_Delta_Pct']

	# Run automated benchmarks if user has them installed (skip if not found)
	# Feature untested and unfinished, recommend set to 0
	benchmark = 0

	# End user configure =>

	init_logger(logfile_name=logfile_name)

	# Run automated benchmarks
	if benchmark:
		run_benches('2560x1440')

	# Load input file
	input_file = open_file(input_filename)
	input_file = split_by_line(input_file)

	# Get column names and GPU name
	GPU_name = get_GPU_name(input_file)
	col_names = get_col_names(input_file)
	num_cols = len(col_names)

	# Create dict which will contain logged data
	data_points = init_data_points_dict(col_names)

	# Add all valid data to data_points dict
	for row in input_file:
		if is_valid_data_point(row, num_cols):
			data_points = map_data_points_to_dict(row, data_points, col_names)

	# Filter out outliers
	data_points = discard_outliers(data_points, accept_outliers, 
		upper_bound_only = ['Framerate'])

	# Calculate statistics
	statistics = calculate_statistics(data_points)

	# Report results
	log_bench_parameters(GPU_name, input_filename)
	log_data_summary(statistics, include_only=include_only, 
		desired_statistics=desired_statistics)

main()
