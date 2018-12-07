#!/usr/bin/env python
import RPi.GPIO as GPIO
import functools
import os.path
import pyudev
import subprocess
import ctypes
import os
from os import listdir
from os.path import isfile, join
import platform
import sys
import time

#set the pi pins so it starts off green on and red off
def setup_GPIO(green_pin, red_pin):
	GPIO.setmode(GPIO.BCM)
	GPIO.setwarnings(False)
	GPIO.setup(red_pin,GPIO.OUT)
	GPIO.setup(green_pin,GPIO.OUT)
	#12 is greeen
	GPIO.output(green_pin,GPIO.HIGH)
	#16 is red
	GPIO.output(red_pin,GPIO.LOW)

green_pin=12
red_pin=16
setup_GPIO(12,16)

while 1:
	GPIO.output(green_pin,GPIO.LOW)
	GPIO.output(red_pin,GPIO.HIGH)
	time.sleep(2)
	GPIO.output(green_pin,GPIO.HIGH)
	GPIO.output(red_pin,GPIO.LOW)
	time.sleep(2)

