# Import necessary modules
print("START")
from machine import Pin, ADC
import bluetooth
import time
import math
from XRPLib.gamepad import *
from pestolink import PestoLinkAgent
from XRPLib.board import Board
from XRPLib.servo import Servo
from XRPLib.differential_drive import DifferentialDrive
from XRPLib.rangefinder import Rangefinder
from XRPLib.reflectance import Reflectance
from delivery_lib import *

#Choose the name your robot shows up as in the Bluetooth paring menu
#Name should be 8 characters max!


# Create an instance of the PestoLinkAgent class




robot_name = "XRP_3"

pestolink = PestoLinkAgent(robot_name)
servo1 = Servo.get_default_servo(1)
differentialDrive = DifferentialDrive.get_default_differential_drive()
board = Board.get_default_board()
rangefinder = Rangefinder.get_default_rangefinder()
reflectance = Reflectance.get_default_reflectance()


print(f"Hello from {robot_name} !")
servo1.set_angle(90)

# Start an infinite loop
while True:
    if pestolink.is_connected():  # Check if a BLE connection is established
        rotation = -1 * pestolink.get_axis(0)
        throttle = -1 * pestolink.get_axis(1)
        
        differentialDrive.arcade(throttle, rotation)
        
        if(pestolink.get_button(0)):
            servo1.set_angle(110)
        else:
            servo1.set_angle(90)
        if(pestolink.get_button(1)):
            differentialDrive.turn(180, 0.5)
        if(pestolink.get_button(2)):
            print("En el boton 2")
            delivery(pestolink, servo1, differentialDrive, board, rangefinder, reflectance)
            
            
        
        batteryVoltage = (ADC(Pin("BOARD_VIN_MEASURE")).read_u16())/(1024*64/14)
        pestolink.telemetryPrintBatteryVoltage(batteryVoltage)

    else: #default behavior when no BLE connection is open
        differentialDrive.arcade(0, 0)
        servo1.set_angle(50)
