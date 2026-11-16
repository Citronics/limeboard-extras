#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""blink_gpiozero.py [gpio]: the classic gpiozero blink, on the Limeboard.

Blinks an LED on GPIO17 (header pin 11) until Ctrl-C. Run with the Limeboard
pin factory:

    GPIOZERO_PIN_FACTORY=limeboard python3 blink_gpiozero.py
"""
import sys
from signal import pause

from gpiozero import LED

led = LED(int(sys.argv[1]) if len(sys.argv) > 1 else 17)
led.blink(on_time=0.5, off_time=0.5)
pause()
