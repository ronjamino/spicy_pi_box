#
#
#

import os
import time
import gpiozero
import threading
import lcddriver

from datetime import datetime
from consts import PI_FAN_GPIO
from consts import PI_TEMP_POLL_INTERVAL
from consts import PI_TEMP_UPPER_LIMIT
from consts import PI_TEMP_COOLDOWN

display = lcddriver.lcd()
pi_fanRelay = gpiozero.OutputDevice(PI_FAN_GPIO, active_high = False,
                                  initial_value = False)

def heartbeat():
    threading.Timer(50, heartbeat).start()
    
def measure_temp():
        temp = os.popen('vcgencmd measure_temp').readline()
        return temp[5:-3]
        
heartbeat()

pi_fanState = False
while True:
    currTemp = float(measure_temp())
    display.lcd_display_string("Pi Temp: " + str(currTemp), 2)
    
    if (currTemp > PI_TEMP_UPPER_LIMIT and pi_fanState is False):
        pi_fanRelay.on()
        pi_fanState = True

    elif (currTemp < PI_TEMP_COOLDOWN and pi_fanState is True):
        pi_fanRelay.off()
        pi_fanState = False
    
    time.sleep(PI_TEMP_POLL_INTERVAL)