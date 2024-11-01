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

lowerTowerPosition = 60
upperTowerPosition = 76

STEPPER_NUM = 0
MAGNET_NUM = 1
MAGNET_STATUS = OFF
AIR_NUM = 0
AIR_STATUS = OFF

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

print()
# ////////////////////////////////////////////////////////////////
# //                       MAIN FUNCTIONS                       //
# //             SHOULD INTERACT DIRECTLY WITH HARDWARE         //
# ////////////////////////////////////////////////////////////////
	
class MainScreen(Screen):
    armPosition = 0
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
    def pickUpBall(self, drop = False):
        print("Magnet turned on")
        global MAGNET_STATUS
        dpiComputer.writeServo(MAGNET_NUM, 180)
        MAGNET_STATUS = ON
        if drop:
            sleep(5)
            self.dropBall()
        print("Magnet turned on")

    """
        Precondition: No components are moving, and their statuses are correctly accounted for
        Runs when the "Start" button is pressed
    """
    def auto(self): #TODO fill out
        print("Run the arm automatically here")
        #if ball is on top tower, grab it, move it to bottom, maneuver over top tower, and go back to home
        #if ball is on bottom tower, maneuver over top tower, grab it, move it to top and go back to home

    def toggleArm(self): #TODO fill out with actual function
        print("Process arm movement here")

        dpiStepper.moveToRelativePositionInSteps(STEPPER_NUM, -10, True) #remove later
        val, position = dpiStepper.getCurrentPositionInSteps(STEPPER_NUM)
        print("Position: " + str(position))
        self.homeArm(-1) #remove later?

    def setArmPosition(self, position): #TODO fill out
        print("Move arm here")

    """
        directionTowardHome: -1 is clockwise, 1 is counterclockwise
    """
    def homeArm(self, directionTowardHome): # TODO get this to work clockwise and counterclockwise and make movement fluid
        # arm.home(self.homeDirection)
        if directionTowardHome not in [-1, 1]:
            print("Error homing arm")
            return

        val, position = dpiStepper.getCurrentPositionInSteps(STEPPER_NUM)
        print("Position: " + str(position))
        # if position < 0:
        #     dpiStepper.moveToHomeInSteps(STEPPER_NUM, -1, 100, 1000)
        # elif position > 0:
        #     dpiStepper.moveToHomeInSteps(STEPPER_NUM, 1, 100, 1000)
        # else:
        #     print("Arm already home")

        dpiStepper.moveToHomeInSteps(STEPPER_NUM, directionTowardHome, 100, 1000)
        print("Arm moved to home")
        
    def isBallOnTallTower(self): #TODO check that this works
        sensor_val = dpiComputer.readDigitalIn(dpiComputer.IN_CONNECTOR__IN_2)
        if sensor_val == 0:
            sleep(DEBOUNCE)
            if sensor_val == 0:
                return True
        return False

    def isBallOnShortTower(self): #TODO check that this works
        sensor_val = dpiComputer.readDigitalIn(dpiComputer.IN_CONNECTOR__IN_1)
        if sensor_val == 0:
            sleep(DEBOUNCE)
            if sensor_val == 0:
                return True
        return False

    def initialize(self):
        self.homeArm(-1)
        #sleep(2)
        #self.moveToRelativePositionInSteps(10)
        self.dropBall()

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

# Stepper disabled
dpiStepper.enableMotors(OFF)
print("Stepper motor disabled")

#Magnet off
dpiComputer.writeServo(MAGNET_NUM, 90)
print("Magnet turned off")