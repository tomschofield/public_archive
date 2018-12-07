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
stick_ripped_out  = False
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
	while (dir_is_empty(image_dir)==False and file_count<10):
		print "start of while. stick_ripped_out: ", stick_ripped_out, file_count

		GPIO.output(red_pin,GPIO.HIGH)
		first_file_name_in_dir = get_file_list(image_dir)[0]
		file_size = get_file_size(image_dir+first_file_name_in_dir)
		try:
			free_space = get_free_space_mb(drive_path)
		except:
			print "no valid file when getting free space"
			stick_ripped_out = True
			break
		print "file: ",first_file_name_in_dir,"file size: ",file_size,"free space on drive", free_space
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
		else:
			break
		
	os.system("eject "+drive_path)
	print "end of transfer until full"
	GPIO.output(red_pin,GPIO.LOW)
	GPIO.output(green_pin,GPIO.HIGH)

#this is not really the way to do this...better than ripping out USB sticks when they're mounted though
def force_unmount_everything():

	command = "umount -l /media/sda1"
	os.system(command)
	command = "umount -l /media/sdb1"
	os.system(command)
	command = "umount -l /media/sdc1"
	os.system(command)
	command = "umount -l /dev/sda1"
	os.system(command)
	command = "umount -l /dev/sdb1"
	os.system(command)
	command = "umount -l /dev/sdc1"
	os.system(command)
	command = "umount -l /dev/sda"
	os.system(command)

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
    for device in iter(monitor.poll, None):
	if (device['ACTION']=='add'):
		print "found ADD usb action in listen"
		time.sleep(2)
		
		mount_from = os.popen("df -h | awk 'END {print $1}'").read().strip()
		mount_to = os.popen("df -h | awk 'END {print $6}'").read().strip()
		
		exploded = mount_from.split("/");
		if(len(exploded)>=3):
			print "exploded",len(exploded),exploded[0],exploded[2]
			print "mount_from nd to",mount_from,mount_to
	# 		os.system("mount -o sync "+ mount_from+" "+mount_to )
			if(exploded[2]!="root"):
				print "got valid drive", mount_to
				transfer_until_full(image_dir, mount_to, green_pin, red_pin, stick_ripped_out)
				command = "eject "+mount_to
				os.system(command)
# 				command = "umount -l "+mount_from
# 				os.system(command)
# 				command = "umount -l "+mount_to
# 				os.system(command)
# 		force_unmount_everything()
# 		#mount all devices attached
# 		#os.system("mountpy")
# # 		os.system("mount -o sync /dev/sda1 /media/sda1")
# # 		os.system("mount -o sync /dev/sdb1 /media/sdb1")
# # 		os.system("mount -o sync /dev/sdc1 /media/sdc1")
# 		#this is a hacky way of going through sub dirs of a known mount point (/media) and find one that starts in sd and is big
# 		for x in os.walk(mount_directory):
# 			print "x[0]",x[0],x[1]
# 			if(len(x[0].split("/")) >= 3):
# 				if(x[0].split("/")[2][:2]=="pi"):
# 					if device_count < 1:
# 						if (x[0]!="/media/pi/" and x[0]!="/media/pi/SETTINGS"):
# 							print "viable device name (unmounting) ", x[0]
# 							os.system("umount -l "+ x[0])
# 							force_unmount_everything()
# 							print "mounting as sync to ", x[0]
# 							try:
# 								os.system("mount -o sync /dev/sda1 "+x[0])
# 								time.sleep(2)
# 							except:
# 								print "tried to remount non existent drive sda1"
# 							try:
# 								os.system("mount -o sync /dev/sdb1 "+x[0])
# 								time.sleep(2)
# 							except:
# 								print "tried to remount non existent drive sdb1"
# 							try:
# 								os.system("mount -o sync /dev/sdc1 "+x[0])
# 								time.sleep(2)
# 							except:
# 								print "tried to remount non existent drive sdc1"
# 							try:
# 								os.system("mount -o sync /dev/sda "+x[0])
# 								time.sleep(2)
# 							except:
# 								print "tried to remount non existent drive sda"
							
# 							#this line is hack to remove non-existing virtual disk e.g. /media/sda1 (these should return a size which is the available space on the pi)
# 							if get_free_space_mb(x[0]) >get_free_space_mb("/home")*1.2:
# 								print "valid device: ", x[0],get_free_space_mb(x[0])
# 								transfer_until_full(image_dir, x[0], green_pin, red_pin, stick_ripped_out)
# 								print "forcing unmount in listen"
# 								force_unmount_everything()
	if(device['ACTION']=='unbind' or device['ACTION']=='remove'):
		print "found REMOVE usb action in listen"
		stick_ripped_out= True


if __name__ == '__main__':
	# main()
	image_directory = "../images/"
	mount_directory = "/media/"
	print "listening..."
	force_unmount_everything()
	green_pin=16
	red_pin=12
	setup_GPIO(green_pin,red_pin)
	while 1:
		listen(image_directory,mount_directory,green_pin,red_pin, stick_ripped_out)
    
