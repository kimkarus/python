#!/usr/bin/env python3

import sys
import os
import fdb
from datetime import timedelta, datetime
from time import sleep

def file_read(fname):
        content_array = []
        with open(fname) as f:
                for line in f:
                        line=line.replace('\n','')
                        content_array.append(str(line))
        return content_array


def getUidUser(label):
	file_lines = file_read("/etc/howdy_nison_skud_list")
	len_lines = len(file_lines)
	if len_lines > 0:
		for line in file_lines:
			arr = line.split(',')
			if arr[0][0] == "#":
                                return 0
			if arr[0] == label:
				return int(arr[1])
	return 0


def write_state_to_file(path, status):
        with open(path, 'w') as f:
                line1 = str(status)
                line2 = str(datetime.now())
                #f.writelines([line1, line2])
                #f.write(str(status))
                line = line1+"\n"+line2
                f.write(line)


def read_state_from_file(path):
        with open(path) as f:
                line = f.readline()
                line=line.replace('\n','')
                return(line)


def send_data_to_firebird(user_id, type_reg_time, todate_datetime):
	# Соединение
	con = fdb.connect(dsn='192.168.10.173/3053:C:/Program Files (x86)/TimeControl/BASE/OKO.FDB', user='MEGA', password='STMEGA21')
	# Объект курсора
	cur = con.cursor()
	# Выполняем запрос
	#UID user
	AUID = user_id
	#UID admin
	AADDUID = 1
	UID_DOOR = 1
	sql_0 = "SELECT U.DEVICE_UID, E.UID, E.REGDATEFULL, E.INOUTTYPE FROM GRAPH_FACT_EVENTS E LEFT JOIN USERS U ON (U.UID = E.UID) WHERE (E.REGDATEFULL >= '"+str(today0)+"') AND (E.REGDATEFULL <= '"+str(today1)+"') AND (E.USER_TYPE = 0) AND E.UID = "+str(AUID)+";"
	cur.execute(sql_0)
	count = len(cur.fetchall())
	#print(count)
	commit = False
	#print("sql_count:"+str(count))
	if count < 1 and type_reg_time == 2:
		sql_1 = "SELECT ARESULT FROM REG_SETWORKSTATUS(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);"
		cur.callproc("REG_SETWORKSTATUS", (1,AUID,AADDUID,UID_DOOR,str(todate_datetime),1,1,1,1,0,0,0,0,0,0,0,0,1,0,0,0))
		outputParams = cur.fetchone()
		#
		cur.callproc("REG_SETWORKSTATUS", (1,AUID,AADDUID,UID_DOOR,str(todate_datetime),2,1,1,1,0,0,0,0,0,0,0,0,2,0,0,0))
		outputParams = cur.fetchone()
		#
		con.commit()
		print("commit")
	elif count < 1:
		sql_1 = "SELECT ARESULT FROM REG_SETWORKSTATUS(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);"
		cur.callproc("REG_SETWORKSTATUS", (1,AUID,AADDUID,UID_DOOR,str(todate_datetime),type_reg_time,1,1,1,0,0,0,0,0,0,0,0,type_reg_time,0,0,0))
		outputParams = cur.fetchone()
		con.commit()
		print("commit")
	elif count > 0:
		sql_1 = "SELECT ARESULT FROM REG_SETWORKSTATUS(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);"
		cur.callproc("REG_SETWORKSTATUS", (1,AUID,AADDUID,UID_DOOR,str(todate_datetime),type_reg_time,1,1,1,0,0,0,0,0,0,0,0,type_reg_time,0,0,0))
		outputParams = cur.fetchone()
		con.commit()
		print("commit")
	else:
		print("nothing")
	con.close()
	return(0)

if len(sys.argv) < 1:
	print(1)
	sys.exit(1)

label = sys.argv[1]

if label == "":
	print(2)
	sys.exit(2)

user_id = getUidUser(label)
print(user_id)
now = datetime.now()
now_timestamp = now.timestamp()
today = now.strftime('%d.%m.%Y')
todate_datetime = now.strftime("%d.%m.%Y %H:%M:%S")
today0 = today+' 00:00:00'
today1 = today+' 23:59:59'

type_reg_time = 0

if now.hour > 7 and now.hour < 12:
	type_reg_time = 1

if now.hour > 15 and now.hour < 22:
	type_reg_time = 2

if now.hour < 8:
	print(3)
	sys.exit(3)

if now.hour > 23:
	print(4)
	sys.exit(4)

if user_id < 1:
	print(5)
	sys.exit(5)
#type_reg_time = 1
if type_reg_time < 1:
	print(6)
	sys.exit(6)
#######
sleep_timeout = 60
user_status = ['0','']
user_path = "/var/"+str(user_id)+".log"
file_exists = os.path.exists(user_path)
if file_exists:
	user_status = file_read(user_path)
else:
	user_status = ['0','']
user_is = '0'
user_is_datetime = 0
######
if user_path != '' and len(user_status) > 1:
	user_is = user_status[0]
	if len(user_status) > 1:
		if user_status[1] != '' and user_status[1] != '0':
			user_is_datetime = datetime.strptime(str(user_status[1]), '%Y-%m-%d %H:%M:%S.%f')
if len(user_status) > 1:
	if user_status[1] != '' and user_status[1] != '0':
		diff = user_is_datetime-now
		diff_in_seconds = abs(diff.days*24*60*60 + diff.seconds)
else:
	diff_in_seconds = 0
#print("user_is="+str(user_is)+" datetime is="+str(user_is_datetime))


if user_is == '0' or diff_in_seconds > sleep_timeout:
	write_state_to_file(user_path, '1')
	result = send_data_to_firebird(user_id, type_reg_time, todate_datetime)
	sleep(sleep_timeout)
	write_state_to_file(user_path, '0')


sys.exit(0)
