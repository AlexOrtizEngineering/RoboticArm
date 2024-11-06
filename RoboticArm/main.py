# ////////////////////////////////////////////////////////////////
# //                     IMPORT STATEMENTS                      //
# ////////////////////////////////////////////////////////////////

import os
import math
import sys
import time

os.environ["DISPLAY"] = ":0.0"

from kivy.app import App
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import *
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.slider import Slider
from kivy.uix.image import Image
from kivy.uix.behaviors import ButtonBehavior
from kivy.clock import Clock
from kivy.animation import Animation
from functools import partial
from kivy.config import Config
from kivy.core.window import Window
from pidev.kivy import DPEAButton
from pidev.kivy import PauseScreen
from time import sleep
from dpeaDPi.DPiComputer import *
from dpeaDPi.DPiStepper import *

# ////////////////////////////////////////////////////////////////
# //                     HARDWARE SETUP                         //
# ////////////////////////////////////////////////////////////////
"""Stepper goes into MOTOR 0
   Limit Sensor for Stepper Motor goes into HOME 0
   Talon Motor Controller for Magnet goes into SERVO 1
   Talon Motor Controller for Air Piston goes into SERVO 0
   Tall Tower Limit Sensor goes in IN 2
   Short Tower Limit Sensor goes in IN 1
   """

# ////////////////////////////////////////////////////////////////
# //                      GLOBAL VARIABLES                      //
# //                         CONSTANTS                          //
# ////////////////////////////////////////////////////////////////
START = True
STOP = False
UP = False
DOWN = True
ON = True
OFF = False
YELLOW = .180, 0.188, 0.980, 1
BLUE = 0.917, 0.796, 0.380, 1
CLOCKWISE = 0
COUNTERCLOCKWISE = 1
ARM_SLEEP = 2.5
DEBOUNCE = 0.10

lowerTowerPositionFromUpper = 535
upperTowerPosition = 780

STEPPER_NUM = 0
MICROSTEPPING = 8
STEPPER_SPEED = 100
MAGNET_NUM = 1
MAGNET_STATUS = OFF
AIR_NUM = 0
AIR_STATUS = OFF
globalArmPosition = 0

# ////////////////////////////////////////////////////////////////
# //            DECLARE APP CLASS AND SCREENMANAGER             //
# //                     LOAD KIVY FILE                         //
# ////////////////////////////////////////////////////////////////
class MyApp(App):

    def build(self):
        self.title = "Robotic Arm"
        return sm

Builder.load_file('main.kv')
Window.clearcolor = (.1, .1,.1, 1) # (WHITE)


# ////////////////////////////////////////////////////////////////
# //                    SLUSH/HARDWARE SETUP                    //
# ////////////////////////////////////////////////////////////////
sm = ScreenManager()

dpiStepper = DPiStepper()
dpiStepper.setBoardNumber(STEPPER_NUM)
if not dpiStepper.initialize():
    print("Communication with the DPiStepper board failed.")
dpiStepper.enableMotors(False)

dpiComputer = DPiComputer()
dpiComputer.initialize()

# ////////////////////////////////////////////////////////////////
# //                       MAIN FUNCTIONS                       //
# //             SHOULD INTERACT DIRECTLY WITH HARDWARE         //
# ////////////////////////////////////////////////////////////////
	
class MainScreen(Screen):
    armPosition = 0
    grabbingBall = False
    # lastClick = time.clock()

    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.initialize()

    # def debounce(self):
    #     processInput = False
    #     currentTime = time.clock()
    #     if (currentTime - self.lastClick) > DEBOUNCE:
    #         processInput = True
    #     self.lastClick = currentTime
    #     return processInput

    """
        Precondition: MAGNET_STATUS is correctly declared
        Switches the magnet between on and off, runs when a button is pressed
    """
    def toggleMagnet(self):
        global MAGNET_STATUS
        if MAGNET_STATUS == OFF:
            self.pickUpBall()
        elif MAGNET_STATUS == ON:
            self.dropBall()
        else:
            print("Error toggling magnet")

    """
        Turns the magnet off, dropping the ball
    """
    def dropBall(self):
        global MAGNET_STATUS
        dpiComputer.writeServo(MAGNET_NUM, 90)
        MAGNET_STATUS = OFF
        print("Magnet turned off")

    """
        Turns the magnet on, picking up the ball
    """
    def pickUpBall(self):
        global MAGNET_STATUS
        dpiComputer.writeServo(MAGNET_NUM, 180)
        MAGNET_STATUS = ON
        print("Magnet turned on")

    """
        Precondition: No components are moving, and their statuses are correctly accounted for. Robotic Arm is at home (position 0)
        Runs when the "Start" button is pressed; will either move ball to the other tower or will deposit ball in tall tower if ball is already being held
    """
    def auto(self):
        self.setArmPosition(1)
        Clock.schedule_once(lambda dt: self.auto_interact(), DEBOUNCE)

    """
        Automatically interacts with ball based on location
    """
    def auto_interact(self):
        if self.isBallOnTallTower() or self.isBallOnShortTower():
            self.auto_move(2)
            Clock.schedule_once(lambda dt: self.auto_move(1), DEBOUNCE)
        else:
            sleep(1)
            Clock.schedule_once(lambda dt: self.homeArm(), DEBOUNCE)

    """
        Precondition: num is equal to 1 or 2
        Automatically moves arm, called in auto_interact()
    """
    def auto_move(self, num):
        sleep(1)
        self.setArmPosition(num)
        if num == 1:
            sleep(1)
            Clock.schedule_once(lambda dt: self.homeArm(), DEBOUNCE)
            Clock.schedule_once(lambda dt: self.lowerArm(), DEBOUNCE)

    """
        Precondition: AIR_STATUS is properly declared
        Switches between lowering and raising Robotic Arm
    """
    def toggleArm(self):
        global AIR_STATUS
        if AIR_STATUS == OFF:
            self.raiseArm()
        elif AIR_STATUS == ON:
            self.lowerArm()
        else:
            print("Error toggling arm")

    """
        Turns on air, raising arm
    """
    def raiseArm(self):
        global AIR_STATUS
        dpiComputer.writeServo(AIR_NUM, 180)
        AIR_STATUS = ON
        print("Arm raised")

    """
        Turns off air, lowering arm
    """
    def lowerArm(self):
        global AIR_STATUS
        dpiComputer.writeServo(AIR_NUM, 90)
        AIR_STATUS = OFF
        print("Arm lowered")

    """
        Sets arm position based on its last location to avoid collisions with the towers
    """
    def setArmPosition(self, position):
        global globalArmPosition
        if position == 0:
            self.homeArm(-1)
            self.lowerArm()
            self.set_arm_position(0)
        elif position == 1:
            if self.armPosition == 0:
                self.raiseArm()
                self.moveArm(upperTowerPosition)
            elif self.armPosition == 2:
                self.moveArm(-1 * lowerTowerPositionFromUpper)
            else:
                print("Error setting position")
                return
            sleep(DEBOUNCE)
            self.check_for_ball("tall")
            self.set_arm_position(1)
        elif position == 2:
            self.moveArm(lowerTowerPositionFromUpper)
            sleep(DEBOUNCE)
            self.check_for_ball("short")
            self.set_arm_position(2)
        else:
            print("Error setting arm position")

    """
        Updates variables based on new position
    """
    def set_arm_position(self, position_value):
        global globalArmPosition
        globalArmPosition = position_value
        self.armPosition = position_value
        self.ids.armControlLabel.text = "Arm Position: " + str(position_value)

    """
        Grabs or drops ball based on location, or don't do anything if ball isn't there
    """
    def check_for_ball(self, tower):
        boolean = ''
        if tower == "tall":
            boolean = self.isBallOnTallTower()
        elif tower == "short":
            boolean = self.isBallOnShortTower()
        else:
            print("tower variable incorrectly defined")
        self.interact_with_tower(boolean)
        sleep(0.5)
        Clock.schedule_once(lambda dt: self.raiseArm(), DEBOUNCE)

    """
        Either picks up the ball, drops the ball, or ignores the ball if it isn't there
    """
    def interact_with_tower(self, boolean):
        if self.grabbingBall:
            self.lowerArm()
            self.grabbingBall = False
            sleep(0.5)
            Clock.schedule_once(lambda dt: self.dropBall(), DEBOUNCE)
        elif not self.grabbingBall and boolean:
            self.lowerArm()
            self.grabbingBall = True
            sleep(1)
            Clock.schedule_once(lambda dt: self.pickUpBall(), DEBOUNCE)

    """
        Moves arm in steps and gets the position
    """
    def moveArm(self, distanceToMoveInSteps):
        dpiStepper.moveToRelativePositionInSteps(STEPPER_NUM, distanceToMoveInSteps, True)
        print("Arm moved")

    """
        Returns position of arm
        Postcondition: Positive or negative int
    """
    def getArmPosition(self):
        val, position = dpiStepper.getCurrentPositionInSteps(STEPPER_NUM)
        return position

    """
        Precondition: If initial = True, the metal screw on the Robotic Arm servo is to the right of the Limit Sensor connected to Home
        directionTowardHome: -1 is clockwise, 1 is counterclockwise
        Moves arm to home either clockwise or counterclockwise; on first call, checks that directionTowardHome is the correct value
    """
    def homeArm(self, directionTowardHome = -1, initial = False):
        # arm.home(self.homeDirection)
        if initial:
            if directionTowardHome not in [-1, 1]:
                print("Error homing arm")
            else:
                dpiStepper.moveToHomeInSteps(STEPPER_NUM, directionTowardHome, STEPPER_SPEED * MICROSTEPPING, 1600)
        else:
            position = self.getArmPosition()
            if position < 0:
                dpiStepper.moveToHomeInSteps(STEPPER_NUM, 1, STEPPER_SPEED * MICROSTEPPING, 1600)
            elif position > 0:
                dpiStepper.moveToHomeInSteps(STEPPER_NUM, -1, STEPPER_SPEED * MICROSTEPPING, 1600)
            else:
                print("Arm already home")
        self.initialize_motor_settings()
        self.set_arm_position(0)
        print("Arm moved to home")

    """
        Precondition: Tall tower sensor is connected to IN 2 on dpiComputer
        Postcondition: Returns True or False
    """
    def isBallOnTallTower(self):
        sensor_val = dpiComputer.readDigitalIn(dpiComputer.IN_CONNECTOR__IN_2)
        if sensor_val == 0:
            sleep(DEBOUNCE)
            if sensor_val == 0:
                return True
        return False

    """
        Precondition: Short tower sensor is connected to IN 1 on dpiComputer
        Postcondition: Returns True or False
    """
    def isBallOnShortTower(self):
        sensor_val = dpiComputer.readDigitalIn(dpiComputer.IN_CONNECTOR__IN_1)
        if sensor_val == 0:
            sleep(DEBOUNCE)
            if sensor_val == 0:
                return True
        return False

    """
        Initializes stepper motor settings, homes arm, turns off magnet
    """
    def initialize(self):
        self.initialize_motor_settings()
        self.homeArm(-1, True)
        self.dropBall()

    """
        Precondition: Stepper motor is connected to dpiStepper board
        Sets microstepping, speed, and acceleration of Stepper motor
    """
    def initialize_motor_settings(self):
        global MICROSTEPPING
        dpiStepper.setMicrostepping(MICROSTEPPING)

        speed_steps_per_second = STEPPER_SPEED * MICROSTEPPING
        dpiStepper.setSpeedInStepsPerSecond(STEPPER_NUM, speed_steps_per_second)
        dpiStepper.setAccelerationInStepsPerSecondPerSecond(STEPPER_NUM, speed_steps_per_second)
        print("Motor settings initialized")

    def resetColors(self):
        self.ids.armControl.color = YELLOW
        self.ids.magnetControl.color = YELLOW
        self.ids.auto.color = BLUE

    def quit(self):
        MyApp().stop()
    
sm.add_widget(MainScreen(name = 'main'))


# ////////////////////////////////////////////////////////////////
# //                          RUN APP                           //
# ////////////////////////////////////////////////////////////////
if __name__ == "__main__":
    # Window.fullscreen = True
    # Window.maximize()
    MyApp().run()

# Arm lowered
dpiComputer.writeServo(AIR_NUM, 90)
print("Arm lowered")

# Magnet off
dpiComputer.writeServo(MAGNET_NUM, 90)
print("Magnet turned off")

# Arm homed
if globalArmPosition == 2:
    dpiStepper.moveToHomeInSteps(STEPPER_NUM, 1, STEPPER_SPEED * MICROSTEPPING, 2000)
else:
    dpiStepper.moveToHomeInSteps(STEPPER_NUM, -1, STEPPER_SPEED * MICROSTEPPING, 2000)

# Stepper disabled
dpiStepper.enableMotors(OFF)
print("Stepper motor disabled")