# SPDX-License-Identifier: MIT
"""Read the phone's motion and light sensors on a Limeboard.

The Fairphone 2's sensor hub (its ADSP) serves the accelerometer, gyroscope,
magnetometer, and light and proximity sensors when present, as buffered Linux
IIO devices named "qcom-smgr-<kind>". A sample in a buffer is the int32
channels, padding to 8 bytes, then an int64 timestamp.

    from phone_sensors import PhoneSensors

    with PhoneSensors() as sensors:
        print(sensors.read())     # {"accel_x": 0.12, ..., "mag_z": -0.31}

Only one program at a time can read a sensor's buffer: stop limeboard-ha
first, which streams them to Home Assistant.
"""
import glob
import os
import struct

# Channels of each kind of sensor, in buffer order
LAYOUT = {
    "accel": ("accel_x", "accel_y", "accel_z"),   # m/s²
    "gyro": ("gyro_x", "gyro_y", "gyro_z"),       # rad/s
    "mag": ("mag_x", "mag_y", "mag_z"),           # gauss
    "light": ("light",),                          # lux
    "prox": ("prox",),                            # > 0: something is near
}


def _read(path, default=None):
    try:
        with open(path) as f:
            return f.read().strip()
    except OSError:
        return default


def _write(path, value):
    with open(path, "w") as f:
        f.write(value)


def find_sensors():
    """Return {kind: IIO device directory} for the sensors the phone has."""
    found = {}
    for path in glob.glob("/sys/bus/iio/devices/iio:device*"):
        kind = (_read(path + "/name") or "").removeprefix("qcom-smgr-")
        if kind in LAYOUT:
            found[kind] = path
    return found


class PhoneSensors:
    """The phone's sensors, read through their IIO buffers."""

    def __init__(self, kinds=None):
        self._streams = {}
        try:
            for kind, path in find_sensors().items():
                if kinds is None or kind in kinds:
                    self._open(kind, path)
        except OSError:
            self.close()
            raise

    def _open(self, kind, path):
        _write(path + "/buffer/enable", "0")
        for enable in glob.glob(path + "/scan_elements/in_*_en"):
            _write(enable, "1")
        _write(path + "/buffer/length", "1")
        _write(path + "/buffer/enable", "1")
        scales = glob.glob(path + "/in_*_scale")
        scale = float(_read(scales[0], 1)) if scales else 1.0
        size = 24 if len(LAYOUT[kind]) == 3 else 16
        fd = os.open("/dev/" + os.path.basename(path), os.O_RDONLY)
        self._streams[kind] = (path, fd, size, scale)

    @property
    def kinds(self):
        return list(self._streams)

    def read(self):
        """Return a fresh sample of every open sensor, scaled to SI units."""
        values = {}
        for kind, (_, fd, size, scale) in self._streams.items():
            os.read(fd, size)  # the buffered sample may be old: the next one is fresh
            raw = struct.unpack_from(f"<{len(LAYOUT[kind])}i", os.read(fd, size))
            values.update({name: round(v * scale, 4) for name, v in zip(LAYOUT[kind], raw)})
        return values

    def close(self):
        for path, fd, _, _ in self._streams.values():
            os.close(fd)
            _write(path + "/buffer/enable", "0")
        self._streams.clear()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
