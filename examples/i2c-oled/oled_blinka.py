#!/usr/bin/env python3
"""oled_blinka.py: the SSD1306 OLED with Adafruit's CircuitPython driver,
through Blinka. Draws a frame and a moving bar until Ctrl-C.

Needs: pip install adafruit-blinka adafruit-circuitpython-ssd1306
"""
import time

import adafruit_ssd1306
import board

# page_addressing=True: the driver sends the frame one 128-byte page at a
# time. Its default, the whole frame in one message, is more than the
# Limeboard's I2C adapter accepts (256 bytes).
oled = adafruit_ssd1306.SSD1306_I2C(128, 64, board.I2C(), addr=0x3C, page_addressing=True)

x = 0
try:
    while True:
        oled.fill(0)
        oled.rect(0, 0, 128, 64, 1)
        oled.fill_rect(4 + x, 28, 16, 8, 1)
        oled.show()
        x = (x + 8) % 104
        time.sleep(0.1)
except KeyboardInterrupt:
    oled.fill(0)
    oled.show()
