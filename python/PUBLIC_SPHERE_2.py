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

def get_free_space_mb(dirname):
	try:
		st = os.statvfs(dirname)
		return st.f_bavail * st.f_frsize / 1024 / 1024
	except:
		print "no valid dir"
		return 0

def get_file_list(path):
	onlyfiles = [f for f in listdir(path) if isfile(join(path, f))]
	return onlyfiles

def dir_is_empty(path):
	if(len(get_file_list(path))>0):
		return False
	return True

def get_file_size(path):
	return os.path.getsize(path) / 1000.0 / 1000.0

#fills the target drive until its full of images sourced from image_dir
def transfer_until_full(image_dir, drive_path, green_pin, red_pin, stick_ripped_out):
	print "start transfer until full"
	GPIO.output(green_pin,GPIO.LOW)
	GPIO.output(red_pin,GPIO.HIGH)
	stick_ripped_out==False
	file_count = 0
	print dir_is_empty(image_dir), stick_ripped_out,file_count
	#while there are images left and until we've transferred 10 across
	while (dir_is_empty(image_dir)==False and file_count<12):
		print "start of while. stick_ripped_out: ", stick_ripped_out, file_count
		#turn the red light on
		GPIO.output(red_pin,GPIO.HIGH)
		first_file_name_in_dir = get_file_list(image_dir)[0]
		#check the size of the image to transfer
		file_size = get_file_size(image_dir+first_file_name_in_dir)
		#find how much free space is left on the drive
		try:
			free_space = get_free_space_mb(drive_path)
		except:
			print "no valid file when getting free space"
			stick_ripped_out = True
			break
		#debug print. which file are we on and how big is it and how much space is left on the drive
		print "file: ",first_file_name_in_dir,"file size: ",file_size,"free space on drive", free_space
		#if there's enough space on the drive
		if(free_space>file_size):
			command = "rsync -c "+ image_dir+first_file_name_in_dir +" "+drive_path+"/"+first_file_name_in_dir
			#subprocess.call(command)
			#try:
			result = os.system(command)
			print "result", result
			#time.sleep(2)
			os.system("rm "+image_dir+first_file_name_in_dir)
			file_count+=1
			#this is the error code for cannot create regular file
			if(result ==5888):
				print "stick ripped out in transfer function"
				stick_ripped_out==True
				GPIO.output(red_pin,GPIO.LOW)
				GPIO.output(green_pin,GPIO.HIGH)
				break
			
			GPIO.output(red_pin,GPIO.LOW)
		#otherwise lets quit the transfer
		else:
			break
		
	#os.system("eject "+drive_path)
	print "end of transfer until full"
	GPIO.output(red_pin,GPIO.LOW)
#listen for USB hotplug events
def listen(image_dir,mount_directory,green_pin,red_pin, stick_ripped_out):
    BASE_PATH = os.path.abspath(os.path.dirname(__file__))
    path = functools.partial(os.path.join, BASE_PATH)
    call = lambda x, *args: subprocess.call([path(x)] + list(args))

    #uses pyudev to monitor usb
    context = pyudev.Context()
    monitor = pyudev.Monitor.from_netlink(context)
    monitor.filter_by(subsystem='usb')  # Remove this line to listen for all devices.
    monitor.start()

    device_count = 0
    #if there's a USB event go through the devices one by one
    mount_to = 0
    for device in iter(monitor.poll, None):
		if (device['ACTION']=='add' and "BUSNUM" in device and device["ID_MODEL"]!="DELL_Laser_Mouse" and device["ID_MODEL"]!="Dell_KB216_Wired_Keyboard"):
			for item in device.keys():
				print item, device[item]
			if(device_count == 0):
				print "found ADD usb action in listen"
				start_time = time.time()
				is_valid_drive = True
				while os.popen("df -h | awk 'END {print $1}'").read().strip()=="tmpfs":
					#hold until the drive shows up
					print "holding", time.time() - start_time, os.popen("df -h | awk 'END {print $1}'").read().strip()
					var = 1
					if time.time() - start_time > 8:
						is_valid_drive = False
						break
				if(is_valid_drive):
					print "mounted", mount_to
					#break #we don't want to know about more than one device
					mount_from = os.popen("df -h | awk 'END {print $1}'").read().strip()
					mount_to = os.popen("df -h | awk 'END {print $6}'").read().strip()
					print mount_from, mount_to
					device_count += 1
					transfer_until_full(image_dir, mount_to, green_pin, red_pin, stick_ripped_out)
					#command = "eject "+mount_to
					command = "eject "+mount_to
					os.system(command)
					print "device ejected"
					device_count = 0
					command = "./hub-ctrl -h 0 -P 2 -p 0"
					os.system(command)
					print "powered usb hub off"
					time.sleep(4)
					command = "./hub-ctrl -h 0 -P 2 -p 1"
					os.system(command)
					print "powered usb hub on"
					command = "mount "+mount_to
					os.system(command)
		if(device['ACTION']=='unbind' or device['ACTION']=='remove'):
			print "found REMOVE usb action in listen"
			device_count = 0
			command = "eject "+mount_to
			os.system(command)




image_directory = "../images/"
mount_directory = "/media/"
print "listening..."
green_pin=16
red_pin=12
setup_GPIO(green_pin,red_pin)
stick_ripped_out = False
#while 1:
listen(image_directory,mount_directory,green_pin,red_pin, stick_ripped_out)
