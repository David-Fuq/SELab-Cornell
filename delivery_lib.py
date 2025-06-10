import time

def delivery(pestolink, servo1, differentialDrive, board, rangefinder, reflectance):
    if(pestolink.get_button(0)):
        return None
    
    print("EN DELIVERY")
    
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
    
    
    
    #board.wait_for_button()
    initial_left = differentialDrive.get_left_encoder_position()
    initial_right = differentialDrive.get_right_encoder_position() 
    if(pestolink.get_button(0)):
        return None
    
    while not(rangefinder.distance()) < 15:
        if(pestolink.get_button(0)):
            return None
        #pestolink.feed()
        turn_effort = (reflectance.get_right()) - (reflectance.get_left())
        differentialDrive.arcade(0.4, turn_effort*1.4)
    differentialDrive.stop()
    
    before_turn_left = differentialDrive.get_left_encoder_position()
    before_turn_right = differentialDrive.get_right_encoder_position()
    if(pestolink.get_button(0)):
        return None
    #pestolink.feed()
    differentialDrive.turn(180, 0.5)
    if(pestolink.get_button(0)):
        return None
    servo1.set_angle(0)
    if(pestolink.get_button(0)):
        return None
    time.sleep(1)
    if(pestolink.get_button(0)):
        return None
    #pestolink.feed()
    after_turn_left = differentialDrive.get_left_encoder_position()
    after_turn_right = differentialDrive.get_right_encoder_position()
    if(pestolink.get_button(0)):
        return None
    
    excess = (after_turn_right + after_turn_left) - (before_turn_right + before_turn_left)
    #pestolink.feed()
    differentialDrive.straight(-5, 0.5)
    if(pestolink.get_button(0)):
        return None
    servo1.set_angle(60)
    time.sleep(1)
    
    differentialDrive.straight(5, 0.5)
    if(pestolink.get_button(0)):
        return None
    #pestolink.feed()
    final_left = differentialDrive.get_left_encoder_position()
    final_right = differentialDrive.get_right_encoder_position() 
    
    differentialDrive.reset_encoder_position()
    
    while differentialDrive.get_left_encoder_position() + differentialDrive.get_right_encoder_position() <= final_left + final_right - excess:
        #pestolink.feed()
        if(pestolink.get_button(0)):
            return None
        turn_effort = (reflectance.get_right()) - (reflectance.get_left())
        differentialDrive.arcade(0.4, turn_effort*1.4)
    differentialDrive.stop()
    
    differentialDrive.turn(180, 0.5)
    if(pestolink.get_button(0)):
        return None
    servo1.set_angle(0)
    time.sleep(1)
    if(pestolink.get_button(0)):
        return None
    servo1.set_angle(100)
