from XRPLib.encoded_motor import EncodedMotor
from XRPLib.board import Board
from XRPLib.differential_drive import DifferentialDrive

#motor1 = EncodedMotor.get_default_encoded_motor(1)
#motor2 = EncodedMotor.get_default_encoded_motor(2)
board = Board.get_default_board()
differentialDrive = DifferentialDrive.get_default_differential_drive()



"""while not (board.is_button_pressed()):
    print(motor1.get_position())
    time.sleep(0.1)"""

"""motor2.set_speed(60)
motor1.set_effort(0.3)
board.wait_for_button()
"""

#differentialDrive.set_speed(40, 20)
"""differentialDrive.straight(20, 0.5)
board.wait_for_button()"""

board.wait_for_button()
for i in range(4):
    differentialDrive.straight(20, 0.5)
    differentialDrive.turn(90, 0.5)
