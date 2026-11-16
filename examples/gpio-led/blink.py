#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""blink.py [gpio]: blink an LED wired to a header GPIO (default GPIO17, pin 11).

Needs the libgpiod v2 Python bindings (Debian: python3-libgpiod, pip: gpiod).
"""
import glob
import sys
import time

import gpiod
from gpiod.line import Direction, Value

GPIO = int(sys.argv[1]) if len(sys.argv) > 1 else 17  # BCM number = citronics-dln2 line


def find_chip(label="citronics-dln2"):
    """Return the /dev/gpiochipN path of the Limeboard header's GPIO chip."""
    for path in sorted(glob.glob("/dev/gpiochip*")):
        with gpiod.Chip(path) as chip:
            if chip.get_info().label == label:
                return path
    raise SystemExit("no 'citronics-dln2' GPIO chip: is the Limeboard I/O firmware running?")


with gpiod.request_lines(
    find_chip(),
    consumer="blink",
    config={GPIO: gpiod.LineSettings(direction=Direction.OUTPUT)},
) as led:
    print(f"blinking GPIO{GPIO}, Ctrl-C to stop")
    try:
        while True:
            led.set_value(GPIO, Value.ACTIVE)
            time.sleep(0.5)
            led.set_value(GPIO, Value.INACTIVE)
            time.sleep(0.5)
    except KeyboardInterrupt:
        led.set_value(GPIO, Value.INACTIVE)
