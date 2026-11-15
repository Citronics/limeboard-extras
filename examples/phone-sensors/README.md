# Example 4: the phone's motion sensors

The Fairphone 2 on the Limeboard has an accelerometer, a gyroscope and a
magnetometer. Some phones also have light and proximity sensors. The
phone's sensor hub serves them as Linux IIO devices named `qcom-smgr-accel`,
`qcom-smgr-gyro`, and so on.

[`phone_sensors.py`](phone_sensors.py) is a small module that reads them.
Copy it next to your script:

```python
from phone_sensors import PhoneSensors

with PhoneSensors() as sensors:            # or PhoneSensors(kinds=("accel",))
    print(sensors.kinds)                   # ['gyro', 'accel', 'mag']
    print(sensors.read())
# {'accel_x': 0.31, 'accel_y': -0.94, 'accel_z': 9.43,
#  'gyro_x': 0.0014, ..., 'mag_z': -0.27}
```

| Values | Unit |
|---|---|
| `accel_x`, `accel_y`, `accel_z` | m/s² (about 9.8 on the axis pointing up) |
| `gyro_x`, `gyro_y`, `gyro_z` | rad/s |
| `mag_x`, `mag_y`, `mag_z` | gauss |
| `light` | lux |
| `prox` | greater than 0 when something is near |

Each `read()` returns a fresh sample of every sensor. It takes a few
milliseconds per sensor.

## Example: tilt and compass

[`tilt.py`](tilt.py) prints the phone's tilt and a compass heading twice a
second:

```sh
sudo python3 tilt.py
```

```
sensors: accel, mag
tilt   5.8°   heading 147.5°
```

The tilt comes from the accelerometer: it is the angle between gravity and
the phone's z axis. The heading comes from the magnetometer and is valid
while the phone lies flat. It is not calibrated, so expect an offset.

## Notes

- Only one program at a time can read a sensor. `limeboard-ha` streams
  them to Home Assistant, so stop it first (`systemctl stop limeboard-ha` or
  `/etc/init.d/S95limeboard-ha stop`), or read the values from Home
  Assistant or MQTT instead.
- Reading needs root, or write access to the IIO devices' sysfs files and
  `/dev/iio:device*`.
- The sensor hub only runs after the phone's ADSP firmware has booted, a
  few seconds after the system starts. `PhoneSensors()` then finds no
  sensors yet.
