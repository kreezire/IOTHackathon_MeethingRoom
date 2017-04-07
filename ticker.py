#!/usr/bin/python
#
# Smart Meeting Room using Adobe IOT Badge (Arduino Lily Pad USB based)
# Thinking out of the cubicle(gupta1, vipaggar, thirani)
#

import re, string, time, urllib, os, sys, time
import csv, urllib, StringIO, serial
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

# Where to open a connection to the badge
# See https://wiki.corp.adobe.com/pages/viewpage.action?spaceKey=tech2017&title=How+to+Reuse+the+IoT+Badge
badge_serial_port = 'COM4'

class State:
	FREE = 1
	BOOKING_CURRENTLY = 2
	BOOKED_OCCUPIED = 3
	BOOKED_UNOCCUPIED = 4
	
class Mode:
	DEBUG = 1
	EXPORT = 2

mode = Mode.EXPORT

def debugPrint(str):
	global mode
	if mode == Mode.DEBUG:
		sys.stdout.write(str)
	
freeScreenMsg = ["1 to Book", "3 for Housekeeping", ""]
bookingCurrentlyScreenMsg = [ "2 to add time", "3 to dec time", "4 to book"]
bookedUnoccupiedScreenMsg = ["1 mails attendees", "3 for Housekeeping", "4 to Occupy"]
bookedOccupiedScreenMsg = ["1 mails attendees", "3 for Housekeeping", "5 to Free"]

class MeetingRoom:
	def __init__(self):
		self.name = "EKLAVYA"
		self.state = State.FREE
		self.freeTill = self.getFreeTime()
		self.bookedTill = 0
		self.emalID="vipaggar@adobe.com"
		
	def help(self):
		global badge
		helpMsg = []
		if self.state == State.FREE:
			helpMsg = freeScreenMsg
		elif self.state == State.BOOKING_CURRENTLY:
			helpMsg = bookingCurrentlyScreenMsg
		elif self.state == State.BOOKED_UNOCCUPIED:
			helpMsg = bookedUnoccupiedScreenMsg;
		elif self.state == State.BOOKED_OCCUPIED:
			helpMsg = bookedOccupiedScreenMsg;
		badge.threeLineRoomStatusDisplaySmall(helpMsg[0], helpMsg[1], helpMsg[2])
		time.sleep(2)
			
	def setName(self, str):
		self.name = str
		
	def setTime(self, num):
		self.time = int(num)
		
	def occupy(self):
		self.state = State.BOOKED_OCCUPIED
		
	def getFreeTime(self):
		return int(60)
		
	def tryBook(self):
		global badge
		mins = 15
		hrs = 0
		if self.state == State.FREE:
			self.state = State.BOOKING_CURRENTLY
			while True:
				badge.threeLineRoomStatusDisplay("Enter Time", "%s:%s" % (str(hrs), str(mins)), "2 for + 3 for -")
				btnPressed = getButtonPress(badge)
				if btnPressed == 1:
					self.help()
				elif btnPressed == 2:
					mins = mins + 15
					if mins == 60:
						mins = 0
						hrs += 1
				elif btnPressed == 4:
					if mins >= 15:
						mins = mins - 15
					else:
						if hrs >= 1:
							mins = 45
							hrs -= 1
				elif btnPressed == 8:
					if (hrs*60 + mins) > self.freeTill:
						badge.threeLineRoomStatusDisplaySmall("Available for", "%s hrs :%s mins " % (str(self.freeTill/60), str(self.freeTill%60)), "Please Try Again")
						time.sleep(1)
					else:
						self.state = State.BOOKED_UNOCCUPIED
						self.bookedTill = hrs*60 + mins
						self.freeTill = 0
						mess = "Request to Book for "+ str(self.bookedTill) +" mins."
						badge.threeLineRoomStatusDisplay("Trying to", "book", self.name)
						badge.sendMail([self.emalID], self.name, mess)
					break
				else:
					nop
			
	def freeUp(self):
		self.state = State.FREE
		self.bookedTill = 0
		self.freeTill = self.getFreeTime()
		
	def updateRoomStatus(self):
		nop
		
	def getMeetingName(self):
		return "Ice Cream Party"
		
	def convertTime(self):
		self.minutes = self.time %60
		self.hours = self.time/60
		
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
		self.sendStr("clear; rgb(-1,0,0,0)")

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
			
	def threeLineRoomStatusDisplaySmall(self, firstline, secondline, thirdline):

		hpos1 = (128 - len(firstline)*6) / 2  # Center
		hpos2 = (128 - len(secondline)*6) / 2  # Center
		hpos3 = (128 - len(thirdline)*6) / 2  # Center
		self.sendStr('o_clear;o_font("sys5x7");o_1x;o_cursor(%d,0);o_print("%s");o_cursor(%d,3);o_print("%s");o_1x;o_cursor(%d,6);o_print("%s")'%(hpos1, firstline,hpos2,secondline,hpos3,thirdline))	
			
	def threeLineRoomStatusDisplay(self, firstline, secondline, thirdline):

		hpos1 = (128 - len(firstline)*12) / 2  # Center
		hpos2 = (128 - len(secondline)*12) / 2  # Center
		hpos3 = (128 - len(thirdline)*6) / 2  # Center
		self.sendStr('o_clear;o_font("sys5x7");o_2x;o_cursor(%d,0);o_print("%s");o_cursor(%d,3);o_print("%s");o_1x;o_cursor(%d,6);o_print("%s")'%(hpos1, firstline,hpos2,secondline,hpos3,thirdline))		

		
		#self.sendStr('o_clear;o_font("sys5x7");o_2x')
		#hpos = (128 - len(firstline)*12) / 2  # Center
		#self.sendStr('o_cursor(%d,0);o_print("%s")' % (hpos, firstline))
		#hpos = (128 - len(secondline)*12) / 2  # Center
		#self.sendStr('o_cursor(%d,3);o_print("%s")' % (hpos, secondline))	
		#self.sendStr('o_1x')
		#hpos = (128 - len(thirdline)*6) / 2  # Center
		#self.sendStr('o_cursor(%d,6);o_print("%s")' % (hpos, thirdline))
	def sendMail(self, to,subject, message):
		if True:
			time.sleep(1)
			return
		print("trying to send mail\n")
		sender = "placementplusplus@gmail.com"
		messageFinal = """From: """+sender+"""
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
			smtpObj.sendmail(sender, to, message)        
			print "Successfully sent email"
		except smtplib.SMTPException as e:
			print "Error: unable to send email" + str(e)

	def mailHouseKeeping(self):
		self.threeLineRoomStatusDisplay("Sending", "Email To", "Housekeeping")
		self.sendMail(["vipaggar@adobe.com"], "House Keeping", "We messed it up")
		self.threeLineRoomStatusDisplay("", "Mail Sent", "")
		time.sleep(1)
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
			self.threeLineRoomStatusDisplay(room.name, "Free", "Till %s hrs %s mins" % (str(room.freeTill/60), str(room.freeTill%60)))
			
		elif room.state == State.BOOKED_OCCUPIED or room.state == State.BOOKED_UNOCCUPIED:
			if room.state == State.BOOKED_OCCUPIED:
				self.setBothLEDColor(ColorCode.red)
				self.threeLineRoomStatusDisplay(room.name, "Occupied", "Till %s hrs %s mins" % (str(room.bookedTill/60), str(room.bookedTill%60)))
			else:
				self.setBothLEDColor(ColorCode.yellow)
				self.threeLineRoomStatusDisplay(room.name, "Booked", "Press 4 to occupy")			
		time.sleep(1)
			
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
	def emailAttendees(self):
		self.threeLineRoomStatusDisplay("Sending", "Email To", "Attendees")
		self.sendMail(["vipaggar@adobe.com", "gupta1@adobe.com"], "Meeting", "Meeting reminder.")
		self.threeLineRoomStatusDisplay("", "Mail Sent", "")
		time.sleep(1)
		return
					
	def buttonPressed(self, btn):
		global room
		if room.state == State.FREE:
			if btn == 1:
				room.tryBook()
			elif btn == 2:
				room.help()
			elif btn == 4:
				self.mailHouseKeeping()
			elif btn == 8:
				nop
			elif btn == 16:
				room.freeUp()
			else:
				nop
		elif room.state == State.BOOKED_UNOCCUPIED:
			if btn == 1:
				self.emailAttendees()
			if btn == 2:
				room.help()
			elif btn == 8:
				room.occupy()
			elif btn == 4:
				self.mailHouseKeeping()
			elif btn == 16:
				room.freeUp()
		elif room.state == State.BOOKED_OCCUPIED:
			if btn == 1:
				self.emailAttendees()
			elif btn == 16:
				room.freeUp()
			if btn == 2:
				room.help()
			elif btn == 4:
				self.mailHouseKeeping()
			elif btn == 16:
				room.freeUp()
			
def getButtonPress(badge):
	btnPressed = -1
	prevTime = getCurTime()
	while True:
		temp = getCurTime()
		if  (temp - prevTime) > 5:
			if room.state == State.FREE:
				room.freeTill -= 1
				if room.freeTill == 0:
					room.state = State.BOOKED_UNOCCUPIED
					room.bookedTill = 60
			elif room.state == State.BOOKED_OCCUPIED or room.state == State.BOOKED_UNOCCUPIED:
				room.bookedTill -= 1
				if room.bookedTill == 0:
					room.state = State.FREE
					room.freeTill = room.getFreeTime()
			badge.displayRoomStatus()
			prevTime = temp
		ret = badge.sendStr("print buttons")
		l = ret.split('\n')
		if len(l) > 1:
			if l[1].find('>') == -1:
				btnPressed = int(l[1])
				debugPrint("return val = %d\n" % btnPressed)
				if btnPressed != 0:
					break
	return btnPressed

def getCurTime():
	return int(time.time())

badge = Badge()

def doStuff():
	global badge
	
	while True:
		badge.displayRoomStatus()
		btnPressed = getButtonPress(badge)
		if btnPressed != -1:
			#debugPrint("Reached here\n")
			badge.buttonPressed(btnPressed)
	
doStuff()