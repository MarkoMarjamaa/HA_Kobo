
import paho.mqtt.client as mqtt
import json

import time
from datetime import datetime
import subprocess

#import Tkinter as tk
import tkinter as tk
from threading import Thread

# MQTT Server address
broker_address="homeautomation"

class State:
	current_hours = 25
	current_minutes = 61
	current_day = "00.00"
	current_year = "0000"
	nextrain = datetime.now()
	current_nextrain = ""

	current_capacity = 0

	current_inside_temperature = 19.6
	new_inside_temperature = 19.6

	current_outside_temperature = -99.0
	new_outside_temperature = -99.0

	next_sunset = datetime.now()
	current_next_sunset = ""

	current_notifications = ""
	new_notifications = ""

	current_wifi_stayon = True
	new_wifi_stayon = True

	lblDay = None
	lblInsideTemp= None
	lblOutsideTemp= None
	lblYear= None
	lblTime= None
	lblNextSunset= None
	lblNoRainIn= None
	txtNotif= None

# MQTT message loop
def on_message(client, userdata, message):
	global State
	#print(message.topic)
	data = str(message.payload.decode("utf-8"))
	#print(data)
	
	if message.topic == "RainRadar2MQTT/sensor/rainradar_home" :
		resp = json.loads(data)
		NextRainIn = resp['NextRainIn']
		State.nextrain = datetime.strptime(NextRainIn[:-6]+ " " + NextRainIn[-6:-3]+ NextRainIn[-2:], '%Y-%m-%dT%H:%M:%S %z').astimezone().replace(tzinfo=None)
		#print("MQTT nextrain: " + str(State.nextrain))

	if message.topic == "HA_Kobo/inside_temperature" :
		State.new_inside_temperature = float(data)
		#print("MQTT temp: " + str(State.new_inside_temperature))

	if message.topic == "HA_Kobo/outside_temperature" :
		State.new_outside_temperature = float(data)
		#print("MQTT temp: " + str(State.new_outside_temperature))
	
	if message.topic == "HA_Kobo/next_sunset" :
		sunset= data[:-6] + " " + data[26:-3]+ data[30:]
		State.next_sunset = (datetime.strptime(sunset, '%Y-%m-%dT%H:%M:%S.%f %z')).astimezone().replace(tzinfo=None)
		#print("MQTT sunset: " + str(State.next_sunset))

	if message.topic == "HA_Kobo/wifi_stay_on" :
		if data == "on" : 
			State.current_wifi_stayon = True
		else :
			State.current_wifi_stayon = False

	if message.topic == "HA_Kobo/notifications" :
		State.new_notifications = (" ".join((message.payload.decode("ascii")).split())).replace("\\n", "\n")
		#print("MQTT notications: " + State.new_notifications)

def TimeDiff2Str( dtDiff ):
	divDiff = divmod(int(dtDiff.total_seconds()/60), 60 )
	strDiff = ""
	if divDiff[0] == 1 :
		strDiff = strDiff + "1 Hr"
	elif divDiff[0] > 1 :
		strDiff = strDiff + str(divDiff[0]) + " Hrs"
	if divDiff[0] < 3 :
		if divDiff[0] > 0 and divDiff[0] > 0 : 
			strDiff = strDiff + ","
		if divDiff[1] == 1 :
			strDiff = strDiff + "1 Min"
		elif divDiff[1] > 1 :
			strDiff = strDiff + str(divDiff[1]) + " Mins"
	if divDiff[0] == 0 and divDiff[0] == 0 : 
		strDiff = "Now"
	return strDiff

def updater(State):
	# Sync to minute
	#print("Starting")
	#print (datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3])

	# Start loop
	just_started=True
	while True:
		# Minute starts
		#print (" Minute: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3])
		time.sleep(1)
		current_now = datetime.now()
		minutes = int(current_now.strftime('%M'))
		hours = int(current_now.strftime('%H'))
		day = current_now.strftime('%d.%m')
		year = current_now.strftime('%Y')
	
		if( minutes == 6 or minutes == 21 or minutes == 36 or minutes == 51 or just_started ) :
			#print ("Connecting HA")
			#enable Wifi
			# Get current ip (=check wifi is on) 
			ips = (subprocess.check_output("sudo ifconfig eth0 | grep -o -E '([0-9]{1,3}\.){3}[0-9]{1,3}' | head -1", shell=True)).decode().splitlines()
			#print(ips)
			if ( len(ips) == 0) :
				#print("No ip")
				if State.current_wifi_stayon == False : 
					#print("Starting wifi")
					subprocess.call('/home/marek/scripts/wifi/start', shell=True)
					#print("Wi-Fi enabled")

			# Get current ip (=check wifi is on) 
			ips = (subprocess.check_output("sudo ifconfig eth0 | grep -o -E '([0-9]{1,3}\.){3}[0-9]{1,3}' | head -1", shell=True)).decode().splitlines()
			#print(ips)
			if ( len(ips) == 1) :
				# Ip found = wifi on
				#print("creating new instance")
				client = mqtt.Client("HA_Kobo_Kobo")
				client.on_message=on_message #attach function to callback

				#print("connecting to broker")
				client.connect(broker_address)

				# Inform Battery capacity
				capacity = int((subprocess.check_output("cat /sys/class/power_supply/mc13892_bat/capacity", shell=True)).decode())
				if capacity != State.current_capacity : 
					#print ("Update capacity: " + str(capacity))
					State.current_capacity = capacity

					client.publish("HA_Kobo/battery",str(capacity))

				client.loop_start()

				#print("Subscribing to topic","HA_Kobo/")
				client.subscribe("RainRadar2MQTT/sensor/rainradar_home")
				client.subscribe("HA_Kobo/+")

				time.sleep(2)
				client.loop_stop()
			
				if State.current_wifi_stayon == False : 
					#print("Stopping wifi")
					subprocess.call('/home/marek/scripts/wifi/stop', shell=True)
					#print("Wi-Fi disabled")

		#print("### UPDATES ###")
			
		if ( State.new_notifications != State.current_notifications ) : 
			#print ( "Update notifications : "+ State.new_notifications)
			State.current_notifications = State.new_notifications
			State.txtNotif.config(text=State.current_notifications )

		if ( State.new_outside_temperature != State.current_outside_temperature ) : 
			#print ( "Update outside temperature : "+ str(State.new_outside_temperature))
			State.current_outside_temperature = State.new_outside_temperature
			State.lblOutsideTemp.config(text=(str(State.current_outside_temperature)+"C") )

		if ( State.new_inside_temperature != State.current_inside_temperature ) : 
			#print ( "Update inside temperature : "+ str(State.new_inside_temperature))
			State.current_inside_temperature = State.new_inside_temperature
			State.lblInsideTemp.config(text=(str(State.current_inside_temperature)+"C") )

		# Update minutes and all dependent of minutes
		if( State.current_minutes != minutes ) : 
			if( State.current_hours != hours ) : 
				#print("Update hours : " + str(hours))
				State.current_hours = hours

			#print("Update minutes : " + str(minutes))
			State.current_minutes = minutes
			State.lblTime.config(text=(str(State.current_hours).zfill(2)+":"+str(State.current_minutes).zfill(2)) )
			
			# Next rain in 
			if ( State.nextrain >= current_now ) : 
				diffNextRainIn = State.nextrain-current_now
			else :
				diffNextRainIn = State.nextrain-State.nextrain
			strNextRainIn = TimeDiff2Str( diffNextRainIn )
			
			if strNextRainIn != State.current_nextrain : 
				#print( "Update NextRainIn : " + strNextRainIn )
				State.current_nextrain = strNextRainIn
				State.lblNoRainIn.config(text=State.current_nextrain )

			# Next Sunset
			diffNextSunset = State.next_sunset-current_now
			strNextSunset = TimeDiff2Str( diffNextSunset )
			
			if strNextSunset != State.current_next_sunset : 
				#print( "Update NextSunset : " + strNextSunset )
				State.current_next_sunset = strNextSunset
				State.lblNextSunset.config(text=State.current_next_sunset )
				
		if( State.current_day != day ) : 
			#print("Update day : " + day)
			State.current_day = day
			State.lblDay.config(text=State.current_day )

		if( State.current_year != year ) : 
			#print("Update day : " + year)
			State.current_year = year
			State.lblYear.config(text=str(State.current_year) )

		just_started = False
		# Calculate delay for next minute
		seconds = 60.0 - float(datetime.now().strftime('%S.%f')[:-3])
		time.sleep(seconds)


# Main
# Create window
root = tk.Tk()
root.geometry("600x740") 
root.resizable(0, 0)
root.configure(bg="white")
frmMain = root

State.lblDay = tk.Label(frmMain, text=str(State.current_day), font=("Arial", 50) ,bg="white")
State.lblDay.place(x=10, y=0, width=240, height=100)
State.lblYear = tk.Label(frmMain, text=str(State.current_year), font=("Arial", 30) ,bg="white")
State.lblYear.place(x=10, y=100, width=240, height=50)

State.lblTime = tk.Label(frmMain, text=(str(State.current_hours)+":"+str(State.current_minutes)), font=("Arial", 80) ,bg="white")
State.lblTime.place(x=250, y=0, width=350, height=200)

lblInsideTemp_ = tk.Label(frmMain, text="Inside", font=("Arial", 30) ,bg="white")
lblInsideTemp_.place(x=10, y=200, width=300, height=50)
State.lblInsideTemp = tk.Label(frmMain, text=str(State.current_inside_temperature)+"C", font=("Arial", 50) ,bg="white")
State.lblInsideTemp.place(x=10, y=250, width=300, height=100)

lblOutsideTemp_ = tk.Label(frmMain, text="Outside", font=("Arial", 30) ,bg="white")
lblOutsideTemp_.place(x=300, y=200, width=290, height=50)
State.lblOutsideTemp = tk.Label(frmMain, text=str(State.current_outside_temperature)+"C", font=("Arial", 50) ,bg="white")
State.lblOutsideTemp.place(x=300, y=250, width=290, height=100)

lblNextSunset_ = tk.Label(frmMain, text="Next sunset:", font=("Arial", 30) ,bg="white")
lblNextSunset_.place(x=10, y=350, width=270, height=75)
State.lblNextSunset = tk.Label(frmMain, text=State.current_next_sunset, font=("Arial", 30) ,bg="white")
State.lblNextSunset.place(x=270, y=350, width=320, height=75)

lblNoRainIn_ = tk.Label(frmMain, text="  No rain in:", font=("Arial", 30) ,bg="white")
lblNoRainIn_.place(x=10, y=425, width=270, height=75)
State.lblNoRainIn = tk.Label(frmMain, text=State.current_nextrain, font=("Arial", 30) ,bg="white")
State.lblNoRainIn.place(x=270, y=425, width=320, height=75)

State.txtNotif = tk.Label(frmMain, text=State.current_notifications, font=("Arial", 30) ,bg="white")
State.txtNotif.place(x=10, y=500, width=580, height=240)

# Start updater thread
th = Thread(target=updater, args=[State])
th.start()

# Start Tkinter mainloop
tk.mainloop()
