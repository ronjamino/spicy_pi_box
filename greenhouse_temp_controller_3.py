#
#
#

import os
import time
import gpiozero
import threading
import lcddriver
import Adafruit_DHT
import threading
import mysql.connector as mariadb
import glob

from connection_details import GH_USERNAME
from connection_details import GH_PASSWORD

from datetime import datetime

from consts import PI_FAN_GPIO
from consts import GREENHOUSE_FAN_GPIO
from consts import LIGHTS_GPIO
from consts import HEATPAD_GPIO

from consts import PI_TEMP_POLL_INTERVAL
from consts import GREENHOUSE_TEMP_POLL_INTERVAL

from consts import PI_TEMP_UPPER_LIMIT
from consts import PI_TEMP_COOLDOWN

from consts import GREENHOUSE_FAN_DAYTIME_UPPER_LIMIT
from consts import GREENHOUSE_FAN_DAYTIME_LOWER_LIMIT
from consts import GREENHOUSE_FAN_NIGHTTIME_UPPER_LIMIT
from consts import GREENHOUSE_FAN_NIGHTTIME_LOWER_LIMIT

from consts import HEATPAD_DAYTIME_UPPER_LIMIT
from consts import HEATPAD_DAYTIME_LOWER_LIMIT
from consts import HEATPAD_NIGHTTIME_UPPER_LIMIT
from consts import HEATPAD_NIGHTTIME_LOWER_LIMIT

from consts import daytimeStart
from consts import daytimeEnd

display       = lcddriver.lcd()
sensor_type   = 22
tempSensorPin = 26

#Variables for MySQL  
db = mariadb.connect(host="localhost", user="root", passwd="Ykib37lif", db="greenhouse") # replace password with your password  
 

pi_fanRelay   = gpiozero.OutputDevice(
                                       PI_FAN_GPIO
                                     , active_high = False
                                     , initial_value = False
                                     )
gh_fanRelay   = gpiozero.OutputDevice(
                                       GREENHOUSE_FAN_GPIO
                                     , active_high = False
                                     , initial_value = False
                                     )
lightRelay    = gpiozero.OutputDevice(
                                       LIGHTS_GPIO
                                     , active_high = False
                                     , initial_value = False
                                     )
heatRelay     = gpiozero.OutputDevice(
                                       HEATPAD_GPIO
                                     , active_high = False
                                     , initial_value = False
                                     )

def heartbeat():
    threading.Timer(600, heartbeat).start()
    
def measure_pi_temp():
        pitemp = os.popen('vcgencmd measure_temp').readline()
        return pitemp[5:-3]

def measure_gh_temp():
        humidity, ghtemp = Adafruit_DHT.read_retry(sensor_type, tempSensorPin)
        return "%.2f" % round(ghtemp,2)

def dateTime(): #get UNIX time  
        secs = float(time.time())  
        secs = secs*1000  
        return secs
    
heartbeat()

pi_fanState  = False
gh_fanState  = False
lightState   = False
heatpadState = False
isDaytime    = False

while True:
    
    secs          = dateTime()  
    now           = datetime.now()
    current_time  = now.strftime("%H:%M:%S")    
    
    print(str(current_time))
    display.lcd_clear()
    
    piTemp = float(measure_pi_temp())
    print("Pi Temp: " + str(piTemp))
    display.lcd_display_string("Pi Temp: " + str(piTemp), 2)
        
    ghTemp = float(measure_gh_temp())
    print("GH Temp: " + str(ghTemp))
    display.lcd_display_string("GH Temp: " + str(ghTemp), 1)

    cur = db.cursor()
    
    sql = ("""INSERT INTO temperature (datetime, temperature) VALUES (%s,%s)""", (secs, ghTemp))  

    try:  
        print("Writing to the database...")  
        cur.execute(*sql)  
        db.commit()  
        print("Write complete")
  
    except mariadb.Error as error:
        print("Error: {}".format(error))
  
    cur.close()  
      
    
    #Pi temperature control loop
    if (piTemp > PI_TEMP_UPPER_LIMIT and pi_fanState is False):
        pi_fanRelay.on()
        pi_fanState = True
        print("pi fan on")

    elif (piTemp < PI_TEMP_COOLDOWN and pi_fanState is True):
        pi_fanRelay.off()
        pi_fanState = False
        print("pi fan off")

    #Day/Night control loop
    if current_time > daytimeStart and current_time < daytimeEnd:
        isDaytime = True
    
    elif current_time < daytimeStart or current_time > daytimeEnd:
        isDaytime = False

    #If it's daytime
    if isDaytime is True:
        
        #If the lights are off, turn them on
        if lightState is False:
            lightRelay.on()
            lightState = True
            print("Lights on")  
            
            #if it's too hot, turn the fan on
        if ghTemp > GREENHOUSE_FAN_DAYTIME_UPPER_LIMIT and gh_fanState is False:
            gh_fanRelay.on()
            gh_fanState = True
            print("gh fan on")
                         
        #if it's too cool turn the fan off
        if ghTemp < GREENHOUSE_FAN_DAYTIME_LOWER_LIMIT and gh_fanState is True:
            gh_fanRelay.off()
            gh_fanState = False
            print("gh fan off")

        #if its too cool turn the heat mat on
        if ghTemp < HEATPAD_DAYTIME_LOWER_LIMIT and heatpadState is False:
            heatRelay.on()
            heatpadState = True
            print("Heating on")

        #if its too hot turn the heat mat off
        if ghTemp > HEATPAD_DAYTIME_UPPER_LIMIT and heatpadState is True:
            heatRelay.off()
            heatpadState = False
            print("Heating off")
                
    elif isDaytime is False:
        
        #If the lights are on, turn them off
        if lightState is True:
            lightRelay.off()
            lightState = False
            print("Lights Off")  
            
        #if it's too hot, turn the fan on
        if ghTemp > GREENHOUSE_FAN_NIGHTTIME_UPPER_LIMIT and gh_fanState is False:
            gh_fanRelay.on()
            gh_fanState = True
            print("gh fan on")
                    
        #if it's too cool turn the fan off
        if ghTemp < GREENHOUSE_FAN_NIGHTTIME_LOWER_LIMIT and gh_fanState is True:
            gh_fanRelay.off()
            gh_fanState = False
            print("gh fan off")

        #if its too hot turn the heat mat off
        if ghTemp > HEATPAD_NIGHTTIME_UPPER_LIMIT and heatpadState is True:
            heatRelay.off()
            heatpadState = False
            print("Heating off")
            
        #if its too cool turn the heat mat on
        if ghTemp < HEATPAD_NIGHTTIME_LOWER_LIMIT and heatpadState is False:
            heatRelay.on()
            heatpadState = True
            print("Heating on")

    time.sleep(PI_TEMP_POLL_INTERVAL)

db.close()