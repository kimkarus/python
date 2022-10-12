#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#

import os
import sys
from time import sleep

def write_state_to_file(path, status):
        with open(path, 'w') as f:
                f.write(str(status))


def read_state_from_file(path):
        with open(path) as f:
                line = f.readline()
                line=line.replace('\n','')
                return(line)

rele_path = sys.argv[1]

door_opened = '0'
if rele_path != 'no' and rele_path != '':
        door_opened = read_state_from_file(rele_path)

print(door_opened)

if door_opened == '0':
	res=os.system("usbrelay HW348_1=1")
	write_state_to_file(rele_path, '1')
	sleep(4)
	write_state_to_file(rele_path, '0')
	res=os.system("usbrelay HW348_1=0")


sys.exit(0)
