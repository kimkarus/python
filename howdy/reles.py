 #!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# 

import subprocess, threading, shlex
import os
import sys

def run_rele(rele_type, rele_path):
	if rele_type == "usb":
		subprocess.Popen(["/usr/bin/python3", "/lib/security/howdy/usb.py", rele_path])
	if rele_type == "wifi":
		subprocess.Popen(["/usr/bin/python3", "/lib/security/howdy/wifi.py", rele_path])


rele_types = sys.argv[1]
rele_paths = sys.argv[2]

arr_types = rele_types.split(':')
arr_paths = rele_paths.split(':')

idx = 0
if len(arr_types) > 0:
	for type in arr_types: 
		rele_type = arr_types[idx]
		rele_path = arr_paths[idx]
		run_rele(rele_type, rele_path)
		idx = idx + 1
else:
	run_rele(rele_types, rele_paths)

sys.exit(0)
