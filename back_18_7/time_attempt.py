"""Using time in MicroPython"""

import time
import machine

time.sleep(5)
rtc = machine.RTC()
rtc.datetime((2025, 7, 7, 0, 4, 55, 33, 36))
while True:
    print(rtc.datetime())
    time.sleep(1)

"""
print(time.localtime()[0])
print(time.localtime()[1])
print(time.localtime()[2])
print(time.localtime()[3])
print(time.localtime()[4])
print(time.localtime()[5])
print(time.localtime()[6])
print(time.localtime()[7])
print(time.localtime())


year, month, day, hour, minute, second, weekday, year_day = time.localtime()
print("year", year)
print("month", month)
print("day", day)
print("hour", hour)
print("minute", minute)
print("second", second)
print("weekday", weekday)
print("year_day", year_day)
print("isdst", isdst)
"""