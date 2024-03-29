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




CURRENT SETTINGS:
                     Min distance between points| \/Enable Debugging
python3 pointDetect.py raspi/rgb158.fits 224 10 7 True
               Filename^  Number of points^   ^Min Flux threshold
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

ignoreBreakpoints = False


# override Presets with commandline Args:
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
    """Experimental, doesnt work"""
    xx = int(x)
    yy = int(y)
    chunk = data[yy-r : yy+r, xx-r : xx+r]
    x, y = photutils.centroid_2dg(x, y, chunk)



def pythDist(a, b):
    """Calculates Pythagorean distance"""
    dist = math.sqrt(a**2 + b**2)
    return dist

def getRandColor():
    """Returns random Hex Color String"""
    r = lambda: random.randint(0,255)
    return ('#%02X%02X%02X' % (r(),r(),r()))

def pxToDeg(px):
    """Converts Pixel Position to Angle, assuming Equiangular projection"""
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
    """Starts interactive prompt for debugging"""
	global ignoreBreakpoints
	if not ignoreBreakpoints:
		while True:
			userIn = input(">>> ")
			if userIn == "c" or userIn == "continue" or userIn == "":
				break
			if userIn == "k" or userIn == "kill":
				sys.exit()
            if userIn == "h" or userIn == "help":
                print("Press Enter or enter c or continue to exit the prompt and continue the program or enter k or kill to stop the program")
			else:
				try:
					exec(userIn)
				except Exception as e:
					print("Fail", e)

def getPointPos(plateDist, xOffset, yOffset):
    """Calculates the Angles of a point given the Points position"""
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

# Generate Matrix and add Custom points (Orientation markers)
realPoints = getPointMatrix(plateDist, holeSpacing)
x, y = getPointPos(plateDist, -25, -25)
realPoints.append([x, y, 15])
x, y = getPointPos(plateDist, -25, 25)
realPoints.append([x, y, 15])
x, y = getPointPos(plateDist, 25, -25)
realPoints.append([x, y, 15])

#Plot all points that should be measured
fig, ax = plt.subplots()

for i in range(len(realPoints)):
    x, y = realPoints[i][0], realPoints[i][1]
    scale = realPoints[i][2]
    col = getRandColor()
    col = "red"
    ax.scatter(x, y, c=col, s=scale,
               alpha=1.0, edgecolors='none')

ax.grid(True)
plt.show()

#_=input()


hdul = fits.open(fileName)
data = hdul[0].data

shape = data.shape

dataList = data.tolist()

points = {}

for x in range(len(dataList)):
    for y in range(len(dataList[0])):
        points[str(x) + " " + str(y)] = dataList[x][y]

ranked = []
for key, value in sorted(points.items(), key=lambda item: item[1]):
    ranked.append([key, value])

ranked.reverse()

if verbose:
    for i in range(1000):
        print(ranked[i])


    print(data)

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

alreadyExamined = []
c = 0   # counts different points
p = 0   # counts every checked pixel
exactPoints = []
try:
    while c < pointsToAnalyze:
        maxCoords = ranked[p][0].split()
        print("p:", p)
        p += 1

        x = int(maxCoords[1])
        y = int(maxCoords[0])
        lowestDist = 1000
        for point in alreadyExamined:
            dist = abs(point[0] - x) + abs(point[1] - y)
            if verbose:
                #print("d", dist)
                pass
            if dist < lowestDist:
                lowestDist = dist
        print("lowest Dist:", lowestDist)
        if lowestDist > minDistance: # and 10 < x < 150 and 10 < y < 110:            # New point discovered
            print("==== NEW POINT ====")
            if verbose:
                print(lowestDist)
                print(dataList[y][x])
                print("Position", x, y)
            try:
                exactX, exactY, flux = examine.aper_phot(x, y, data)
                success = True
                breakPoint()
            except Exception as e:
                print("aper_phot failed...")
                traceback.print_exc()
                exactX, exactY, flux = x, y, 20
                success = False
                breakPoint()
            if flux < minFlux:
                print("Breaking due to minFlux")
                break
            c += 1
            exactPoints.append([exactX, exactY, success])

            alreadyExamined.append([exactX, exactY])
            #_ = input("")
            print("==== END POINT ====")
        else:
            print("pos:", x, y)
    print("search ended")
    print("analyzed", c, "points")
except TypeError as e:
    print(e)
    print("An Error occured, you may need to edit imexam to return the Point position for aper_phot")


exactAngles = [] # measured Angles
angleErrors = [] # difference to real angles
realAngles = []  # real Angles

w = shape[1] # get width
h = shape[0] # get height

print(w, h)

conX = []
conY = []

for point in exactPoints:
    xAngle = pxToDeg(point[0] - w/2) # get measured angle on x Axis
    yAngle = pxToDeg(point[1] - h/2) # get measured angle on y Axis
    targetX, targetY = getNearestHole(xAngle, yAngle) # get real angle on x
    angleErrors.append([xAngle-targetX, yAngle-targetY]) # save difference between measured and real
    exactAngles.append([xAngle, yAngle]) # save measured angles
    realAngles.append([targetX, targetY]) # save real angles
    conX.append([targetX, xAngle])
    conY.append([targetY, yAngle])




fig, ax = plt.subplots()

for i in range(len(realPoints)):
    x, y = realPoints[i][0], realPoints[i][1]
    scale = 40
    col = getRandColor()
    col = 'green'
    ax.scatter(x, y, c=col, s=scale,
               alpha=0.5, edgecolors='none')


for i in range(len(exactAngles)):
    x, y = exactAngles[i][0], exactAngles[i][1]
    scale = 20
    col = getRandColor()
    col = 'red'
    ax.scatter(x, y, c=col, s=scale,
               alpha=1.0, edgecolors='none')

    x, y = realAngles[i][0], realAngles[i][1]
    scale = 50
    col = getRandColor()
    col = 'blue'
    ax.scatter(x, y, c=col, s=scale,
               alpha=0.5, edgecolors='none')

for i in range(len(conX)):  #Add connection lines from measured to real points
    plt.plot(conX[i], conY[i], c="blue")


#ax.legend()
ax.grid(True)
plt.show()


fig, ax = plt.subplots()

for i in range(len(exactAngles)):
    x, y = exactAngles[i][0], exactAngles[i][1]
    scale = (abs(angleErrors[i][0]) + abs(angleErrors[i][1])) * 30
    col = getRandColor()
    col = 'red'
    ax.scatter(x, y, c=col, s=scale,
               alpha=1.0, edgecolors='none')

ax.grid(True)
plt.show()


#Plot all the Points that have been measured, green means successful aper_phot, red means failure
fig, ax = plt.subplots()

for i in range(len(exactPoints)):
    x, y = exactPoints[i][0], exactPoints[i][1]
    scale = 30
    col = getRandColor()
    if exactPoints[i][2] == True:
    	col = "green"
    else:
    	col = 'red'
    ax.scatter(x, y, c=col, s=scale,
               alpha=1.0, edgecolors='none')

ax.grid(True)
plt.show()

print(len(exactPoints))
print(shape)

_ = input("press enter to exit")    #Keep plots from closing after program is finished
