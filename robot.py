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


##############################################################################
# Configuration

clearance_threshold_mm = 220
duty_percentage_forward = 70
duty_percentage_stop = 0
pin_motor_left = 26
pin_motor_right = 5
pin_motor_servo = 17
ping_ultrasound_trigger = 21
ping_ultrasound_echo = 22
servo_centre = 6.5
servo_right = 4
servo_left = 11



########################################################################
# Set up ui

setScreenColor(0x000000)
label0 = M5TextBox(16, 85, "Text", lcd.FONT_DejaVu40, 0xFFFFFF, rotate=0)
label1 = M5TextBox(16, 156, "Text", lcd.FONT_DejaVu40, 0xFFFFFF, rotate=0)
label2 = M5TextBox(180, 15, "Text", lcd.FONT_DejaVu18, 0xFFFFFF, rotate=0)
label0.setText('Distance')


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
        

# Set up ultrasound
sensor = HCSR04(trigger_pin=ping_ultrasound_trigger, echo_pin=ping_ultrasound_echo, echo_timeout_us=1000000)


# Set up PWM
left = machine.Pin(pin_motor_left, mode=machine.Pin.OUT, pull=machine.Pin.PULL_UP)
right = machine.Pin(pin_motor_right, mode=machine.Pin.OUT, pull=machine.Pin.PULL_UP)
PWM_left = machine.PWM(pin_motor_left, freq=1000, duty=0, timer=0)
PWM_right = machine.PWM(pin_motor_right, freq=1000, duty=0, timer=0)
PWM_servo = machine.PWM(pin_motor_servo, freq=50, duty=0, timer=0)



class ClearanceChecker():
    def isClear(self):
        distance = sensor.distance_mm()
        label1.setText(str(distance))
        return distance > clearance_threshold_mm


################################################################################
# Motion State Machine

MotionState = {}
class MoveForward():
    def run(self):
        PWM_left.duty(duty_percentage_forward)
        PWM_right.duty(duty_percentage_forward+5)
        clearance = ClearanceChecker()
        while clearance.isClear() is True:
          wait_ms(50)
        Stop()
        return "LookLeft"
MotionState["MoveForward"] = MoveForward()


class TurnLeft():
    def run(self):
        PWM_left.duty(0)
        PWM_right.duty(duty_percentage_forward+5)
        wait_ms(500)
        Stop()
        return "LookAhead"    
MotionState["TurnLeft"] = TurnLeft()


class TurnRight():
    def run(self):
        PWM_left.duty(duty_percentage_forward)
        PWM_right.duty(0)
        wait_ms(500)
        Stop()
        return "LookAhead"      
MotionState["TurnRight"] = TurnRight()


class LookLeft():
    def run(self):
        PWM_servo.duty(servo_left)
        wait_ms(2000)
        if (ClearanceChecker().isClear() is True):
          return "TurnLeft"
        else:
          return "LookRight"
MotionState["LookLeft"] = LookLeft()


class LookRight():
    def run(self):
        PWM_servo.duty(servo_right)
        wait_ms(2000)
        if (ClearanceChecker().isClear() is True):
            return "TurnRight"
        else:
            return "Stop"
MotionState["LookRight"] = LookRight()


class LookAhead():
    def run(self):
      PWM_servo.duty(servo_centre)
      wait_ms(300)
      if (ClearanceChecker().isClear() is True):
        return "MoveForward"
      else:
        return "Stop"
      
MotionState["LookAhead"] = LookAhead()


############################################################################
# Reset state machine

def buttonA_wasPressed():
    RunStateMachine()
    pass
btnA.wasPressed(buttonA_wasPressed)


############################################################################
# Stop state machine

def buttonB_wasPressed():
  nextState = "Stop"
  pass
btnB.wasPressed(buttonB_wasPressed)


############################################################################


def Stop():
  PWM_left.duty(duty_percentage_stop)
  PWM_right.duty(duty_percentage_stop)
  PWM_servo.duty(servo_centre)
        
def RunStateMachine():
    nextState = "LookAhead"
    while nextState is not "Stop":
      label2.setText(nextState)
      motionState = MotionState[nextState]
      nextState = motionState.run()
    Stop()

# Acknowledge download
speaker.tone(200, 20)

############################################################################
# Run state machine
