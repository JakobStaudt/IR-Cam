# https://imexam.readthedocs.io/en/latest/index.html#
"""
import os
os.environ['XPA_METHOD'] = "local"
import matplotlib,imexam
import numpy as np

myWin = imexam.connect()

myWin.load_fits('test.fits')
myWin.imexam()


# array = np.ones((100,100), dtype=np.float) * np.random.rand(100)
# myWin.view(array)
# myWin.zoom()  # by default, zoom-to-fit, or give it a scale factor
"""

"""
CURRENT PROBLEMS:

aper_phot / gauss_center throws ValueError: zero-size array to reduction operation maximum which has no identity
if point is too far to the lower border of the image (distance to border < delta)
and ValueError: operands could not be broadcast together with shapes (placeholder,ph) (ph,ph)
if point is too close to the upper border of the image (distance to border < delta)
Current workaround:
Dont use Gaussian fit in these cases and instead use the position of the brightest Pixel
"""




import os
os.environ['XPA_METHOD'] = "local"
import matplotlib.pyplot as plt
import matplotlib,imexam
import numpy as np
import imexam
from imexam import imexamine
from astropy.io import fits
import random
import math
import sys
import traceback
import photutils



# CONFIG VARIABLES
fileName = "AwiXg_orig.FITS"      # FITS-File to analyze
pointsToAnalyze = 110             # How many Points to analyze and plot
minFlux = 3000                    # Minimum Flux to continue searching
minDistance = 15                  # Minimum Manhattan distance to every old Point to accept new Point
verbose = False                   # Enable debug printout
plateDist = 815                   # Distance to plate in mm
holeSpacing = 50                  # Distance between points in mm

ignoreBreakpoints = True


# override with commandline Args:
argCount = len(sys.argv)

try:
    if argCount > 1:
        fileName = sys.argv[1]
    if argCount > 2:
        pointsToAnalyze = int(sys.argv[2])
    if argCount > 3:
        minFlux = int(sys.argv[3])
    if argCount > 4:
        minDistance = int(sys.argv[4])
    if argCount > 5:
        verbose = bool(sys.argv[5])
    if argCount > 6:
        plateDist = int(sys.argv[6])
    if argCount > 7:
        holeSpacing = int(sys.argv[7])
except Exception as e:
    print("INVALID ARGUMENTS:", e)
    sys.exit()


def centroidFinder(x, y, data, r):
    verbose = True
    xx = int(x)
    yy = int(y)
    ox = x
    oy = y
    chunk = data[yy-r : yy+r, xx-r : xx+r].tolist()
    if verbose:
        print(chunk)
    xSum = 0
    ySum = 0
    pixCount = 0
    for y in range(len(chunk)):
        for x in range(len(chunk[0])):
            if verbose:
                print(chunk[y][x], end=" ")
            ySum += y*chunk[y][x]
            xSum += x*chunk[y][x]
            pixCount += chunk[y][x]
        if verbose:
            print()
    #print(pixCount)
    yPos = ySum / pixCount
    xPos = xSum / pixCount

    print(yPos, xPos)

    yPos = oy - r + yPos
    xPos = ox - r + xPos

    return xPos, yPos


def  pythDist(a, b):
    dist = math.sqrt(a**2 + b**2)
    return dist

def getRandColor():
    r = lambda: random.randint(0,255)
    return ('#%02X%02X%02X' % (r(),r(),r()))

def pxToDeg(px):
    deg = px * 0.35625   # multiply pixel position with degrees per pixel
    return deg

def getNearestHole(measuredX, measuredY):
    '''Determines the closest real hole position to a observed point'''
    smallestDist = 1000000
    for point in realPoints:
        dist = math.sqrt((point[0]-measuredX)**2 + (point[1]-measuredY)**2)
        if dist < smallestDist:
            nearestPoint = point
            smallestDist = dist
    realX, realY = nearestPoint[0], nearestPoint[1]
    return realX, realY

def breakPoint():
	global ignoreBreakpoints
	if not ignoreBreakpoints:
		while True:
			userIn = input(">>> ")
			if userIn == "c" or userIn == "continue" or userIn == "":
				break
			if userIn == "k" or userIn == "kill":
				sys.exit()
			else:
				try:
					exec(userIn)
				except Exception as e:
					print("Fail", e)

def getPointPos(plateDist, xOffset, yOffset):
    xDist = math.sqrt(plateDist**2 + xOffset**2)
    yDist = math.sqrt(plateDist**2 + yOffset**2)

    dirDist = math.sqrt(xDist**2 + yOffset**2)

    realX = math.degrees(math.atan(xOffset/yDist))
    realY = math.degrees(math.atan(yOffset/xDist))

    return realX, realY


def getPointMatrix(plateDist, holeSpacing):
	"""Generate real position matrix"""
	realPoints = []
	for x in range(-8, 9):
	    xOffset = x*holeSpacing
	    for y in range(-6, 7):
	        yOffset = y*holeSpacing

	        xDist = math.sqrt(plateDist**2 + xOffset**2)
	        yDist = math.sqrt(plateDist**2 + yOffset**2)

	        dirDist = math.sqrt(xDist**2 + yOffset**2)

	        realX = math.degrees(math.atan(xOffset/yDist))
	        realY = math.degrees(math.atan(yOffset/xDist))

	        realPoints.append([realX, realY, 30])
	return realPoints

hdul = fits.open(fileName)
data = hdul[0].data

shape = data.shape

dataList = data.tolist()


examine = imexamine.Imexamine()
"""
examine.column_fit(x, y,data)
"""
examine.set_aper_phot_pars({'function':["aperphot",],
'center':[True,"Center the object location using a Gaussian2D fit"],
'width':[2,"Width of sky annulus in pixels"],
'subsky':[True,"Subtract a sky background?"],
'skyrad':[3,"Distance to start sky annulus is pixels"],
'radius':[2,"Radius of aperture for star flux"],
'zmag':[25.,"zeropoint for the magnitude calculation"],
'genplot': [True, 'Plot the apertures'],
'title': [None, 'Title of the plot'],
'scale': ['zscale', 'How to scale the image'],
'color_min': [None, 'Minimum color value'],
'color_max': [None, 'Maximum color value'],
'cmap': ['Greys', 'Matplotlib colormap to use']})
x, y = 80, 60
for i in range(10):
    x, y, _ = examine.aper_phot(x, y, data)
    print(x, y)

x, y = 79, 60
for i in range(1):
    x, y = centroidFinder(x, y, data, 10)
    print(x, y)

_ = input("")