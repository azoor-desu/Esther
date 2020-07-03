#!/usr/bin/python
#
# Monitor removal of bluetooth reciever
import os
import sys
import subprocess
import time

def idleloop():
    while True == True:
        status = subprocess.call('ls /dev/input/event0 2>/dev/null',shell=True)
        print (status)
        if status == 0:
            time.sleep(5)
        else:
            subprocess.call('~/bluetooth/autopair', shell=True)
            time.sleep(2)
idleloop()
