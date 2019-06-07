import numpy as np
from astropy.io import fits
import sys
import os


def fileToFits(filename, outputFilename):
	try:
		with open(filename + ".txt") as file:
			file = file.readlines()	# Read input file lines into array "file"

		total = []

		for line in file:		# go over each line
			strLine = line.strip().split(" ")	# split line into one string with float value per pixel
			floatLine = []
			for val in strLine:					# go over each pixel
				floatLine.append(float(val))   # convert each pixel value string to float and append to line array
			total.append(floatLine)		# append current line array to total array

		ntotal = np.asarray(total)	# create NumPy-Array out of total array (list)

		print("converted to numpy array")
		print(ntotal.shape)		# print image dimensions

		hdu = fits.PrimaryHDU(ntotal)
		hdu.writeto(outputFilename + '.fits')		# write data to fits file with input filename and fits extension

		print("wrote fits")
		return 0
	except FileNotFoundError:	# If file an not be opened
		print("ERROR: File " + filename + ".txt not found")
		return 1
	except Exception as e:		# unknown errors
		print("ERROR: " + str(e))
		return 1


isFile = False

selection = 0

if len(sys.argv) > 1:	# check if command line argument present
	filename = sys.argv[1] # use first argument as filename
	if len(sys.argv) > 2:
		selection = sys.argv[2]
	outputFilename = filename
else:
	print("Enter Filename or Directory")
	filename = input(">>> ")	# get filename from user input

if filename[-4:] == ".txt":		# if .txt file extension present
	filename = filename[:-4]	# remove file extension
	isFile = True
	print("Using File", filename + ".txt")		# debug output/confirmation
	fileToFits(filename, filename)
else:
	fileList = []
	for file in os.listdir(filename):
	    if file.endswith(".txt"):
	        fileList.append(os.path.join(filename, file)[:-4])
	if selection == 0:
		print("Found", len(fileList), "Files")
		print("Select an option:")
		print("  1) Convert all files")
		print("  2) Select files individually")
		selection = input(">>> ")
	filesToConvert = []
	if selection == "1":
		filesToConvert = fileList
	if selection == "2":
		for file in fileList:
			select = input(file + ">>> ")
			if select == "y":
				print("converting file", file + ".txt")
				filesToConvert.append(file)
			if select == "e":
				break

	print("Confirm selected Files:")
	for file in filesToConvert:
		print(file)
	print("Enter y to confirm selection")
	if input(">>> ") == "y":
		errorCount = 0
		print("Converting files...")
		for file in filesToConvert:
			errorCount += fileToFits(file, file)
		print("Converted Files,", errorCount, "Errors")
	else:
		print("Aborted")

