#!/bin/env python

import argparse
import sys
# Uses pyserial: community/python-pyserial
import serial
import socket
import xml.etree.ElementTree as ET
from time import time

# Variables
parity	 = serial.PARITY_NONE
stopbits = serial.STOPBITS_ONE
bytesize = serial.EIGHTBITS
timeout	 = None

prefix	 	= "btree."
graphite_server = "127.0.0.1"
graphite_port	= 2003


# code

parser = argparse.ArgumentParser(description='Fetch debug information via serial from a CurrentCost EnviR and post it to graphite')
parser.add_argument('-device', action="store", dest="device", default="/dev/ttyUSB0", help="serial device (default: /dev/ttyUSB0)")
parser.add_argument('-baud', action="store", dest="baud", type=int, default=57600, help="baud rate (default: 57600)")
parser.add_argument('-prefix', action="store", dest="prefix", default="", help="metric prefix")
parser.add_argument('-host', action="store", dest="host", default="graphite", help="graphite host to send metrics to (default: 'graphite')")
parser.add_argument('-port', action="store", dest="port", type=int, default=2003, help="graphite port to send metrics to (default: 2003)")
options = parser.parse_args()

tty = serial.Serial(port=options.device, baudrate=options.baud, parity=parity, stopbits=stopbits, bytesize=bytesize, timeout=timeout)

while True:
	metrics=[]
	xml = tty.readline()
	msg = ET.fromstring(xml)

	if msg.find("hist"):
		continue

	mytime = int(time())
	metricn = options.prefix+"envir.sensor-"+msg.find("sensor").text

	# Handle temperature
	metric = metricn+".temperature"
	metrics.append("%s %s %s" % (metric, msg.find("tmpr").text, mytime))

	# Handle watts
	channels = msg.findall(".//watts/..")
	for channel in channels:
		chanpos = channel.tag.find("ch")+2
		metric  = metricn+".channel-"+channel.tag[chanpos:]+".watts"
		metrics.append("%s %s %s" % (metric, channel.find("watts").text, mytime))


	if len(metrics) > 0:
		try:
			sock = socket.socket()
			sock.connect((options.host, options.port))
			payload = '\n'.join(metrics)+'\n'
			sock.sendall(payload.encode())
			sock.close()
		except:
			print("Failed to send payload. Error:", sys.exc_info())
