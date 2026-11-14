#!/usr/bin/env python3
"""oled.py [address]: system status on an SSD1306 128x64 I2C OLED
(default address 0x3C) wired to the Limeboard header's I2C pins.

Needs luma.oled (pip install luma.oled) and smbus2.
"""
import glob
import os
import socket
import sys
import time

from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306
from smbus2 import SMBus

ADDRESS = int(sys.argv[1], 16) if len(sys.argv) > 1 else 0x3C


def find_bus(name="dln2-i2c"):
    """Return the number N of the Limeboard header's /dev/i2c-N."""
    for path in glob.glob("/sys/bus/i2c/devices/i2c-*"):
        with open(path + "/name") as f:
            if f.read().startswith(name):
                return int(os.path.basename(path)[4:])
    raise SystemExit("no 'dln2-i2c' bus: is the Limeboard I/O firmware running?")


def cpu_temp():
    temps = []
    for path in glob.glob("/sys/class/thermal/thermal_zone*/temp"):
        try:
            with open(path) as f:
                temps.append(int(f.read()) // 1000)
        except (OSError, ValueError):
            pass
    return max(temps) if temps else 0


# The bus is opened with smbus2 so that luma sends 32-byte SMBus block writes.
# luma's default (i2c(port=N)) writes the whole 1 KiB frame in one message,
# which the Limeboard's I2C adapter (256 bytes per message) rejects.
device = ssd1306(i2c(bus=SMBus(find_bus()), address=ADDRESS))

while True:
    load = os.getloadavg()[0]
    with canvas(device) as draw:
        draw.rectangle(device.bounding_box, outline="white")
        draw.text((6, 4), "Limeboard", fill="white")
        draw.text((6, 16), socket.gethostname(), fill="white")
        draw.text((6, 28), f"CPU {cpu_temp()} C  load {load:.2f}", fill="white")
        draw.text((6, 46), time.strftime("%H:%M:%S"), fill="white")
    time.sleep(1)
