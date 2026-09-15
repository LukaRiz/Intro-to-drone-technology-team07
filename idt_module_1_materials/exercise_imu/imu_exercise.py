#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# IMU exercise
# Copyright (c) 2015-2024 Kjeld Jensen kjen@mmmi.sdu.dk kj@kjen.dk

##### Insert initialize code below ###################

## Uncomment the file to read ##
#fileName = 'data/imu_razor_data_roll_65deg.txt' # Task 3.2.2: calculate roll angle
#fileName = 'data/imu_razor_data_pitch_55deg.txt' # Task 3.2.1: calculate pitch angle
fileName = 'data/imu_razor_data_roll_65deg.txt' # Task 3.2.4: low-pass filtering
#fileName = 'data/imu_razor_data_roll_65deg.txt' # Task 3.2.4: low-pass filtering

## IMU type
#imuType = 'vectornav_vn100'
imuType = 'sparkfun_razor'

## Variables for plotting ##
showPlot = True
plotDataPitch = []
plotDataRoll = []
plotDataPitchFiltered = []
plotDataRollFiltered = []

## Initialize your variables here ##
myValue = 0.0
filterAlpha = 0.1
filteredPitch = None
filteredRoll = None






######################################################

# import libraries
from math import pi, sqrt, atan2
import matplotlib.pyplot as plt

# open the imu data file
f = open (fileName, "r")

# initialize variables
count = 0

# looping through file

for line in f:
	count += 1

	# split the line into CSV formatted data
	line = line.replace ('*',',') # make the checkum another csv value
	csv = line.split(',')

	# keep track of the timestamps 
	ts_recv = float(csv[0])
	if count == 1: 
		ts_now = ts_recv # only the first time
	ts_prev = ts_now
	ts_now = ts_recv

	if imuType == 'sparkfun_razor':
		# import data from a SparkFun Razor IMU (SDU firmware)
		acc_x = int(csv[2]) / 1000.0 * 4 * 9.82;
		acc_y = int(csv[3]) / 1000.0 * 4 * 9.82;
		acc_z = int(csv[4]) / 1000.0 * 4 * 9.82;
		gyro_x = int(csv[5]) * 1/14.375 * pi/180.0;
		gyro_y = int(csv[6]) * 1/14.375 * pi/180.0;
		gyro_z = int(csv[7]) * 1/14.375 * pi/180.0;

	elif imuType == 'vectornav_vn100':
		# import data from a VectorNav VN-100 configured to output $VNQMR
		acc_x = float(csv[9])
		acc_y = float(csv[10])
		acc_z = float(csv[11])
		gyro_x = float(csv[12])
		gyro_y = float(csv[13])
		gyro_z = float(csv[14])
	 		
	##### Insert loop code below #########################

	# Variables available
	# ----------------------------------------------------
	# count		Current number of updates		
	# ts_prev	Time stamp at the previous update
	# ts_now	Time stamp at this update
	# acc_x		Acceleration measured along the x axis
	# acc_y		Acceleration measured along the y axis
	# acc_z		Acceleration measured along the z axis
	# gyro_x	Angular velocity measured about the x axis
	# gyro_y	Angular velocity measured about the y axis
	# gyro_z	Angular velocity measured about the z axis

	## Task 3.2.4: low-pass filter pitch and roll angles ##
	pitch = atan2 (acc_y, sqrt (acc_x**2 + acc_z**2))
	roll = atan2 (-acc_x, sqrt (acc_y**2 + acc_z**2))
	if filteredPitch is None:
		filteredPitch = pitch
		filteredRoll = roll
	else:
		filteredPitch = filterAlpha*pitch + (1-filterAlpha)*filteredPitch
		filteredRoll = filterAlpha*roll + (1-filterAlpha)*filteredRoll

	plotDataPitch.append (pitch*180.0/pi)
	plotDataRoll.append (roll*180.0/pi)
	plotDataPitchFiltered.append (filteredPitch*180.0/pi)
	plotDataRollFiltered.append (filteredRoll*180.0/pi)

	######################################################

# closing the file	
f.close()

# show the plot
if showPlot == True:
	plt.plot(plotDataRoll, alpha=0.35, label='Raw roll')
	plt.plot(plotDataRollFiltered, label='Filtered roll')
	plt.xlabel('Sample')
	plt.ylabel('Roll angle (degrees)')
	plt.title('Low-pass filtering of roll angle')
	plt.legend()
	plt.grid(True)
	plt.savefig('pics/imu_exercise_low_pass_filter_plot.png')
	plt.show()


