# Author: Brandon Hong
# Pre-release

import numpy

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

def print_data(data_points):
	print 'Mean', numpy.mean(data_points['Framerate'])
	print 'Median', numpy.median(data_points['Framerate'])
	print '10th Percentile', numpy.percentile(data_points['Framerate'], 10)
	print '90th Percentile', numpy.percentile(data_points['Framerate'], 90)
	print 'Min', min(data_points['Framerate'])
	print 'Max', max(data_points['Framerate'])

def main():
	input_filename = 'HardwareMonitoring.hml'

	# Load input file
	input_file = open_file(input_filename)
	input_file = split_by_line(input_file)

	# Get column names
	col_names = get_col_names(input_file)
	num_cols = len(col_names)

	# Create dict which will contain logged data
	data_points = init_data_points_dict(col_names)

	# Add all valid data to data_points dict
	for row in input_file:
		if is_valid_data_point(row, num_cols):
			data_points = map_data_points_to_dict(row, data_points, col_names)

	print_data(data_points)

main()