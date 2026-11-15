#!/usr/bin/env python3
"""blink_rpi_gpio.py: the classic RPi.GPIO blink, on the Limeboard.

Blinks an LED on GPIO17 (header pin 11) until Ctrl-C. On Lime images
RPi.GPIO is rpi-lgpio, set up for the Limeboard by limeboard-compat.
"""
import time

import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.OUT)
try:
    while True:
        GPIO.output(17, GPIO.HIGH)
        time.sleep(0.5)
        GPIO.output(17, GPIO.LOW)
        time.sleep(0.5)
except KeyboardInterrupt:
    pass
finally:
    GPIO.cleanup()
