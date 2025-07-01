import time
from machine import Pin

# Blue_Button = Pin(40, Pin.IN, Pin.PULL_UP)
pin_list = []
for n in range(47):
    pin_list.append(Pin(n, Pin.IN, Pin.PULL_UP))
    time.sleep(.1)
    print(n)

# while True:
#     print(f'value + {Blue_Button.value()}')
#     if not Blue_Button.value():
#         print("blue")
#     else:
#         print("nothing")
#         time.sleep(0.3)

for ind, p in enumerate(pin_list):
    if p.value() != 1:
        print(ind)
        
        
# 39, 38, 32, 33, 11, 9, 6, 5, 4, 20, 21, 34, 35, 40, 