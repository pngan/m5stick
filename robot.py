# Controls robot with 2 PWM drive motors, ultrasound distance sensor
# Moves forward if clearance ahead of robot is more than 200mm, otherwise stops


from m5stack import *
from m5ui import *
from uiflow import *
import machine
import time
from machine import Pin
import os
from easyIO import *

MotionState = {}
class MoveForward():
    def run(self):
        while True:
            distance = sensor.distance_mm()
            label1.setText(str(distance))
            if distance < 200:
                duty = 0
            else:
                duty = 70
            PWM_left.duty(duty)
            PWM_right.duty(duty+5)
            
            wait_ms(100)

            return "LookLeft"

MotionState["MoveForward"] = MoveForward()

class LookLeft():
    def run(self):
        while True:
            # Turn sensor left
            # if clear
            #     return "TurnLeft"
            # else
            #     return "LookRight"

MotionState["LookLeft"] = LookLeft()

class LookRight():
    def run(self):
        while True:
            # Turn sensor right
            # if clear
            #     return "TurnRight"
            # else
            #     return "Stop"

MotionState["LookRight"] = LookRight()


class TurnLeft():
    def run(self):
        while True:
            # Turn robot left
            # return "MoveForward"     

MotionState["TurnLeft"] = TurnLeft()


class TurnRight():
    def run(self):
        while True:
            # Turn robot right
            # return "MoveForward"        


MotionState["TurnRight"] = TurnRight()

######################################################################
class HCSR04:
    """
    Driver to use the untrasonic sensor HC-SR04.
    The sensor range is between 2cm and 4m.
    The timeouts received listening to echo pin are converted to OSError('Out of range')
    """
    # echo_timeout_us is based in chip range limit (400cm)
    def __init__(self, trigger_pin, echo_pin, echo_timeout_us=500*2*30):
        """
        trigger_pin: Output pin to send pulses
        echo_pin: Readonly pin to measure the distance. The pin should be protected with 1k resistor
        echo_timeout_us: Timeout in microseconds to listen to echo pin. 
        By default is based in sensor limit range (4m)
        """
        self.echo_timeout_us = echo_timeout_us
        # Init trigger pin (out)
        self.trigger = Pin(trigger_pin, mode=Pin.OUT, pull=None)
        self.trigger.value(0)
 
        # Init echo pin (in)
        self.echo = Pin(echo_pin, mode=Pin.IN, pull=None)
 
    def _send_pulse_and_wait(self):
        """
        Send the pulse to trigger and listen on echo pin.
        We use the method `machine.time_pulse_us()` to get the microseconds until the echo is received.
        """
        self.trigger.value(0) # Stabilize the sensor
        time.sleep_us(5)
        self.trigger.value(1)
        # Send a 10us pulse.
        time.sleep_us(10)
        self.trigger.value(0)
        try:
            pulse_time = machine.time_pulse_us(self.echo, 1, self.echo_timeout_us)
            return pulse_time
        except OSError as ex:
            if ex.args[0] == 110: # 110 = ETIMEDOUT
                raise OSError('Out of range')
            raise ex
 
    def distance_mm(self):
        """
        Get the distance in milimeters without floating point operations.
        """
        pulse_time = self._send_pulse_and_wait()
 
        # To calculate the distance we get the pulse_time and divide it by 2 
        # (the pulse walk the distance twice) and by 29.1 becasue
        # the sound speed on air (343.2 m/s), that It's equivalent to
        # 0.34320 mm/us that is 1mm each 2.91us
        # pulse_time // 2 // 2.91 -> pulse_time // 5.82 -> pulse_time * 100 // 582 
        mm = pulse_time * 100 // 582
        return mm
 
    def distance_cm(self):
        """
        Get the distance in centimeters with floating point operations.
        It returns a float
        """
        pulse_time = self._send_pulse_and_wait()
 
        # To calculate the distance we get the pulse_time and divide it by 2 
        # (the pulse walk the distance twice) and by 29.1 becasue
        # the sound speed on air (343.2 m/s), that It's equivalent to
        # 0.034320 cm/us that is 1cm each 29.1us
        cms = (pulse_time / 2) / 29.1
        return cms
        
########################################################################
# Set up ui

setScreenColor(0x000000)
label0 = M5TextBox(16, 85, "Text", lcd.FONT_DejaVu40, 0xFFFFFF, rotate=0)
label1 = M5TextBox(16, 156, "Text", lcd.FONT_DejaVu40, 0xFFFFFF, rotate=0)
label2 = M5TextBox(180, 15, "Text", lcd.FONT_DejaVu18, 0xFFFFFF, rotate=0)
label0.setText('Distance')

# Set up ultrasound
sensor = HCSR04(trigger_pin=21, echo_pin=22,echo_timeout_us=1000000)

# Set up PWM
left = machine.Pin(26, mode=machine.Pin.OUT, pull=machine.Pin.PULL_UP)
right = machine.Pin(5, mode=machine.Pin.OUT, pull=machine.Pin.PULL_UP)
PWM_left = machine.PWM(26, freq=1000, duty=0, timer=0)
PWM_right = machine.PWM(5, freq=1000, duty=0, timer=0)


# Set up state machine


# Acknowledge download
speaker.tone(200, 20)




