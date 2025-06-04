from XRPLib.board import Board
from XRPLib.servo import Servo
from XRPLib.differential_drive import DifferentialDrive
from XRPLib.rangefinder import Rangefinder
from XRPLib.reflectance import Reflectance
import time


"""Delivery Challenge"""

servo1 = Servo.get_default_servo(1)
differentialDrive = DifferentialDrive.get_default_differential_drive()
board = Board.get_default_board()
rangefinder = Rangefinder.get_default_rangefinder()
reflectance = Reflectance.get_default_reflectance()

#Servo movement
#board.wait_for_button()
"""servo1.set_angle(0)
time.sleep(1)
servo1.set_angle(60)
time.sleep(1)
"""
#Get distance
"""while not (board.is_button_pressed()):
    print(f'{rangefinder.distance()}')
    time.sleep(0.1)
"""

#Get reflectance
"""
while not (board.is_button_pressed()):
    print(f'{reflectance.get_left()} --- {reflectance.get_right()}')
    time.sleep(0.1)

board.wait_for_button()
servo1.set_angle(0)
time.sleep(2)
differentialDrive.straight(-5, 0.5)
servo1.set_angle(60)
time.sleep(2)
differentialDrive.straight(5, 0.5)
time.sleep(1)
servo1.set_angle(0)
"""



board.wait_for_button()
initial_left = differentialDrive.get_left_encoder_position()
initial_right = differentialDrive.get_right_encoder_position() 

while not(rangefinder.distance()) < 15:
    turn_effort = (reflectance.get_right()) - (reflectance.get_left())
    differentialDrive.arcade(0.45, turn_effort*1.4)
differentialDrive.stop()

before_turn_left = differentialDrive.get_left_encoder_position()
before_turn_right = differentialDrive.get_right_encoder_position()

differentialDrive.turn(180, 0.5)
servo1.set_angle(0)
time.sleep(1)

after_turn_left = differentialDrive.get_left_encoder_position()
after_turn_right = differentialDrive.get_right_encoder_position()

excess = (after_turn_right + after_turn_left) - (before_turn_right + before_turn_left)

differentialDrive.straight(-5, 0.5)
servo1.set_angle(60)
time.sleep(1)

differentialDrive.straight(5, 0.5)

final_left = differentialDrive.get_left_encoder_position()
final_right = differentialDrive.get_right_encoder_position() 

differentialDrive.reset_encoder_position()

while differentialDrive.get_left_encoder_position() + differentialDrive.get_right_encoder_position() <= final_left + final_right - excess:
    turn_effort = (reflectance.get_right()) - (reflectance.get_left())
    differentialDrive.arcade(0.45, turn_effort*1.4)
differentialDrive.stop()

differentialDrive.turn(180, 0.5)
servo1.set_angle(0)
