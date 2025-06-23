from time import sleep

from machine import Pin, I2C

from apds9960.const import *
from apds9960.device import uAPDS9960 as APDS9960

bus = I2C(0, sda=Pin(4), scl=Pin(5))

apds = APDS9960(bus)

print("Light Sensor Test")
print("=================")
apds.enableLightSensor()

oval = -1
while True:
    sleep(0.25)
    red = apds.readRedLight()
    green = apds.readGreenLight()
    blue = apds.readBlueLight()
    if red != oval:
        print(f"R: {red}, G: {green}, B:{blue}")
        oval = blue
