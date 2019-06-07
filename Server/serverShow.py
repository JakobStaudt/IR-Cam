#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
   Small Raspberry Pi based viewer for the FLIR Lepton-3
'''

from PyQt4 import QtCore, QtGui
from PyQt4.QtGui import QDialog
from PyQt4.uic import loadUi

import numpy as np
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

import socket

import subprocess

import datetime,time, sys

#import cv2

import re

failures = 0

start = time.time()

def normalize(a):
    maxVal = np.amax(a)
    minVal = np.amin(a)
    vRange = maxVal - minVal
    for x in np.nditer(a, op_flags=["readwrite"]):
        r = (x-minVal) / (vRange / 255.0)
        #print r
        x[...] = r
    return a


###################################################################################################

class MyMplCanvas(FigureCanvas):
    """A matplotlib canvas for presenting graphics"""

    def __init__(self, parent=None, width=5, height=4, dpi=100,frameon=False):

        fig = Figure(figsize=(width, height), dpi=dpi)
        # self.axes = fig.add_subplot(111)
        self.axes = fig.add_axes([0, 0, 1, 1])
        self.axes.axis('off')
        # We want the axes cleared every time plot() is called

        self.compute_initial_figure()

        #
        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

        def compute_initial_figure(self):
            pass

###################################################################################################

class StaticMplCanvas(MyMplCanvas):
    """
       Display images and Plots - Create one instance for each plot / image

       scatterXY  - An XY scatter plot
       linePlot   - An XY line plot *** on EXISTING scatterXY plot !
       dispImg    - Display an image
       annotatePt - Place text at specified location

       This routine was adapted from All-Sky-Cam/ASP.py - TMH 20SEP17
    """

    def compute_initial_figure(self):
        pass

    #-------------------------------------------------------------------------------------------------#

    def scatterXY(self,x,y,plotLimits,xLab,yLab,title):     #Update XY Plot...Note Xo,Zo are -26.26,3.08)
        """
           Generate a scatter plot of x,y with the supplied limits, labels and title
        """
        x1,x2,y1,y2 = plotLimits[0],plotLimits[1],plotLimits[2],plotLimits[3]   # Extract plot limits
        self.axes.clear()
        self.axes.axis([x1,x2,y1,y2])  # Plot limits

        self.axes.scatter(x, y,marker="o")

        self.axes.set_xlabel(xLab, fontsize=14)
        self.axes.set_ylabel(yLab, fontsize=14)

        # self.axes.text((x1+x2)/2.0, y1 + 0.9(y2-y1), title,horizontalalignment='center',fontsize=20,transform = self.axes.transAxes)

        self.axes.set_title(title, fontsize=18,loc='center')

        self.draw()

    #-------------------------------------------------------------------------------------------------#

    def linePlot(self,xL,yL):
        """ Generate a line plot on the existing self.axes.
        """
        self.axes.plot(xL,yL)
        self.draw()

    #-------------------------------------------------------------------------------------------------#

    def plotCross(self,xL,yL):
        """ 
            Places a (black) cross at xL,yL in existing plot.
        """
        self.axes.plot(xL,yL,'k+')
        self.draw()

    #-------------------------------------------------------------------------------------------------#

    def dispImg(self,im,clut,autoscale=True,cuts=[0.0,1.0]):
        '''
           Display the supplied image (which is a numpy array!)
           Note that if autoscale is not true, you must supply "cuts = [min,max]"
        '''
        self.axes.cla()

        if autoscale:

            mn,mx = np.min(im),np.max(im)      # Min, max image values
            av = 0.5*(mn+mx)                   #   and average

            minC = av - 1.1 * (av-mn)          # Need to stretch, even across zero
            maxC = av + 1.1 * (mx-av)

            self.axes.imshow(im,clim=(minC,maxC),cmap=clut, interpolation='none')            # Autoscale

        else:
            self.axes.imshow(im,clim=(cuts[0],cuts[1]),cmap=clut, interpolation='none')     # Can use e.g. clim=(0.2, 0.5), cmap="gray" to enhance

        self.axes.axis('off')   # Suppress tickmarks, numbers, etc.

        self.draw()

    #-------------------------------------------------------------------------------------------------#

    def annotatePt(self,txt,xyPos,txtPos):
        """ Annotates the plot with the text txt at position
            xyPos. The text appears at txtPos (presumably
            offset somewhat). Note that xyPos and txtPos are
            tuples, created for example, by xyPos = (x,y)
        """
        self.axes.annotate(txt,xy=xyPos,xytext=txtPos,size=10)
        self.draw()

###################################################################################################

class getImThread(QtCore.QThread):

    '''
        Thread which returns one FLIR image at the appropriate rate.

        The variable camConnected = True if the FLIR is hooked up. Otherwise,
        the routine spits back the splash image with added noise.

    '''

    def __init__(self):
        QtCore.QThread.__init__(self)

        self.iTime = 1.0              # Default image rate is 1 per sec
        self.running = True           # Whether we are waiting for commands

        self.camConnected = True      # Whether the FLIR is hooked up
        self.img = []

    def __del__(self):
        self.wait()

    def capture(self,flip_v, device):
      '''
          Capture routine from here:


      '''
      with Lepton3(device) as l:
        a,_ = l.capture()
      if flip_v:
        #cv2.flip(a,0,a)
        pass

      a = normalize(a)
      #cv2.normalize(a, a, 0, 65535, cv2.NORM_MINMAX)
      #np.right_shift(a, 8, a)
      #return np.uint8(a)

      return a


    def run(self):
        global failures
        global start

        imgStr = ""

        HOST = ''	# Symbolic name meaning all available interfaces
        PORT = 8888	# Arbitrary non-privileged port
        
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print 'Socket created'
        
        #Bind socket to local host and port
        try:
                s.bind((HOST, PORT))
        except socket.error as msg:
                print 'Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
                sys.exit()
                
        print 'Socket bind complete'
        
        #Start listening on socket
        s.listen(10)
        while True:

                conn, addr = s.accept()

                imgStr = ""
                imgList = ""
        
                while self.running:                 # We are waiting for a name to start
        
                        #Receiving from client
                        data = conn.recv(1024)
                        if "s" in data:			# New Frame begins
                            imgStr = ""		        # Reset Frame Buffer
                
                        imgStr += data			# Append newest message


                
                        if "e" in data:
                                try:
                                        print "got image, current error count = " + str(failures)
                                        imgStr = re.search("s(.*)e", imgStr).group(1)		# Remove "s" and "e" markers
                                        exec("img = " + imgStr)		# convert string to list (hacky)
                                        #print img[0][0]			# print 1st entry (debug)
                                        self.img = np.array(img)
                                        self.emit( QtCore.SIGNAL('GotOne(QString)'), datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                                        imgStr = ""
                                except:
                                        print "decryptError"
                                        print "failure after " + str(time.time()-start) + " seconds"
                                        failures += 1
                
                        if not data: 
                            break

        return

###################################################################################################

class AppWin(QtGui.QMainWindow):

    """ 
        Adapted from Generic_GUI.py.
    """
    
    def __init__(self):                         # Initialiaze self
        super(AppWin, self).__init__()          # Initialize inherited class
        self.initVar()                          # Initialize important variables
        self.initUI()                           # Initialize this window
        self.startIm()                          # Start taking data
        self.startTimer()

    def initVar(self):
        """ Initializes important variables (i.e. current stage positions, limits)"""
        
        self.winBig = False      # Whether Histogram etc. shown - start small

        self.lutNo = 1           # Default colour table

        self.autoscale = True    # Whether to autoscale

        self.av10 = np.array([])

        self.avgHistory = np.zeros([20])
        
        self.frames = 0
        self.good = 0
        self.bad = 0
        self.dup = 0
        
        self.lastGoodFrmTime = 0
        
        self.oldImageId = 0

    def initUI(self):               
        """ Initializes the GUI, especially attaching widgets to routines """

        self.ui = loadUi("server.ui",self)     # Load GUI XML file into ui

        self.ui.details_pb.clicked.connect(self.togWin)     # Connect button to routine
        self.ui.save_pb.clicked.connect(self.saveFile)      # Save current file

        # #### Populate Combo Box with Colour Maps 

        self.valLUT = ["gray","rainbow","hot","nipy_spectral"]   # Standard Matplotlib colour maps
        self.ui.lut_cb.insertItems(0,self.valLUT)                # Stuff drop-down
        self.ui.lut_cb.setCurrentIndex(self.lutNo)               # Set current to Default value

        # #### Set default values and validators on numeric entry boxes


        self.ui.z1_le.setText("0.0")       # Default to 0-1
        self.ui.z2_le.setText("255.0")
        self.ui.z1_le.setValidator(QtGui.QDoubleValidator())     # Float entry only!
        self.ui.z2_le.setValidator(QtGui.QDoubleValidator())

        # #### Set up autoscaling stuff

        self.ui.autoscale_cb.setChecked(self.autoscale)               # Set initial checkbox
        self.ui.autoscale_cb.stateChanged.connect(self.togAutoscale)  # To toggle autoscale        

        # #### Set up matplotlib canvases

        self.iFLIR = StaticMplCanvas(width=5, height=4, dpi=100)    # Create  image canvas
        self.iFLIR.resize(320,240)
        self.ui.FLIR_hl.addWidget(self.iFLIR)                   # Add to horizontal layout

        self.iHist = StaticMplCanvas(width=5, height=4, dpi=100)    # Create  plot canvas
        self.iHist.resize(320,240)
        self.ui.hist_hl.addWidget(self.iHist)                   # Add to horizontal layout
        
        self.histo = self.iHist.figure.subplots()
        
        t = np.linspace(0,10,501)
        
        #self.histo.plot(t, np.tan(t), ".")

        self.ui.statusBar().showMessage('Ready')    # Show status bar
        self.ui.resize(self.ui.minimumSize())       # Resize window to small

        self.ui.show()                              # Show the user interface

#------------------------------------------------------------------------------------------------#

    def startIm(self):
        '''
            Launch thread to start taking data...
        '''

        self.imThrd = getImThread()
        self.connect( self.imThrd, QtCore.SIGNAL("GotOne(QString)"),self.gotFrm)
        self.imThrd.start()
        
    def startTimer(self):
        timer = QtCore.QTimer(self)
        self.connect(timer, QtCore.SIGNAL("timeout()"), self.update)
        timer.start(10)

#------------------------------------------------------------------------------------------------#

    def newItime(self):
        ''' User has set a new interval'''

        if self.imThrd.running:      # Only if it's there

             self.imThrd.iTime = self.ui.iTime_le.value()    # Grab new interval

#------------------------------------------------------------------------------------------------#

    def saveFile(self):     # Save numpy data to file

        fNam = str(QtGui.QFileDialog.getSaveFileName(self,'Numpy file name',''))

        np.savetxt(fNam,self.theImg,fmt='%.10f',delimiter=' ',newline='\n')
        

#------------------------------------------------------------------------------------------------#

    def togWin(self):               # Toggle big / small window
        
        '''
            Toggles between compact and details view.
        '''

        if self.winBig:                          # Need to shrink
          self.ui.resize(self.ui.minimumSize())  # Resize window and msg area
          self.ui.details_pb.setText(u"Details ▼")  # Change button text
          self.winBig=False                      # Set flag
        else:
          self.ui.resize(self.ui.maximumSize())  # Resize
          self.ui.details_pb.setText(u"Hide ▲")     # Button text
          self.winBig=True                       # Set flag
          self.drawHisto()

#------------------------------------------------------------------------------------------------#

    def gotFrm(self):

        '''
            We got a new frame. Display it.
        '''

        self.theImg = self.imThrd.img#[:,:,0]                  # Grab the numpy array (and flatten)
        
        imageId = self.theImg.tobytes()
        
        if not imageId == self.oldImageId:
            
            duplicatePixelCount = np.amax(np.bincount(self.theImg.flatten()))
            
            self.oldImageId = imageId
        
            #print "GOT A FRAME with 2-D shape ",self.theImg.shape

            cMap = self.valLUT[self.ui.lut_cb.currentIndex()]     # Grab the desired colour map

            self.theImg = normalize(self.theImg)

            #cv2.normalize(self.theImg, self.theImg, 0, 255, cv2.NORM_MINMAX)
            #np.right_shift(self.theImg, 8, self.theImg)

            self.theImg = np.uint8(self.theImg)


            if self.autoscale:
                self.iFLIR.dispImg(self.theImg,cMap,autoscale=True)     # Show the image autoscaled

            else:

                z1 = float(self.ui.z1_le.text())                 # Image cuts
                z2 = float(self.ui.z2_le.text())

                self.iFLIR.dispImg(self.theImg,cMap,autoscale=False,cuts=[z1,z2])     # Show the image not autoscaled
                
                     
            self.frames += 1
            
            if duplicatePixelCount < 1000:
                self.good += 1
                self.lastGoodFrmTime = time.time()
            else:
                self.bad += 1
            
            if self.winBig:                                      # only plot Histogram if visible (expanded)
                self.drawHisto()
                self.frame_lcd.display(self.frames)
                self.good_lcd.display(self.good)
                self.bad_lcd.display(self.bad)
        else:
            print "duplicate received"
            self.dup += 1
            self.dup_lcd.display(self.dup)
        

#------------------------------------------------------------------------------------------------#

    def togAutoscale(self):
        ''' Change the status of autoscaling'''

        if self.ui.autoscale_cb.isChecked():
            self.autoscale = True
        else:
            self.autoscale = False

#------------------------------------------------------------------------------------------------#

    def shutdown(self):          # Run shutdown routines

        # reply = QtGui.QMessageBox.critical(self, 'Wow',"All Done!",QtGui.QMessageBox.Ok)
        self.close()             # Close App window
        
#------------------------------------------------------------------------------------------------#
        
    def drawHisto(self):
        self.histo.clear()                               # clear Histogram windows
        self.histo.hist(self.theImg.flatten(), 30)       # plot Histogram
        self.histo.figure.canvas.draw()                  # show Histogram
        
#------------------------------------------------------------------------------------------------#
        
    def doFFC(self):          # Perform FFC
        print "Performing FFC"
        self.ui.statusBar().showMessage("Performing FFC...")
        runCCI(1)
        self.ui.statusBar().showMessage("Ready")
        
#------------------------------------------------------------------------------------------------#
        
    def update(self):
        if self.winBig:
            self.ui.time_lcd.display(time.time() - self.lastGoodFrmTime)
        
def runCCI(command):
    x = subprocess.call(["./c_libs/raspberrypi_video/raspberrypi_video", str(command)])
    print "Return: " , x
   
#------------------------------------------------------------------------------------------------#


###### MAIN APPLICATION LOOP #######

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)  # Create an application object
    aWin = AppWin()                     # Instantiate appWin
    aWin.setWindowTitle("Tom's FLIR Viewer") 
    sys.exit(app.exec_())
