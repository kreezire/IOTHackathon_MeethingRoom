#!/usr/bin/python
#
# Stock ticker display on the TechSummit 2017 badge
# J. Peterson, March 2017
#

import re, string, time, urllib, os, sys
import csv, urllib, StringIO, serial

# List of stocks you want to display (keep it <= 20)
stocks = ['AAPL','GOOG','ADBE','MSFT','AMZN','TWTR','ADSK','VFINX','NVDA','TXN']

# Where to open a connection to the badge
# See https://wiki.corp.adobe.com/pages/viewpage.action?spaceKey=tech2017&title=How+to+Reuse+the+IoT+Badge
badge_serial_port = 'COM6'

class State:
	FREE = 1
	BOOKED_OCCUPIED = 2
	BOOKED_UNOCCUPIED = 3
	
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
		self.status = State.FREE
		self.statusTill = "1 hr"
	
	def setName(self, str):
		self.name = str
	def updateRoomStatus(self):
		self.status = State.BOOKED_OCCUPIED
		self.statusTill = "0.5 hr"
	def getMeetingName(self):
		return "Ice Cream Party"
class Badge:
	def __init__(self):
		self.port = serial.Serial(badge_serial_port, baudrate=9600,timeout=1)
		self.lastreply = self.port.read(100)
		self.bookedDisplayIter = 0
	def sendStr(self, s):
		self.port.write(s + '\r')
		# By waiting to read back the echoed string along
		# with the prompt ('\n> ') we throttle the traffic
		# to what the board can handle.
		self.lastreply = self.port.read(len(s) + 4)
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
		self.led(0,rgb)
		time.sleep(0.3)
		self.sendStr('rgb(0,0,0,0);rgb(1,%d,%d,%d)' % (rgb[0],rgb[1],rgb[2]))
		time.sleep(0.3)
		self.ledsOff()
		
	def displayQuote(self,quote):
		self.sendStr('o_clear;o_font("sys5x7");o_2x;o_cursor(0,1);o_print("%s")' % quote.sym)
		hpos = (128 - len(quote.price)*12) / 2  # Center
		self.sendStr('o_cursor(%d,4);o_print("%s")' % (hpos, quote.price))
		self.sendStr('o_1x;o_cursor(0,7);o_print("%s")' % quote.name)
		hpos = 128 - len(quote.change)*6		# Right justify
		self.sendStr('o_cursor(%d,2);o_print("%s")' % (hpos, quote.change))
		
		green = [ 0,30, 0]
		red =   [30, 0, 0]
		yellow =[30,15, 0]
		blue  = [ 0, 0,30]
		
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
	def threeLineRoomStatusDisplay(self, firstline, secondline, thirdline):
		
		self.sendStr('o_clear;o_font("sys5x7");o_2x')
		hpos = (128 - len(firstline)*12) / 2  # Center
		self.sendStr('o_cursor(%d,0);o_print("%s")' % (hpos, firstline))
		hpos = (128 - len(secondline)*12) / 2  # Center
		self.sendStr('o_cursor(%d,3);o_print("%s")' % (hpos, secondline))	
		self.sendStr('o_1x')
		hpos = (128 - len(thirdline)*6) / 2  # Center
		self.sendStr('o_cursor(%d,6);o_print("%s")' % (hpos, thirdline))
	def display(self, status, room):
		if status == State.FREE:
			self.sendStr("o_2x")
			self.sendStr('o_println("%s")' % room.name)
			self.sendStr('o_println("ITS FREE")')
	
	
	def displayRoomStatus(self):
		room = MeetingRoom()
		room.updateRoomStatus()
		
		if room.status == State.FREE:
			self.bookedDisplayIter=0
			self.threeLineRoomStatusDisplay(room.name, "Free", "Till "+room.statusTill)
		elif room.status == State.BOOKED_OCCUPIED or room.status == BOOKED_UNOCCUPIED:
			self.bookedDisplayIter=(self.bookedDisplayIter+1)%2
			if self.bookedDisplayIter<1:
				self.threeLineRoomStatusDisplay(room.name, "Booked", "Till "+room.statusTill)
			else:
				self.sendStr('o_clear;o_font("sys5x7");o_1x')
				hpos = 0  # Center
				self.sendStr('o_cursor(%d,0);o_print("%s")' % (hpos, room.getMeetingName()))
		else:
			self.sendStr("clr")
			self.sendStr('o_font("sys5x7")')
			room.setName('EKLAVYA')
			self.display(State.FREE, room)
			time.sleep(1)
			self.threeLineRoomStatusDisplay("A","B","C")
		time.sleep(2)
	

def test():
	q = loadQuotes()
	b = Badge()
	b.displayQuote(q['GOOG'])

def doStuff():
	#quotes = loadQuotes()
	badge = Badge()
	while True:
		badge.displayRoomStatus()
	#delay = 60 / len(quotes.keys())
	#for stock in sorted(quotes.keys()):
	#		badge.displayQuote(quotes[stock])
	#		time.sleep(delay)

doStuff()
