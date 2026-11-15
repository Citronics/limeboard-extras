#!/usr/bin/env python3
"""Cycle the onboard RGB LED through its 8 colours with gpiozero, then turn it
off. Press the user button to stop early.

Run with the Limeboard pin factory:

    GPIOZERO_PIN_FACTORY=limeboard python3 rgb_led_gpiozero.py
"""
from time import sleep

from gpiozero import Button, RGBLED

# One LED, three colour channels. pwm=False: each channel is on or off.
led = RGBLED("LED_R", "LED_G", "LED_B", pwm=False)
button = Button("BUTTON", pull_up=None, active_state=True)

COLOURS = {
    "red": (1, 0, 0),
    "green": (0, 1, 0),
    "blue": (0, 0, 1),
    "yellow": (1, 1, 0),
    "cyan": (0, 1, 1),
    "magenta": (1, 0, 1),
    "white": (1, 1, 1),
}

for name, colour in COLOURS.items():
    if button.is_pressed:
        break
    print(name)
    led.color = colour
    sleep(1)
led.off()
