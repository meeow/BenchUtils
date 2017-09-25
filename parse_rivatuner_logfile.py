# Author: Brandon Hong
# Pre-release

import numpy, math

# @param filename: path to target file
def open_file(filename):
	return open(filename, 'r').read()

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

# @param data_points: complete dictionary containing performance data
def print_data(data_points):
	FPS_mean = numpy.mean(data_points['Framerate'])
	FPS_median = numpy.median(data_points['Framerate'])
	print 'Mean FPS', FPS_mean
	print 'Median FPS', FPS_median
	print 'Mean - Median FPS pct differential', (FPS_mean - FPS_median)/FPS_mean
	print '10th Pct FPS', numpy.percentile(data_points['Framerate'], 10)
	print '90th Pct FPS', numpy.percentile(data_points['Framerate'], 90)
	
# Discard values greater than (1.5x) IQR outside 1st or 3rd quartile
# @param data_points: complete dictionary containing performance data
# @param accept_outliers: list containing keys this function shall ignore
# @param threshold: number of times the IQR an outlier must lie outside the 
# 	first or third quartile
# @param upper_bound_only: only discard the high value outliers for these keys
# @return input dictionary, except with outlier values removed
def discard_outliers(data_points, accept_outliers, threshold=1.5,
	upper_bound_only=[]):
	keys = data_points.keys()

	processed_data_points = dict()

	first_quartile, third_quartile = 0, 0
	interquartile_range = 0

	for key in keys:
		if key in accept_outliers: continue

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

		# Print outliers
		#print 'Outliers found in', key, outliers
		#print 'Low bound, high bound: ', lower_threshold, higher_threshold

		# Save non outliers
		processed_data_points[key] = not_outliers

	return processed_data_points

def main():
	input_filename = '10603G_stock_heaven.hml'
	input_filename = '1050_stock_heaven.hml'
	input_filename = '460_stock_heaven.hml'
	input_filename = '10606G_stock_heaven.hml'
	input_filename = '4804G_stock_heaven.hml'
	
	accept_outliers = ['FB usage', 'Memory usage', 'RAM usage', 'CPU usage']

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

	print GPU_name
	print '[ Before high outliers discarded ]'
	print_data(data_points)

	# Filter out outliers
	data_points = discard_outliers(data_points, accept_outliers, 
		upper_bound_only = ['Framerate'])

	print '[ After high outliers discarded ]'
	print_data(data_points)

main()
