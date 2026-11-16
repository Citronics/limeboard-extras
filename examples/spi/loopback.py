#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""loopback.py [device]: check the Limeboard's SPI bus with one jumper wire.

Connect MOSI (header pin 19) to MISO (pin 21). Every byte sent then comes
back. Default device: /dev/spidev0.0 (chip select CE0).

Needs py-spidev (Debian: python3-spidev; on Lime images already installed).
"""
import os
import sys

import spidev

path = sys.argv[1] if len(sys.argv) > 1 else "/dev/spidev0.0"
bus, cs = (int(n) for n in path.removeprefix("/dev/spidev").split("."))

spi = spidev.SpiDev()
spi.open(bus, cs)
spi.mode = 0
failures = 0
for speed in (500_000, 1_000_000, 4_000_000):  # the firmware does 328 kHz to 42 MHz
    spi.max_speed_hz = speed
    for size in (4, 256, 1000):  # 1000 bytes: the driver sends 256 at a time
        sent = list(os.urandom(size))
        received = spi.xfer2(sent)
        ok = received == sent
        failures += not ok
        print(f"{speed / 1e6:4.1f} MHz {size:5} bytes: {'ok' if ok else 'MISMATCH'}"
              + ("" if ok else f" (first bytes back: {received[:8]})"))
spi.close()

if failures:
    sys.exit("Check the jumper between pins 19 and 21. All 0xFF: MISO is not connected.")
print("SPI loopback works")
