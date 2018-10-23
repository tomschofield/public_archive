#!/usr/bin/env python

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

def get_free_space_mb(dirname):
        st = os.statvfs(dirname)
        return st.f_bavail * st.f_frsize / 1024 / 1024


directory = "/media/"

def get_file_list(path):
        onlyfiles = [f for f in listdir(path) if isfile(join(path, f))]
        return onlyfiles

def main():
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
        print device
        time.sleep(3)
        os.system("mountpy")
        for x in os.walk(directory):
                #print x[0]
                if(len(x[0].split("/")) == 3):
                        #print "end of path",x[0].split("/")[2], x[0].split("/")[2][:2]
                        if(x[0].split("/")[2][:2]=="sd"):
                                if device_count < 1:
                                        print "device name ", x[0]
                                        #command = "mv ./images/_90402_RP_P_2017_6105.jpg "+x[0]
                                        #os.system(command)
                                        print get_free_space_mb(x[0])
        device_count+=1
        break

        


if __name__ == '__main__':
   main()
    #print get_file_list(directory)


