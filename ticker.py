#!/usr/bin/python
#
# Stock ticker display on the TechSummit 2017 badge
# J. Peterson, March 2017
#

import re, string, time, urllib, os, sys
import csv, urllib, StringIO, serial
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
# List of stocks you want to display (keep it <= 20)
stocks = ['AAPL','GOOG','ADBE','MSFT','AMZN','TWTR','ADSK','VFINX','NVDA','TXN']

# Where to open a connection to the badge
# See https://wiki.corp.adobe.com/pages/viewpage.action?spaceKey=tech2017&title=How+to+Reuse+the+IoT+Badge
badge_serial_port = 'COM6'

class State:
	FREE = 1
	BOOKED_OCCUPIED = 2
	BOOKED_UNOCCUPIED = 3
	
class Mode:
	DEBUG = 1
	EXPORT = 2

mode = Mode.EXPORT

def debugPrint(str):
	global mode
	if mode == Mode.DEBUG:
		sys.stdout.write(str)
	
class Quote(object):
	def __init__(self,data):
		# Order of the keys matches the nsl1c1 format
		# from Yahoo CSV stock data
		keys = ['name','sym','price','change']
		for i in range(len(keys)):
			self.__dict__[keys[i]] = data[i]

	def dump(self):
		print self.__dict__

def loadQuotes():
	# See http://www.jarloo.com/yahoo_finance/
	# n=name, s=symbol, l1=last trade price, c6=change
	infoRequest = 'nsl1c1'
	reqURL = 'http://finance.yahoo.com/d/quotes.csv?s=' + string.join(stocks,'+') + '&f=' + infoRequest

	csvReader = csv.reader(urllib.urlopen(reqURL))
	stockDict = {}
	for row in csvReader:
		q = Quote(row)
		stockDict[q.sym] = q

##	for q in stockDict.keys():
##		stockDict[q].dump()
	return stockDict

class MeetingRoom:
	def __init__(self):
		self.name = "EKLAVYA"
		self.state = State.FREE
		self.statusTill = "1 hr"
		self.emalID="vipaggar@adobe.com"
	
	def setName(self, str):
		self.name = str
		
	def tryBook(self):
		if self.state == State.FREE:
			self.state = State.BOOKED_OCCUPIED
			
	def freeUp(self):
		self.state = State.FREE
		
	def updateRoomStatus(self):
		nop
		#self.status = State.BOOKED_OCCUPIED
		#self.statusTill = "0.5 hr"
		
	def getMeetingName(self):
		return "Ice Cream Party"
		
room = MeetingRoom()
room.setName('EKLAVYA')
class ColorCode:
	green = [ 0,30, 0]
	red =   [30, 0, 0]
	yellow =[30,15, 0]
	blue  = [ 0, 0,30]
class Badge:
	def __init__(self):
		self.port = serial.Serial(badge_serial_port, baudrate=9600,timeout=1)
		self.lastreply = self.port.read(100)
		

	def sendStr(self, s):
		self.port.write(s + '\r')
		# By waiting to read back the echoed string along
		# with the prompt ('\n> ') we throttle the traffic
		# to what the board can handle.
		self.lastreply = self.port.read(len(s) + 6)
		return self.lastreply

	# Most of these are here just to document the badge commands
	def flush(self):
		print self.port.read(100)

	def msgln(self,s):
		self.sendStr('o_println("%s")' % s)

	def msg(self,s):
		self.sendStr('o_print("%s")' % s)

	def clear(self):
		self.sendStr("o_clear()")

	# Note pos is measured in PIXELS on the x, and LINES on the Y
	def pos(self,x,y):
		self.sendStr('o_cursor(%d,%d)' % (x,y))

	def fontScale(self,x):
		self.sendStr('o_%dx()' % x)

	# Choices are sys5x7, small (# only), large (# only), Images
	def font(self,fontname):
		self.sendStr('o_font("%s")' % fontname)

	def led(self,led,rgb):
		self.sendStr('rgb(%d,%d,%d,%d)' % (led,rgb[0],rgb[1],rgb[2]))

	def ledsOff(self):
		self.sendStr('rgb(0,0,0,0);rgb(1,0,0,0)')

	def blink(self,rgb):
		#self.led(0,rgb)
		#self.led(1,rgb)
		self.sendStr('rgb(0,%d,%d,%d);rgb(1,%d,%d,%d)' % (rgb[0],rgb[1],rgb[2],rgb[0],rgb[1],rgb[2]))
		#time.sleep(0.3)
		#self.sendStr('rgb(0,0,0,0);rgb(1,%d,%d,%d)' % (rgb[0],rgb[1],rgb[2]))
		#time.sleep(0.3)
		#self.ledsOff()
		
	def displayQuote(self,quote):
		self.sendStr('o_clear;o_font("sys5x7");o_2x;o_cursor(0,1);o_print("%s")' % quote.sym)
		hpos = (128 - len(quote.price)*12) / 2  # Center
		self.sendStr('o_cursor(%d,4);o_print("%s")' % (hpos, quote.price))
		self.sendStr('o_1x;o_cursor(0,7);o_print("%s")' % quote.name)
		hpos = 128 - len(quote.change)*6		# Right justify
		self.sendStr('o_cursor(%d,2);o_print("%s")' % (hpos, quote.change))
		
		
		
		try:
			change = float(quote.change)
			price = float(quote.price)
			mustchange = 0.5 / 100
			if (abs(change)/price < mustchange):	# Looking for more than mustchange% change
				self.blink(yellow)
			else:
				self.blink( green if (change > 0) else red )
		except ValueError:
			self.blink(blue)
	
	def setBothLEDColor(self, color):
		try:
			#change = float(quote.change)
			#price = float(quote.price)
			#mustchange = 0.5 / 100
			#if (abs(change)/price < mustchange):	# Looking for more than mustchange% change
			self.blink(color)
			#else:
			#	self.blink( green if (change > 0) else red )
		except ValueError:
			self.blink([0,0,0])
	def threeLineRoomStatusDisplay(self, firstline, secondline, thirdline):
		
		self.sendStr('o_clear;o_font("sys5x7");o_2x')
		hpos = (128 - len(firstline)*12) / 2  # Center
		self.sendStr('o_cursor(%d,0);o_print("%s")' % (hpos, firstline))
		hpos = (128 - len(secondline)*12) / 2  # Center
		self.sendStr('o_cursor(%d,3);o_print("%s")' % (hpos, secondline))	
		self.sendStr('o_1x')
		hpos = (128 - len(thirdline)*6) / 2  # Center
		self.sendStr('o_cursor(%d,6);o_print("%s")' % (hpos, thirdline))
	def sendMail(self, to,subject, message):
		sender = "placementplusplus@gmail.com"
		messageFinal = """From: """+sender+"""
		To: """+to+"""Sumeet Sahu <ssahu@adobe.com>
		MIME-Version: 1.0
		Content-type: text/html
		Subject: """+subject+"""
		
		"""+message+"""
		"""
		try:
			smtpObj = smtplib.SMTP('smtp.gmail.com', 587)	
			smtpObj.ehlo()
			smtpObj.starttls()
			smtpObj.login("placementplusplus@gmail.com", "naveenpadepoopoo")
			#print 23
			smtpObj.sendmail(sender, [to], message)        
			print "Successfully sent email"
		except smtplib.SMTPException as e:
			print "Error: unable to send email" + str(e)
	def mailHouseKeeping(self):
		return
		
	
			
	def displayRoomStatus(self):
		global room
		#green = [ 0,30, 0]
		#red =   [30, 0, 0]
		#yellow =[30,15, 0]
		#blue  = [ 0, 0,30]
		if room.state == State.FREE:
			self.setBothLEDColor(ColorCode.green)
			#self.bookedDisplayIter=0
			self.threeLineRoomStatusDisplay(room.name, "Free", "Till "+room.statusTill)
			
		elif room.state == State.BOOKED_OCCUPIED or room.state == BOOKED_UNOCCUPIED:
			if room.state == State.BOOKED_OCCUPIED:
				self.setBothLEDColor(ColorCode.red)
			else:
				self.setBothLEDColor(ColorCode.yellow)
			#self.bookedDisplayIter=(self.bookedDisplayIter+1)%2
			#if self.bookedDisplayIter<1:
			self.threeLineRoomStatusDisplay(room.name, "Booked", "Till "+room.statusTill)
			#	self.sendStr('o_clear;o_font("sys5x7");o_1x')
			#	hpos = 0  # Center
				#self.sendStr('o_cursor(%d,0);o_print("%s")' % (hpos, room.getMeetingName()))
			
		time.sleep(2)
			
	def display(self, status, room):
		self.sendStr("o_2x")
		self.sendStr('o_println("%s")' % room.name)
		if status == State.FREE:
			self.sendStr('o_println("ITS FREE")')
		elif status == State.BOOKED_OCCUPIED:
			self.sendStr('o_println("ITS BOOKED")')
			
	def displayStuff(self):
		global room
		self.sendStr("clr")
		self.sendStr('o_font("sys5x7")')
		self.display(room.state, room)
		
	def buttonPressed(self, btn):
		global room
		if room.state == State.FREE:
			if btn == 1:
				room.tryBook()
			elif btn == 2:
				nop
			elif btn == 4:
				nop
			elif btn == 8:
				nop
			elif btn == 16:
				nop
			else:
				nop
		elif room.state == State.BOOKED_OCCUPIED:
			if btn == 1:
				room.freeUp()

def test():
	q = loadQuotes()
	b = Badge()
	b.displayQuote(q['GOOG'])

def doStuff():
	badge = Badge()
	#badge.sendMail("vipaggar@adobe.com"," SMTP HTML e-mail test", "sdfdsfs" )
	#return
	while True:
		badge.displayRoomStatus()
		btnPressed = -1
		while True:
			ret = badge.sendStr("print buttons")
			l = ret.split('\n')
			if l[1].find('>') == -1:
				btnPressed = int(l[1])
				debugPrint("return val = %d\n" % btnPressed)
				if btnPressed != 0:
					break
		if btnPressed != -1:
			debugPrint("Reached here\n")
			badge.sendStr('clr; o_2x; o_font("sys5x7"); o_println("Pressed=%d");' % btnPressed)
			time.sleep(1)
			badge.buttonPressed(btnPressed)
	
doStuff()