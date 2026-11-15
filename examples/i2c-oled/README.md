# Example 2: an I2C OLED display

This example shows the board's status on a 0.96" SSD1306 OLED module
(128x64 pixels, I2C). These modules are sold by many vendors and usually
answer at address 0x3C.

## Wiring

| OLED pin | Header pin |
|---|---|
| GND | 6 (GND) |
| VCC | 1 or 17 (3.3 V) |
| SDA | 3 (GPIO2, I2C SDA) |
| SCL | 5 (GPIO3, I2C SCL) |

Most SSD1306 modules carry their own regulator and pull-up resistors and
accept 3.3 V or 5 V on VCC. Their SDA and SCL lines must stay at 3.3 V.

## Check that the display answers

```sh
i2cdetect -l | grep dln2             # e.g. "i2c-1  i2c  dln2-i2c-1-1.5:1.0-0  I2C adapter"
sudo i2cdetect -y -r 1               # use the bus number found above
```

`3c` should appear in the table. The address `28` also appears: that is
the board's own USB-C power controller, which shares this bus (GPIO2/3).

## Install luma.oled

[luma.oled](https://luma-oled.readthedocs.io/) is the library most
Raspberry Pi tutorials use for these displays. It draws with Pillow.

Debian and Ubuntu images:

```sh
sudo apt install python3-smbus2 python3-pil python3-venv
python3 -m venv --system-site-packages ~/limeboard-venv
~/limeboard-venv/bin/pip install luma.oled
```

## Run the example

[`oled.py`](oled.py) shows the host name, CPU temperature, load and time,
refreshed every second:

```sh
sudo ~/limeboard-venv/bin/python oled.py          # address 0x3C
sudo ~/limeboard-venv/bin/python oled.py 3d       # another address
```

## On the second I2C bus

The Limeboard has a second I2C bus on GPIO0 (SDA, pin 27) and GPIO1 (SCL,
pin 28), where a Raspberry Pi has its i2c0 (see
[Bus names](../../README.md#bus-names)). To use it, move the display's SDA to
pin 27 and SCL to pin 28, keep VCC and GND, then:

```sh
i2cdetect -l | grep dln2              # two buses: names end in -0 (GPIO2/3) and -1 (GPIO0/1)
sudo i2cdetect -y -r 2                # the -1 bus: /dev/i2c-2 on a Fairphone 2
sudo ~/limeboard-venv/bin/python oled.py 3c 1
```

`oled.py`'s second argument is the Limeboard I2C port: 0 for GPIO2/3, 1 for
GPIO0/1. With Blinka, the second bus is `busio.I2C(board.SCL0, board.SDA0)`.

The second bus needs a kernel whose `dln2` driver adds a bus for each port.
Its pins stay plain GPIOs until something uses the bus. Unlike on GPIO2/3, no
other device of the board sits on it.

## The one difference from a Raspberry Pi

Pi tutorials create the display like this:

```python
from luma.core.interface.serial import i2c
serial = i2c(port=1, address=0x3C)
```

With that interface luma writes the whole frame (1 KiB) in one I2C message.
The Limeboard's I2C adapter accepts at most 256 bytes per message, so the
write fails with `OSError: [Errno 95] Operation not supported`. Open the bus
with smbus2 and give it to luma instead. luma then sends the frame in
32-byte blocks:

```python
from smbus2 import SMBus
from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306

device = ssd1306(i2c(bus=SMBus(1), address=0x3C))
```

Everything else in luma, including canvases, fonts, images and the other
display drivers (sh1106, ssd1309 and others), works unchanged:

```python
from luma.core.render import canvas

with canvas(device) as draw:
    draw.rectangle(device.bounding_box, outline="white")
    draw.text((10, 20), "Hello Limeboard", fill="white")
```

## With Adafruit's CircuitPython driver (Blinka)

[`oled_blinka.py`](oled_blinka.py) uses `adafruit-circuitpython-ssd1306`
through Blinka. The same limit applies, and the driver has an option for it:
`page_addressing=True` sends the frame one 128-byte page at a time.

```python
import board, adafruit_ssd1306

oled = adafruit_ssd1306.SSD1306_I2C(128, 64, board.I2C(), page_addressing=True)
oled.rect(0, 0, 128, 64, 1)
oled.show()
```

Without it, `show()` fails with `OSError: [Errno 95] Operation not supported`.

Other I2C sensors and devices (temperature sensors, IO expanders, PWM
controllers) use small messages and work with their usual Python or kernel
drivers. Only drivers that send more than 256 bytes at once need care.
