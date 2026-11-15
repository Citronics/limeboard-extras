#!/usr/bin/env python3
"""blink_blinka.py: the classic CircuitPython blink, on the Limeboard with
Adafruit Blinka. Blinks an LED on GPIO17 (header pin 11) until Ctrl-C.
"""
import time

import board
import digitalio

led = digitalio.DigitalInOut(board.D17)
led.direction = digitalio.Direction.OUTPUT
try:
    while True:
        led.value = True
        time.sleep(0.5)
        led.value = False
        time.sleep(0.5)
except KeyboardInterrupt:
    led.value = False
