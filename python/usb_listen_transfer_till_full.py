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

def setup_GPIO(green_pin, red_pin):
	GPIO.setmode(GPIO.BCM)
	GPIO.setwarnings(False)
	GPIO.setup(red_pin,GPIO.OUT)
	GPIO.setup(green_pin,GPIO.OUT)
	#12 is greeen
	GPIO.output(green_pin,GPIO.HIGH)
	#16 is red
	GPIO.output(red_pin,GPIO.LOW)        

def get_free_space_mb(dirname):
	st = os.statvfs(dirname)
	return st.f_bavail * st.f_frsize / 1024 / 1024

def get_file_list(path):
	onlyfiles = [f for f in listdir(path) if isfile(join(path, f))]
	return onlyfiles

def dir_is_empty(path):
	if(len(get_file_list(path))>0):
		return False
	return True

def get_file_size(path):
	return os.path.getsize(path) / 1000.0 / 1000.0

def transfer_until_full(image_dir, drive_path, green_pin, red_pin):
	GPIO.output(green_pin,GPIO.LOW)
	GPIO.output(red_pin,GPIO.HIGH)

	while (dir_is_empty(image_dir)==False):
		GPIO.output(red_pin,GPIO.HIGH)
		first_file_name_in_dir = get_file_list(image_dir)[0]
		file_size = get_file_size(image_dir+first_file_name_in_dir)
		free_space = get_free_space_mb(drive_path)
		print "file: ",first_file_name_in_dir,"file size: ",file_size,"free space on drive", free_space
		if(free_space>file_size):
			command = "mv "+ image_dir+first_file_name_in_dir +" "+drive_path+"/"+first_file_name_in_dir
			os.system(command)
			GPIO.output(red_pin,GPIO.LOW)
		else:
			break
	os.system("eject "+drive_path)
	print "breaking"
	GPIO.output(red_pin,GPIO.LOW)
	GPIO.output(green_pin,GPIO.HIGH)




def listen(image_dir,green_pin,red_pin):
    BASE_PATH = os.path.abspath(os.path.dirname(__file__))
    path = functools.partial(os.path.join, BASE_PATH)
    call = lambda x, *args: subprocess.call([path(x)] + list(args))

    context = pyudev.Context()
    monitor = pyudev.Monitor.from_netlink(context)
    monitor.filter_by(subsystem='usb')  # Remove this line to listen for all devices.
    monitor.start()

    device_count = 0
    for device in iter(monitor.poll, None):
        # I can add more logic here, to run only certain kinds of devices are plugged.
        #print(device)
	time.sleep(3)
	os.system("mountpy")
	for x in os.walk(directory):
		if(len(x[0].split("/")) == 3):
	        #print "end of path",x[0].split("/")[2], x[0].split("/")[2][:2]
	        if(x[0].split("/")[2][:2]=="sd"):
	                if device_count < 1:
	                        print "device name ", x[0]
	                        #this line is hack to remove non-existing virtual isk e.g. /media/sda1
	                        #TODO update so that 6000 is free disk space on the pi
	                        if get_free_space_mb(x[0]) >6000:
	                            print get_free_space_mb(x[0])
	                            transfer_until_full(image_dir, drive_path, green_pin, red_pin)
	                            force_unmount_everything()
				#now lets transfer files one by one
				#first check that the source directory isn't empty (it shouldn't be but still)
				

	


if __name__ == '__main__':
    # main()
    image_directory = "../images/"

    print "starting transfer"
    setup_GPIO()
    green_pin=12
    red_pin=16
    listen(directory,green_pin,red_pin)
    print "finished transfer"