# Compare incomming video with known faces
# Running in a local python instance to get around PATH issues

# Import time so we can start timing asap
import time

# Start timing
timings = {
	"st": time.time()
}

# Import required modules
import sys
import os
import subprocess
import json
import configparser
import dlib
import cv2
import datetime
import snapshot
import numpy as np
import _thread as thread
from pathlib import Path
from recorders.video_capture import VideoCapture

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

def sys_exit_msg(result, label, place, device, p, rele_type, rele_path):
	output=str(result)+ "," + label
	name_case = device;
	name_case = name_case.replace("#", "");
	name_case = name_case.replace("/", "");
	path_case = "/var/log/"+name_case+".log";
	#print(path_case);
	#write_state_to_file(path_case, '0');
	#print(output)
	write_state_to_file(path_case, '0');
	if result == 0:
		user_id = getUidUser(label)
		if user_id > 0:
			status_led = subprocess.Popen(["/usr/bin/python3", "/lib/security/howdy/reles.py", rele_type, rele_path])
			status_skud = subprocess.Popen(["/usr/bin/python3", "/lib/security/howdy/skud.py", label])
			dateTimeObj = datetime.datetime.now()
			timestampStr = dateTimeObj.strftime("%d-%b-%Y (%H:%M:%S.%f)")
			log_line = timestampStr + ", " + "user: " + place +" - " + label+" p="+str(round(p, 2)) +", " + "cam: " + device + "\n"
			with open("/var/log/howdy_logins.log", "a", encoding="utf-8") as f:
				f.write(log_line)
		else:
			print(label + " is not allowed")
	if result == 17:
		log_line = timestampStr + ", " + "user: " + place +" - " + label+" p="+str(round(p, 2)) +", " + "cam: " + device + "\n"
		with open("/var/log/howdy_logins_other.log", "a", encoding="utf-8") as f:
			f.write(log_line)
	#write_state_to_file(path_case, '0');
	sys.exit(output)


def init_detector(lock):
	"""Start face detector, encoder and predictor in a new thread"""
	global face_detector, pose_predictor, face_encoder

	# Test if at lest 1 of the data files is there and abort if it's not
	if not os.path.isfile(PATH + "/dlib-data/shape_predictor_5_face_landmarks.dat"):
		print("Data files have not been downloaded, please run the following commands:")
		print("\n\tcd " + PATH + "/dlib-data")
		print("\tsudo ./install.sh\n")
		lock.release()
		sys_exit_msg(1,"os.path.isfile","","", 0)

	# Use the CNN detector if enabled
	if use_cnn:
		face_detector = dlib.cnn_face_detection_model_v1(PATH + "/dlib-data/mmod_human_face_detector.dat")
	else:
		face_detector = dlib.get_frontal_face_detector()

	# Start the others regardless
	pose_predictor = dlib.shape_predictor(PATH + "/dlib-data/shape_predictor_5_face_landmarks.dat")
	face_encoder = dlib.face_recognition_model_v1(PATH + "/dlib-data/dlib_face_recognition_resnet_model_v1.dat")

	# Note the time it took to initialize detectors
	timings["ll"] = time.time() - timings["ll"]
	lock.release()


def make_snapshot(type):
	"""Generate snapshot after detection"""
	snapshot.generate(snapframes, [
		type + " LOGIN",
		"Date: " + datetime.datetime.utcnow().strftime("%Y/%m/%d %H:%M:%S UTC"),
		"Scan time: " + str(round(time.time() - timings["fr"], 2)) + "s",
		"Frames: " + str(frames) + " (" + str(round(frames / (time.time() - timings["fr"]), 2)) + "FPS)",
		"Hostname: " + os.uname().nodename,
		"Best certainty value: " + str(round(lowest_certainty * 10, 1))
	])


def write_state_to_file(path, status):
	if Path(path).is_file():
		with open(path, 'w') as f:
			f.write(str(status))
	else:
		new_file = open(path, "w+")
		new_file.write("0")
		new_file.close()


def read_state_from_file(path):
	if Path(path).is_file():
		with open(path) as f:
			line = f.readline()
			line=line.replace('\n','')
			return(line)
	else:
		new_file = open(path, "w+")
		new_file.write("0")
		new_file.close()
		return("0")



# Make sure we were given an username to tast against
if len(sys.argv) < 2:
	sys_exit_msg(12,"","","",0)

# Get the absolute path to the current directory
PATH = os.path.abspath(__file__ + "/..")

# The username of the user being authenticated
user = sys.argv[1]
device = str(sys.argv[2])
rele_type = sys.argv[3]
rele_path = sys.argv[4]

arr_device = device.split('/')
name_device = arr_device[2]
path_device_state = "/var/"+name_device+".log"

device_busy = '0'
if name_device != 'no' and name_device != '':
	device_busy = read_state_from_file(path_device_state)
if device_busy == '0':
	write_state_to_file(path_device_state, '1')
if device_busy == '1':
	sys_exit_msg(16,"",user,device,0,"","")


print(device+" "+user)

# The model file contents
models = []
# Encoded face models
encodings = []
# Amount of ignored 100% black frames
black_tries = 0
# Amount of ingnored dark frames
dark_tries = 0
# Total amount of frames captured
frames = 0
# Captured frames for snapshot capture
snapframes = []
# Tracks the lowest certainty value in the loop
lowest_certainty = 10
# Face recognition/detection instances
face_detector = None
pose_predictor = None
face_encoder = None

# Try to load the face model from the models folder
try:
	models = json.load(open(PATH + "/models/" + user + ".dat"))

	for model in models:
		encodings += model["data"]
except FileNotFoundError:
	sys_exit_msg(14,"",user,device,0,"","")

# Check if the file contains a model
if len(models) < 1:
	sys_exit_msg(15,"",user,device,0,"","")

# Read config from disk
config = configparser.ConfigParser()
config.read(PATH + "/config_cams.ini")

# set new device_path
config.set("video", "device_path", device)

# Get all config values needed
use_cnn = config.getboolean("core", "use_cnn", fallback=False)
timeout = config.getint("video", "timeout", fallback=5)
dark_threshold = config.getfloat("video", "dark_threshold", fallback=50.0)
video_certainty = config.getfloat("video", "certainty", fallback=3.5) / 10
#end_report = config.getboolean("debug", "end_report", fallback=False)
end_report = True
capture_failed = config.getboolean("snapshots", "capture_failed", fallback=False)
capture_successful = config.getboolean("snapshots", "capture_successful", fallback=False)

# Save the time needed to start the script
timings["in"] = time.time() - timings["st"]

# Import face recognition, takes some time
timings["ll"] = time.time()

# Start threading and wait for init to finish
lock = thread.allocate_lock()
lock.acquire()
thread.start_new_thread(init_detector, (lock, ))

# Start video capture on the IR camera
timings["ic"] = time.time()

video_capture = VideoCapture(config)

# Read exposure from config to use in the main loop
exposure = config.getint("video", "exposure", fallback=-1)

# Note the time it took to open the camera
timings["ic"] = time.time() - timings["ic"]

# wait for thread to finish
lock.acquire()
lock.release()
del lock

write_state_to_file(path_device_state, '0')
# Fetch the max frame height
max_height = config.getfloat("video", "max_height", fallback=0.0)
# Get the height of the image
height = video_capture.internal.get(cv2.CAP_PROP_FRAME_HEIGHT) or 1

# Calculate the amount the image has to shrink
scaling_factor = (max_height / height) or 1

# Fetch config settings out of the loop
timeout = config.getint("video", "timeout")
dark_threshold = config.getfloat("video", "dark_threshold")
end_report = config.getboolean("debug", "end_report")

# Start the read loop
frames = 0
valid_frames = 0
timings["fr"] = time.time()
dark_running_total = 0

clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))

while True:
	# Increment the frame count every loop
	frames += 1
	print(frames)	
	# Stop if we've exceded the time limit
	if time.time() - timings["fr"] > timeout:
		# Create a timeout snapshot if enabled
		if capture_failed:
			make_snapshot("FAILED")

		if dark_tries == valid_frames:
			print("All frames were too dark, please check dark_threshold in config")
			print("Average darkness: " + str(dark_running_total / max(1, valid_frames)) + ", Threshold: " + str(dark_threshold))
			sys_exit_msg(13,"",user,device,0,"","")
		else:
			sys_exit_msg(11,"", user,device,0,"","")

	# Grab a single frame of video
	frame, gsframe = video_capture.read_frame()
	gsframe = clahe.apply(gsframe)

	# If snapshots have been turned on
	if capture_failed or capture_successful:
		# Start capturing frames for the snapshot
		if len(snapframes) < 3:
			snapframes.append(frame)

	# Create a histogram of the image with 8 values
	hist = cv2.calcHist([gsframe], [0], None, [8], [0, 256])
	# All values combined for percentage calculation
	hist_total = np.sum(hist)

	# Calculate frame darkness
	darkness = (hist[0] / hist_total * 100)

	# If the image is fully black due to a bad camera read,
	# skip to the next frame
	if (hist_total == 0) or (darkness == 100):
		black_tries += 1
		continue

	dark_running_total += darkness
	valid_frames += 1
	# If the image exceeds darkness threshold due to subject distance,
	# skip to the next frame
	if (darkness > dark_threshold):
		dark_tries += 1
		continue

	# If the hight is too high
	if scaling_factor != 1:
		# Apply that factor to the frame
		frame = cv2.resize(frame, None, fx=scaling_factor, fy=scaling_factor, interpolation=cv2.INTER_AREA)
		gsframe = cv2.resize(gsframe, None, fx=scaling_factor, fy=scaling_factor, interpolation=cv2.INTER_AREA)

	# Get all faces from that frame as encodings
	# Upsamples 1 time
	face_locations = face_detector(gsframe, 1)
	#print("egegey")
	# Loop through each face
	for fl in face_locations:
		#print("egegey")
		if use_cnn:
			fl = fl.rect
		#print("egegey")
		# Fetch the faces in the image
		face_landmark = pose_predictor(frame, fl)
		face_encoding = np.array(face_encoder.compute_face_descriptor(frame, face_landmark, 1))

		# Match this found face against a known face
		matches = np.linalg.norm(encodings - face_encoding, axis=1)

		# Get best match
		match_index = np.argmin(matches)
		match = matches[match_index]

		# Update certainty if we have a new low
		if lowest_certainty > match:
			lowest_certainty = match
		print("match:"+str(match))
		#print("video_certainty:"+str(video_certainty))
		# Check if a match that's confident enough
		#print(0 < match < video_certainty)
		#print(match > 0 and match > video_certainty)
		#if match > 0 and match > video_certainty:
		#if match < 0 and match < video_certainty:
		if 0 < match < video_certainty:
			timings["tt"] = time.time() - timings["st"]
			timings["fl"] = time.time() - timings["fr"]

			# If set to true in the config, print debug text
			if end_report:
				def print_timing(label, k):
					"""Helper function to print a timing from the list"""
					print("  %s: %dms" % (label, round(timings[k] * 1000)))

				# Print a nice timing report
				print("Time spent")
				print_timing("Starting up", "in")
				print("  Open cam + load libs: %dms" % (round(max(timings["ll"], timings["ic"]) * 1000, )))
				print_timing("  Opening the camera", "ic")
				print_timing("  Importing recognition libs", "ll")
				print_timing("Searching for known face", "fl")
				print_timing("Total time", "tt")

				print("\nResolution")
				width = video_capture.fw or 1
				print("  Native: %dx%d" % (height, width))
				# Save the new size for diagnostics
				scale_height, scale_width = frame.shape[:2]
				print("  Used: %dx%d" % (scale_height, scale_width))

				# Show the total number of frames and calculate the FPS by deviding it by the total scan time
				print("\nFrames searched: %d (%.2f fps)" % (frames, frames / timings["fl"]))
				print("Black frames ignored: %d " % (black_tries, ))
				print("Dark frames ignored: %d " % (dark_tries, ))
				print("Certainty of winning frame: %.3f" % (match * 10, ))

				print("Winning model: %d (\"%s\")" % (match_index, models[match_index]["label"]))

			# Make snapshot if enabled
			if capture_successful:
				make_snapshot("SUCCESSFUL")

			# End peacefully
			sys_exit_msg(0,models[match_index]["label"], user,device,match*10,rele_type,rele_path)
		else:
			if capture_successful:
                                make_snapshot("SUCCESSFUL")
			sys_exit_msg(17,models[match_index]["label"], user,device,match*10,rele_type,rele_path)
	if exposure != -1:
		# For a strange reason on some cameras (e.g. Lenoxo X1E)
		# setting manual exposure works only after a couple frames
		# are captured and even after a delay it does not
		# always work. Setting exposure at every frame is
		# reliable though.
		video_capture.internal.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1.0)  # 1 = Manual
		video_capture.internal.set(cv2.CAP_PROP_EXPOSURE, float(exposure))
