#!/usr/bin/env python3
"""Cycle the Limeboard's onboard RGB LED through its 8 colours, then turn it off.

Needs the libgpiod v2 Python bindings (Debian: python3-libgpiod, pip: gpiod).
"""
import glob
import time

import gpiod
from gpiod.line import Direction, Value

RED, GREEN, BLUE = 28, 29, 30  # lines of the "dln2" GPIO chip

COLOURS = {
    "red": (1, 0, 0),
    "green": (0, 1, 0),
    "blue": (0, 0, 1),
    "yellow": (1, 1, 0),
    "cyan": (0, 1, 1),
    "magenta": (1, 0, 1),
    "white": (1, 1, 1),
    "off": (0, 0, 0),
}


def find_chip(label="dln2"):
    """Return the /dev/gpiochipN path of the Limeboard header's GPIO chip."""
    for path in sorted(glob.glob("/dev/gpiochip*")):
        with gpiod.Chip(path) as chip:
            if chip.get_info().label == label:
                return path
    raise SystemExit("no 'dln2' GPIO chip: is the Limeboard I/O firmware running?")


def set_colour(request, rgb):
    request.set_values({line: Value(on) for line, on in zip((RED, GREEN, BLUE), rgb)})


with gpiod.request_lines(
    find_chip(),
    consumer="rgb-led",
    config={(RED, GREEN, BLUE): gpiod.LineSettings(direction=Direction.OUTPUT,
                                                   output_value=Value.INACTIVE)},
) as led:
    for name, rgb in COLOURS.items():
        print(name)
        set_colour(led, rgb)
        time.sleep(1)
