#!/usr/bin/env python3

# Import required modules
import subprocess, threading, shlex
import os
import sys
import glob
import syslog
from datetime import datetime
from time import sleep


def kill_proc(proc, timeout):
	timeout["value"] = True
	proc.kill()


def run(cmd, timeout_sec):
	#subprocess.Popen(["/usr/bin/python3", "/lib/security/howdy/compare_mod.py", place, place_cam])
	proc = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	timeout = {"value": False}
	timer = threading.Timer(timeout_sec, kill_proc, [proc, timeout])
	timer.start()
	stdout, stderr = proc.communicate()
	timer.cancel()
	return proc.returncode, stdout.decode("utf-8"), stderr.decode("utf-8"), timeout["value"]


place  = sys.argv[1]
place_cam = sys.argv[2] 
rele_type = sys.argv[3]
rele_path = sys.argv[4]

subprocess.Popen(["/usr/bin/python3", "/lib/security/howdy/compare_mod.py", place, place_cam, rele_type, rele_path])
#cmd = "/usr/bin/python3"+" "+"/lib/security/howdy/compare_mod.py"+" "+place+" "+place_cam+" "+rele_type+" "+rele_path
#run(cmd, 17) 
#status = subprocess.Popen(["/usr/bin/python3", "/lib/security/howdy/compare_mod.py", place, place_cam])
#status = subprocess.call(["/usr/bin/python3", "/lib/security/howdy/compare_mod.py", place, place_cam])
#status = subprocess.run(["/usr/bin/python3", "/lib/security/howdy/compare_mod.py", place, place_cam], stdout=subprocess.PIPE)
