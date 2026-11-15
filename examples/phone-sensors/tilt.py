#!/usr/bin/env python3
"""tilt.py: print the phone's tilt and heading twice a second, until Ctrl-C.

The tilt is the angle between the phone's z axis and the vertical, from the
accelerometer. The heading is a rough compass angle from the magnetometer,
valid while the phone lies flat.
"""
import math
import time

from phone_sensors import PhoneSensors

with PhoneSensors(kinds=("accel", "mag")) as sensors:
    print("sensors:", ", ".join(sensors.kinds))
    try:
        while True:
            v = sensors.read()
            tilt = math.degrees(math.atan2(math.hypot(v["accel_x"], v["accel_y"]), v["accel_z"]))
            line = f"tilt {tilt:5.1f}°"
            if "mag_x" in v:
                heading = math.degrees(math.atan2(v["mag_y"], v["mag_x"])) % 360
                line += f"   heading {heading:5.1f}°"
            print(line, flush=True)
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
