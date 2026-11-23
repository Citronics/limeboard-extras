# Using the Limeboard header

The Limeboard is a Citronics carrier board for the Fairphone 2 and 3. Its
STM32 microcontroller runs the **Limeboard I/O firmware**, which turns the
board's 40-pin header into ordinary Linux devices, numbered like a
Raspberry Pi's. Programs talk to them with the same tools and libraries as
on a Pi: gpiozero, libgpiod, i2c-tools, smbus2, luma.oled. Which Raspberry
Pi HATs work is in [HATS.md](HATS.md).

This guide covers using the header with that firmware installed. For
building or flashing the firmware itself, see the `limeboard-firmware`
repository.

- [What the firmware provides](#what-the-firmware-provides)
- [Header pinout](#header-pinout) (complete version: [PINOUT.md](PINOUT.md))
- [Turning the buses on](#turning-the-buses-on)
- [Serial console, firmware and raspi-config](#serial-console-firmware-and-raspi-config)
- [Software to install](#software-to-install)
- [Finding the devices](#finding-the-devices)
- [gpiozero](#gpiozero)
- [Differences from a Raspberry Pi](#differences-from-a-raspberry-pi)
- [Which Raspberry Pi HATs work](HATS.md)
- Examples:
  1. [Onboard RGB LED](examples/onboard-led/README.md)
  2. [I2C OLED display](examples/i2c-oled/README.md)
  3. [LED on a header GPIO](examples/gpio-led/README.md)
  4. [The phone's motion sensors](examples/phone-sensors/README.md)
  5. [Your own devices in Home Assistant](examples/home-assistant/README.md)
  6. [SPI](examples/spi/README.md)
  7. [CAN with an SPI CAN HAT](examples/can/README.md)
- Reusable code:
  - [`limeboard-compat`](limeboard-compat/README.md): gpiozero, RPi.GPIO and
    Adafruit Blinka on the Limeboard, without setup
  - [`limeboard-gpiozero`](limeboard-gpiozero/README.md): the gpiozero pin
    factory, as a package for `pip install`
  - [`phone_sensors.py`](examples/phone-sensors/phone_sensors.py): reads
    the phone's motion and light sensors

## What the firmware provides

The STM32 connects to the phone over USB. The `citronics-dln2` driver of
Citronics kernels (`modinfo citronics-dln2`) turns it into these devices:

| Linux device | What it is |
|---|---|
| GPIO chip `citronics-dln2`, lines 0-27 | header GPIO0 to GPIO27 (BCM numbering) |
| GPIO chip `citronics-dln2`, lines 28, 29, 30 | onboard RGB LED: red, green, blue (1 = on) |
| GPIO chip `citronics-dln2`, line 31 | onboard user button (input) |
| I2C bus `citronics-dln2-i2c-…-0` (Pi i2c1) | SDA GPIO2 (pin 3), SCL GPIO3 (pin 5), 100 kHz: the usual I2C bus |
| I2C bus `citronics-dln2-i2c-…-1` (Pi i2c0) | SDA GPIO0 (pin 27), SCL GPIO1 (pin 28), 100 kHz ([second I2C bus](examples/i2c-oled/README.md#on-the-second-i2c-bus)) |
| SPI 0: `/dev/spidev0.0`, `/dev/spidev0.1` (Pi spi0) | MOSI GPIO10, MISO GPIO9, SCLK GPIO11, CE0 GPIO8, CE1 GPIO7 ([SPI example](examples/spi/README.md)) |
| SPI 1: `/dev/spidev1.0`, `1.1`, `1.2` (Pi spi1) | MOSI GPIO20, MISO GPIO19, SCLK GPIO21, CE0 GPIO18, CE1 GPIO17, CE2 GPIO16 |
| IIO ADC `citronics-dln2-adc`, 8 channels, 10-bit, 0-3.3 V | GPIO5, 12, 16, 22, 17, 25, 20, 23 |
| `/dev/serial0`, a link to the USB serial port `/dev/ttyACM*` | UART TXD GPIO14, RXD GPIO15: [the only UART](#one-uart) |

The GPIO line number is the BCM GPIO number, so GPIO17 is line 17 of the
`citronics-dln2` chip. As on a Raspberry Pi, the I2C and SPI buses are off until you
turn them on ([below](#turning-the-buses-on)). A pin is a plain GPIO until a
function uses it: a bus that is on claims its pins when a program first uses
it (an SPI chip select on its own first use), the ADC on first use, and the
UART while its serial port is open. A claimed pin stays with its function
until the STM32 resets.

### Bus names

The buses keep the Raspberry Pi's names, so that Pi documentation and
tutorials match the pins. On a Pi, i2c1 is the I2C bus of pins 3 and 5, and
i2c0, on GPIO0/1, is the bus of the HAT ID EEPROM. The Limeboard has both,
but its Linux device numbers are given in the order the buses appear, after
the phone's own:

| Pins | Pi name | Linux device (Fairphone 2) | `i2cdetect -l` name ends in |
|---|---|---|---|
| 3, 5 (GPIO2/3) | i2c1 | `/dev/i2c-1` | `-0` |
| 27, 28 (GPIO0/1) | i2c0 | `/dev/i2c-2` | `-1` |
| 19, 21, 23, chip selects 24, 26 | spi0 | `/dev/spidev0.0`, `0.1` | |
| 38, 35, 40, chip selects 12, 11, 36 | spi1 | `/dev/spidev1.0`, `1.1`, `1.2` | |

The numbers are those with both I2C buses on: Linux numbers the buses in
the order they appear, so with only i2c0 on it is `/dev/i2c-1`.
`/dev/i2c-0` is the phone's own I2C controller, so the Limeboard's i2c0 cannot
be `/dev/i2c-0`. Find a bus by its name instead of its number:
`i2cdetect -l | grep citronics-dln2`. The `-0` or `-1` at the end of the name is the
Limeboard I2C port. GPIO0/1 are a plain I2C bus here: the Limeboard does not
read HAT EEPROMs.

### One UART

The header has a single UART, on GPIO14 (TXD, pin 8) and GPIO15 (RXD,
pin 10), as `/dev/ttyACM*`, with `/dev/serial0` as its link, as on a Pi. The STM32's other UARTs have no usable TX/RX
pair on the header: one has its TX on GPIO3, which is I2C, the other its RX
on the onboard LED. Each UART also needs its own USB serial interface, and
the STM32's USB has no endpoints left for a second one. For more serial
ports, use USB serial adapters in the board's USB ports.

Check that the firmware is running:

```sh
lsusb | grep 1209:0001         # the Limeboard I/O firmware
gpiodetect | grep citronics-dln2         # its GPIO chip
i2cdetect -l | grep citronics-dln2       # its I2C buses, once turned on
```

## Turning the buses on

As on a Raspberry Pi, the I2C and SPI buses are off by default. Turn them on
in `/etc/limeboard/config.txt`, with the lines a Pi's `config.txt` uses:

| Line | Bus | Pins |
|---|---|---|
| `dtparam=i2c_arm=on` | i2c1, the usual I2C bus | SDA GPIO2 (pin 3), SCL GPIO3 (pin 5) |
| `dtoverlay=i2c0` or `dtparam=i2c_vc=on` | i2c0 | SDA GPIO0 (pin 27), SCL GPIO1 (pin 28) |
| `dtparam=spi=on` | spi0, `/dev/spidev0.0` and `0.1` | GPIO9-11, CE0 GPIO8, CE1 GPIO7 |
| `dtoverlay=spi0-1cs` | spi0 with CE0 only | |
| `dtoverlay=spi1-1cs`, `spi1-2cs`, `spi1-3cs` | spi1, `/dev/spidev1.0` to `1.2` | GPIO19-21, CE0 GPIO18, CE1 GPIO17, CE2 GPIO16 |
| `spi0_cs1=mcp3008` | a kernel driver on a chip select ([SPI example](examples/spi/README.md#choosing-the-devices-on-the-chip-selects)) | |

Then apply the file with `limeboard-config`. Unlike on a Pi, there is no
reboot: the change applies at once, or, if a program is using a bus, when
the board's STM32 next resets. As on a Pi, an edit also applies at the next
boot (`limeboard-config.service`).

```sh
sudo limeboard-config                   # apply /etc/limeboard/config.txt
sudo limeboard-config enable i2c1       # add the line and apply, like raspi-config
sudo limeboard-config disable spi1
limeboard-config show                   # i2c1: on, i2c0: off, spi0: off, ...
```

`limeboard-config` writes the settings of the `citronics-dln2` driver to
`/etc/modprobe.d/limeboard.conf`, for the next boot, and applies them at
once; do not edit that file. Lines the Limeboard does not support are
reported and ignored.

## Serial console, firmware and raspi-config

`limeboard-config` also does what `raspi-config` does for a Pi's serial port
and bootloader:

**Login console on the header UART.** With a 3.3 V USB-serial cable on pins
8 (TXD), 10 (RXD) and a GND pin, at 115200 baud:

```sh
sudo limeboard-config enable serial-console     # adds serial_console=on to config.txt
```

A login prompt then runs on `/dev/serial0`, also after resets of the STM32.
It is off by default, as on a Pi: the UART is then free for HATs.

**STM32 firmware.** The Limeboard ships with CircuitPython on its STM32,
and keeps it: the Limeboard I/O firmware, which this guide needs, is
opt-in. The images carry it, and one command replaces CircuitPython with it,
saving the board's previous firmware in `/var/backups/limeboard` first:

```sh
sudo limeboard-config firmware install # CircuitPython -> Limeboard I/O firmware
limeboard-config firmware              # running: 1.3, shipped: 1.3
sudo limeboard-config firmware update  # flash the shipped one, about 5 s
```

Once a board runs the Limeboard I/O firmware, a newer one shipped by a
package upgrade goes onto it by itself; a board on CircuitPython is never
flashed without that `install`. To go back to CircuitPython:
`sudo limeboard-config firmware install /var/backups/limeboard/<date>/flash.bin`
(the CIRCUITPY files are saved next to it, in `files/`).

The update restarts the STM32 into its ROM bootloader, flashes it and waits
for the firmware to come back, with the buses set up again. If the STM32 is
left in its bootloader, run the update again. To reach the bootloader by
hand, hold the user button while powering the board.

**Home Assistant agent.** `limeboard-ha` (opt-in, off until set up) shows
the board, its LED, its button and the phone's sensors in Home Assistant:

```sh
sudo limeboard-config ha setup         # broker, user, password; then starts it
```

See [limeboard-ha/README.md](limeboard-ha/README.md).

**raspi-config.** HAT installers often run commands such as
`raspi-config nonint do_i2c 0`. The Limeboard has a `raspi-config` that
answers them through `limeboard-config`:

| Command | Does |
|---|---|
| `raspi-config nonint do_i2c 0` / `1` | i2c1 on / off |
| `raspi-config nonint do_spi 0` / `1` | spi0 on / off |
| `raspi-config nonint do_serial_cons 0` / `1` | login console on / off |
| `raspi-config nonint do_serial_hw 0` | the UART: always on |
| `raspi-config nonint get_i2c` (`get_spi`, …) | prints 0 when on, 1 when off |
| `raspi-config nonint is_pi` | fails: this is not a Pi |

Other commands fail with a message. `raspi-config` without arguments shows
`limeboard-config`'s help.

## CPU budget

The Limeboard has no battery, so nothing absorbs a current peak. A radio
powering up (the modem when it starts, the Wi-Fi firmware after a crash)
while the four CPUs run at full speed can pull the supply under the PMIC's
lockout and reset the board. In Debug mode, powered by a computer's USB port,
this happens readily; Default mode on USB-C PD or PoE has more headroom.

On the Fairphone 2 the image therefore holds the CPUs to a budget, the same in
both modes so a board can move between them without changes. Like a Raspberry
Pi's overclock presets, it has levels:

| Level | CPU ceiling (FP2) | |
|---|---|---|
| `default` | 1574 MHz | the image's budget, safe even in Debug mode |
| `medium` | 1728 MHz | one CPU step higher |
| `high` | 1958 MHz | two steps higher |
| `yolo` | 2265 MHz | no limit: only with a strong supply in Default mode, or with the modem and the Wi-Fi off |

```sh
limeboard-config cpu-budget          # the level and the CPU ceiling
sudo limeboard-config cpu-budget     # the same, with the ceiling of each level
sudo limeboard-config cpu-budget medium
sudo limeboard-config cpu-budget default
```

A level applies at once and at every boot (`/etc/default/citronics-power-budget`).
It needs a kernel with CPU power capping (the FP2 rc kernel) and the
`citronics-lime-fp2` package. Turning the radios off for `yolo` means
`sudo systemctl disable --now rmtfs ModemManager` and no Wi-Fi connection:
even unused, the modem powers up at every boot.

## Header pinout

The header follows the Raspberry Pi layout. [PINOUT.md](PINOUT.md) has the
complete pinout: all 40 pins with their GPIO, STM32 pin and functions, the
onboard LED, button and other STM32 signals, and the board's jumpers and
switches.

![Limeboard 40-pin header pinout](images/limeboard-pinout.svg)

| Function | Pin | Pin | Function |
|---:|:-:|:-:|:---|
| 3.3 V | 1 | 2 | 5 V |
| GPIO2 (I2C SDA) | 3 | 4 | 5 V |
| GPIO3 (I2C SCL) | 5 | 6 | GND |
| GPIO4 | 7 | 8 | GPIO14 (UART TXD) |
| GND | 9 | 10 | GPIO15 (UART RXD) |
| GPIO17 (ADC 4) | 11 | 12 | GPIO18 |
| GPIO27 | 13 | 14 | GND |
| GPIO22 (ADC 3) | 15 | 16 | GPIO23 (ADC 7) |
| 3.3 V | 17 | 18 | GPIO24 |
| GPIO10 (SPI MOSI) | 19 | 20 | GND |
| GPIO9 (SPI MISO) | 21 | 22 | GPIO25 (ADC 5) |
| GPIO11 (SPI SCLK) | 23 | 24 | GPIO8 (SPI CE0) |
| GND | 25 | 26 | GPIO7 (SPI CE1) |
| GPIO0 | 27 | 28 | GPIO1 |
| GPIO5 (ADC 0) | 29 | 30 | GND |
| GPIO6 | 31 | 32 | GPIO12 (ADC 1) |
| GPIO13 | 33 | 34 | GND |
| GPIO19 | 35 | 36 | GPIO16 (ADC 2) |
| GPIO26 | 37 | 38 | GPIO20 (ADC 6) |
| GND | 39 | 40 | GPIO21 |

The pins are 3.3 V logic. Never connect 5 V to a GPIO. The header works
only with the board's mode switch S3 in `DFLT`.

## Software to install

**Lime images** (Citronics Debian, Ubuntu and Buildroot images for the
Lime carrier) already include gpiozero 2.0.1 with the Limeboard pin factory
(see [gpiozero](#gpiozero)), RPi.GPIO (rpi-lgpio) and the Blinka board
definition ([limeboard-compat](limeboard-compat/README.md)), lgpio, psutil
and dfu-util.

**Debian and Ubuntu images**, for the other examples:

```sh
sudo apt install gpiod python3-libgpiod i2c-tools python3-smbus2 python3-pil python3-venv
```

- `gpiod` provides the command line tools `gpiodetect`, `gpioinfo`,
  `gpioget`, `gpioset` and `gpiomon` (libgpiod v2).
- `python3-libgpiod` provides the `gpiod` Python module (libgpiod v2 API).
- `i2c-tools` provides `i2cdetect`, `i2cget` and `i2cset`.

For libraries that are not packaged, such as luma.oled, use a virtual
environment that also sees the system packages:

```sh
python3 -m venv --system-site-packages ~/limeboard-venv
~/limeboard-venv/bin/pip install luma.oled
```

**Buildroot images:** these include `i2c-tools`, Python 3 and gpiozero. The
LED examples also have a variant that needs only `/sys/class/gpio`.

The examples access `/dev/gpiochip*` and `/dev/i2c-*`. Run them as root
(with `sudo`), or give your user access to those device files.

## Finding the devices

The GPIO chip and I2C bus numbers depend on the order in which devices
appear, so look them up by name instead of hard-coding `gpiochip4` or
`i2c-1`.

Shell:

```sh
chip=$(gpiodetect | awk '/\[citronics-dln2\]/ { print $1 }')     # e.g. gpiochip4
bus=$(i2cdetect -l | awk '/citronics-dln2-i2c/ { sub("i2c-", "", $1); print $1 }')   # e.g. 1
```

Python:

```python
import glob, os, gpiod

def find_chip(label="citronics-dln2"):
    for path in sorted(glob.glob("/dev/gpiochip*")):
        with gpiod.Chip(path) as chip:
            if chip.get_info().label == label:
                return path

def find_i2c_bus(name="citronics-dln2-i2c"):
    for path in glob.glob("/sys/bus/i2c/devices/i2c-*"):
        with open(path + "/name") as f:
            if f.read().startswith(name):
                return int(os.path.basename(path)[4:])
```

## gpiozero

[gpiozero](https://gpiozero.readthedocs.io/), the usual GPIO library of
Raspberry Pi tutorials, works on the Limeboard through the **`limeboard` pin
factory**. RPi.GPIO and Adafruit Blinka work too: see
[limeboard-compat](limeboard-compat/README.md). A pin factory is gpiozero's back end. The Limeboard one is
gpiozero's lgpio factory, the default on a Raspberry Pi 5, opened on the
firmware's `citronics-dln2` GPIO chip. Select it with an environment variable, and Pi
code runs unchanged:

```sh
GPIOZERO_PIN_FACTORY=limeboard python3 my_script.py
GPIOZERO_PIN_FACTORY=limeboard pinout      # prints the Limeboard header
```

On Lime images, [limeboard-compat](limeboard-compat/README.md) selects it
for every Python program, so the environment variable is not needed there.

Pins take the same names as on a Pi: `LED(17)`, `LED("GPIO17")`,
`LED("BOARD11")`. The onboard RGB LED and the user button are `LED_R`,
`LED_G`, `LED_B` and `BUTTON`:

```python
from gpiozero import RGBLED, Button

led = RGBLED("LED_R", "LED_G", "LED_B", pwm=False)
button = Button("BUTTON", pull_up=None, active_state=True)
button.when_pressed = lambda: led.toggle()
```

What to keep in mind:
- **Use `pwm=False`** for LEDs, and do not use `PWMLED`. gpiozero would
  generate PWM in software over USB, which flickers.
- **Use `pull_up=None` with `active_state`** for buttons, and wire the
  pull resistor yourself. The firmware does not provide pull-up or
  pull-down resistors.
- **gpiozero's SPI devices** (MCP3008 and the like) are not tested on the
  Limeboard. For analog inputs, use the board's own ADC.
- The factory lives in `limeboard_gpiozero.py`. In Python, without the
  environment variable:
  `Device.pin_factory = limeboard_gpiozero.LimeboardFactory()`.
- Lime images include it. For other systems,
  [`limeboard-gpiozero/`](limeboard-gpiozero/README.md) is the same factory
  as a package for `pip install`.

## Differences from a Raspberry Pi

- **No hardware PWM.** A GPIO is either on or off. Every change travels
  over USB and takes about a millisecond, so software PWM flickers. Fading
  an LED or driving a servo needs an external PWM chip, such as a PCA9685
  on the I2C bus.
- **Raspberry Pi libraries.** gpiozero, RPi.GPIO and Adafruit Blinka work
  through [limeboard-compat](limeboard-compat/README.md). `pigpio` and
  wiringPi access the Pi's processor directly and do not work. libgpiod (the
  `gpiod` Python module and the `gpio*` tools) works on any Linux board.
- **I2C messages are limited to 256 bytes.** Most drivers send small
  messages and are not affected. A library that writes a whole frame buffer
  in one message must split it; see the [OLED example](examples/i2c-oled/README.md).
- **No device tree overlays.** On a Pi, most HATs work through a
  `dtoverlay=` line that loads their kernel driver. The Limeboard's buses
  come over USB and cannot take overlays, so HAT kernel drivers do not load.
  Programs that drive the chips themselves (through I2C, GPIO or the serial
  port) work. See [HATS.md](HATS.md).
- **SPI chips without device tree.** `/dev/spidev0.x` and `1.x` work as on
  a Pi. To put a kernel driver on a chip select instead, set it in
  `/etc/limeboard/config.txt` (see the [SPI example](examples/spi/README.md)).
- **One I2C bus and one SPI bus.** The Pi's second SPI bus (GPIO16-21) is
  not available.
- **ADC.** The header has eight 10-bit analog inputs, which the Pi lacks.
  They appear in `/sys/bus/iio/devices/iio:deviceN/` (name `citronics-dln2-adc`).

## The Home Assistant agent and the onboard LED

When the Home Assistant agent (`limeboard-ha`, opt-in) runs, it uses the
onboard LED and button (lines 28-31). A line in use by one program cannot be
requested by another, and the tools report `Device or resource busy`.
Control the LED from Home Assistant, or stop the agent before you use it
from your own programs:

```sh
sudo systemctl stop limeboard-ha            # Debian, Ubuntu
/etc/init.d/S95limeboard-ha stop            # Buildroot
```

Stopping the agent releases the lines. The header's GPIO0-27 are never
used by the agent. The agent itself is built on gpiozero, psutil and
paho-mqtt; its README in the `limeboard-ha` package describes it.

## License

MIT (`LICENSE`), Copyright (c) 2026 Citronics: the tools, Python packages and
examples here. The Limeboard I/O firmware is MIT too
([Citronics/limeboard-firmware](https://github.com/Citronics/limeboard-firmware));
the kernel's `citronics-dln2` driver is GPL-2.0, as the kernel.
