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
import os
os.environ['XPA_METHOD'] = "local"
import matplotlib.pyplot as plt
import matplotlib,imexam
import numpy as np
import imexamMOD
from imexamMOD import imexamine
from astropy.io import fits
import random
import math
import sys



# CONFIG VARIABLES
fileName = "AwiXg_orig.FITS"      # FITS-File to analyze
pointsToAnalyze = 110             # How many Points to analyze and plot
minFlux = 3000                    # Minimum Flux to continue searching
minDistance = 15                  # Minimum Manhattan distance to every old Point to accept new Point
verbose = False                   # Enable debug printout
plateDist = 700                   # Distance to plate in mm
holeSpacing = 50                  # Distance between points in mm


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
        verbose = bool(sys.argv[4])
    if argCount > 5:
        plateDist = sys.int(argv[5])
    if argCount > 6:
        holeSpacing = int(sys.argv[6])
except Exception as e:
    print("INVALID ARGUMENTS:", e)
    sys.exit()



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


fig, ax = plt.subplots()

realPoints = []

# generate real point position matrix
for x in range(-10, 11):
    xOffset = x*holeSpacing
    for y in range(-8, 9):
        yOffset = y*holeSpacing

        xDist = math.sqrt(plateDist**2 + xOffset**2)
        yDist = math.sqrt(plateDist**2 + yOffset**2)

        dirDist = math.sqrt(xDist**2 + yOffset**2)

        realX = math.degrees(math.atan(xOffset/yDist))
        realY = math.degrees(math.atan(yOffset/xDist))


        col = "red"
        scale = (50 / dirDist) * plateDist

        ax.scatter(realX, realY, c=col, s=scale,
               alpha=1.0, edgecolors='none')

        realPoints.append([realX, realY])

#ax.legend()
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
'width':[4,"Width of sky annulus in pixels"],
'subsky':[True,"Subtract a sky background?"],
'skyrad':[6,"Distance to start sky annulus is pixels"],
'radius':[4,"Radius of aperture for star flux"],
'zmag':[25.,"zeropoint for the magnitude calculation"],
'genplot': [True, 'Plot the apertures'],
'title': [None, 'Title of the plot'],
'scale': ['zscale', 'How to scale the image'],
'color_min': [None, 'Minimum color value'],
'color_max': [None, 'Maximum color value'],
'cmap': ['Greys', 'Matplotlib colormap to use']})

alreadyExamined = []
c = 0   # counts different points
p = 0   # counts every point
exactPoints = []
try:
    while c < pointsToAnalyze:
        maxCoords = ranked[p][0].split()
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
        if lowestDist > minDistance:            # New point discovered
            if verbose:
                print()
                print(lowestDist)
                print(x, y)

            exactX, exactY, flux = examine.aper_phot(x, y, data)
            if flux < minFlux:
                print("Breaking due to minFlux")
                break
            c += 1
            exactPoints.append([exactX, exactY])

            alreadyExamined.append([x, y])
            #_ = input("")
    print("search ended")
    print("analyzed", c, "points")
except TypeError as E:
    print(E)
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
    scale = 50
    col = getRandColor()
    col = 'red'
    ax.scatter(x, y, c=col, s=scale,
               alpha=0.5, edgecolors='none')

    x, y = realAngles[i][0], realAngles[i][1]
    scale = 50
    col = getRandColor()
    col = 'blue'
    ax.scatter(x, y, c=col, s=scale,
               alpha=0.5, edgecolors='none')

for i in range(len(conX)):
    plt.plot(conX[i], conY[i], c="blue")


#ax.legend()
ax.grid(True)

plt.show()


fig, ax = plt.subplots()

for i in range(len(exactAngles)):
    x, y = exactAngles[i][0], exactAngles[i][1]
    scale = (abs(angleErrors[i][0]) + abs(angleErrors[i][1])) * 10
    col = getRandColor()
    col = 'red'
    ax.scatter(x, y, c=col, s=scale,
               alpha=1.0, edgecolors='none')

plt.show()

print(len(exactPoints))
print(shape)

_ = input("press enter to exit")
