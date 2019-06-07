import numpy as np
from astropy.io import fits
import sys

if len(sys.argv) > 1:	# check if command line argument present
	filename = sys.argv[1] # use first argument as filename
	if len(sys.argv) > 2:
		outputFilename = sys.argv[2]
	else:
		outputFilename = filename
else:
	print("Enter Filename")
	filename = input(">>> ")	# get filename from user input

if filename[-4:] == ".txt":		# if .txt file extension present
	filename = filename[:-4]	# remove file extension

print("Using File", filename + ".txt")		# debug output/confirmation

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
except FileNotFoundError:	# If file an not be opened
	print("ERROR: File " + filename + ".txt not found")
except Exception as e:		# unknown errors
	print("ERROR: " + str(e))
