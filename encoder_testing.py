from XRPLib.board import Board
from XRPLib.servo import Servo
from XRPLib.differential_drive import DifferentialDrive
from XRPLib.rangefinder import Rangefinder
from XRPLib.reflectance import Reflectance
import time


"""Encoder Testing"""

servo1 = Servo.get_default_servo(1)
differentialDrive = DifferentialDrive.get_default_differential_drive()
board = Board.get_default_board()
rangefinder = Rangefinder.get_default_rangefinder()
reflectance = Reflectance.get_default_reflectance()

board.wait_for_button()
initial_left = differentialDrive.get_left_encoder_position()
initial_right = differentialDrive.get_right_encoder_position() 

print(f"{initial_left} --- {initial_right}")

while not(rangefinder.distance()) < 15:
    turn_effort = (reflectance.get_right()) - (reflectance.get_left())
    differentialDrive.arcade(0.4, turn_effort*1.3)
differentialDrive.stop()

final_left = differentialDrive.get_left_encoder_position()
final_right = differentialDrive.get_right_encoder_position() 

print(f"{initial_left} --- {initial_right}")
print(f"{final_left} --- {final_right}")

differentialDrive.reset_encoder_position()

initial_left = differentialDrive.get_left_encoder_position()
initial_right = differentialDrive.get_right_encoder_position() 

print(f"{initial_left} --- {initial_right}")

board.wait_for_button()
while differentialDrive.get_left_encoder_position() + differentialDrive.get_right_encoder_position() <= final_left + final_right:
    turn_effort = (reflectance.get_right()) - (reflectance.get_left())
    differentialDrive.arcade(0.4, turn_effort*1.3)
differentialDrive.stop()

final_left = differentialDrive.get_left_encoder_position()
final_right = differentialDrive.get_right_encoder_position() 

print(f"{initial_left} --- {initial_right}")
print(f"{final_left} --- {final_right}")



