from XRPLib.board import Board
from machine import Timer
import time

brightness = 0.1

board = Board.get_default_board()

# Conversion from hue to RGB
def hue_to_rgb(hue):
    # Initialize RGB values
    r = 0;
    g = 0;
    b = 0;
    
    # Ensure hue is in range of [0,360)
    hue %= 360
    
    if(hue < 120):
        # Yellow
        r = (120 - hue) / 120 * 255
        g = (hue -   0) / 120 * 255
        b = 0
    elif(hue < 240):
        # Cyan
        hue -= 120
        r = 0
        g = (120 - hue) / 120 * 255
        b = (hue -   0) / 120 * 255
    else:
        # Magenta
        hue -= 240
        r = (hue -   0) / 120 * 255
        g = 0
        b = (120 - hue) / 120 * 255
    
    # Return RGB as tuple of ints in range of [0,255]
    return (int(r), int(g), int(b))

def update_rgb_led(timer):
    hue = time.ticks_ms() / 10
    rgb = hue_to_rgb(hue)
    r = int(rgb[0] * brightness)
    g = int(rgb[1] * brightness)
    b = int(rgb[2] * brightness)
    board.set_rgb_led(r, g, b)

board.led_blink(1)
rgb_led_timer = Timer(-1)
rgb_led_timer.init(freq = 100, callback = update_rgb_led)