#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#

import os
import sys
from time import sleep
import http.client
import datetime

def write_state_to_file(path, status):
	with open(path, 'w') as f:
		line1 = str(status)
		line2 = str(datetime.datetime.now())
		#f.writelines([line1, line2])
		#f.write(str(status))
		line = line1+"\n"+line2
		f.write(line)


def read_state_from_file(path):
	with open(path) as f:
		line = f.readline()
		line=line.replace('\n','')
		return(line)


def file_read(fname):
	content_array = []
	with open(fname) as f:
		for line in f:
			line=line.replace('\n','')
			content_array.append(str(line))
	return content_array


rele_path = sys.argv[1]

sleep_timeout = 6

rele_status = file_read(rele_path)
door_opened = '0'
door_opened_datetime = 0
datetime_now = datetime.datetime.now()
if rele_path != 'no' and rele_path != '':
	door_opened = rele_status[0]
	if len(rele_status) > 1:
		if rele_status[1] != '' and rele_status[1] != '0':
			door_opened_datetime = datetime.datetime.strptime(str(rele_status[1]), '%Y-%m-%d %H:%M:%S.%f')
if len(rele_status) > 1:
	if rele_status[1] != '' and rele_status[1] != '0':
		diff = door_opened_datetime-datetime_now
		diff_in_seconds = abs(diff.days*24*60*60 + diff.seconds)
else:
	diff_in_seconds = 0
print("door_opened="+str(door_opened)+" datetime opened="+str(door_opened_datetime))

headers = {'accept': 'application/json','cache-control': 'no-store','Content-Type': 'application/json;charset=UTF-8'}
body = """{
  "sequence": "1636464444063",
  "deviceid": "100146b855",
  "selfApikey": "2ad673a2-7b3d-48ef-89a5-7642817ac0d9",
  "iv": "MzYyMTAwMDY1MTAwMjg1Mg==",
  "encrypt": true,
  "data": "OrD8kVbmzv8gLZQzL179lQ=="
}"""

if door_opened == '0' or diff_in_seconds > sleep_timeout:
	write_state_to_file(rele_path, '1')
	conn = http.client.HTTPConnection('192.168.12.77:8081', timeout=sleep_timeout-1)
	conn.request('POST','/zeroconf/switch', body, headers)
	res = conn.getresponse()
	data = res.read()
	print(res.status, res.reason)
	print(data.decode('utf-8'))
	print(res.getheaders())
	sleep(sleep_timeout)
	write_state_to_file(rele_path, '0')


sys.exit(0)
