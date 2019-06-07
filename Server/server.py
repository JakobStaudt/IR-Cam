'''
	Simple socket server using threads
'''

#!/usr/bin/env python
# -*- coding: utf-8 -*-


from PyQt4 import QtCore, QtGui
from PyQt4.QtGui import QDialog
from PyQt4.uic import loadUi

import numpy as np
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

import subprocess

import datetime,time, sys

import cv2

import socket
import sys
import Queue
from thread import *

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
print 'Socket now listening'

#Function for handling connections. This will be used to create threads
def clientthread(conn,q):
	imgStr = ""
	#Sending message to connected client
	conn.send('Welcome to the server. Type something and hit enter\n') #send only takes string
	
	#infinite loop so that function do not terminate and thread do not end.
	while True:
		
		#Receiving from client
		data = conn.recv(1024)
		#print data
		if "s" in data:
			imgStr = ""

		imgStr += data

		if "e" in data:
			print "got image"
			imgStr = imgStr[1:-1]		# Remove "s" and "e" markers
			exec("img = " + imgStr)		# convert string to list (hacky)
			print img[0][0]			# print 1st entry (debug)
			q.put(img)			# send Image array to display thread

		if not data: 
			break
	
	
	#came out of loop
	conn.close()

def echoThread(q):
	while True:
		try:
			x = q.get()
			print "got image at thread2, [0][0] is " + str(x[0][0])
		except:
			pass







q = Queue.Queue()

start_new_thread(echoThread ,(q,))

#now keep talking with the client
while 1:
    #wait to accept a connection - blocking call
	conn, addr = s.accept()
	print 'Connected with ' + addr[0] + ':' + str(addr[1])
	
	#start new thread takes 1st argument as a function name to be run, second is the tuple of arguments to the function.
	start_new_thread(clientthread ,(conn,q,))

s.close()
