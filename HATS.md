# Raspberry Pi HATs on the Limeboard

The Limeboard's header has the Raspberry Pi layout, so most HATs fit
mechanically. Whether a HAT *works* depends on what it needs from the Pi:
some need only the signals the Limeboard I/O firmware provides, others need
parts of the Pi that the board does not have.

In short:

| | |
|---|---|
| **Works** | HATs that use GPIO, I2C, SPI or the serial port, with their usual gpiozero, RPi.GPIO, Blinka or spidev libraries: relays, buttons, LEDs, I2C sensors, I2C ADCs, PCA9685 PWM and servo boards, I2C OLED displays, real-time clocks, GPS data |
| **No** | audio (I2S), displays driven by kernel drivers or DPI, HATs that need the Pi's PWM or microsecond timing, HATs whose kernel driver needs a device tree overlay |

Only the I2C pins (header pins 3 and 5) have been checked with real hardware.
The other pins follow the Raspberry Pi layout as defined by the firmware.
Check the power pins with a multimeter before plugging in a HAT: the current
the board's 3.3 V and 5 V pins can supply is not documented.

## Why: what is different from a Pi

On a Raspberry Pi, the header pins belong to the main processor. On the
Limeboard, they belong to an STM32 microcontroller, which reaches the phone
over USB. Linux's `dln2` drivers make it look like a Pi header, with these
differences:

| | Raspberry Pi | Limeboard |
|---|---|---|
| GPIO | direct, microsecond timing | over USB: about 1 ms per operation. Edge events work |
| Pull-up / pull-down resistors | internal, per pin | none: use external resistors |
| PWM | 2 hardware channels | none |
| I2C | i2c1 on pins 3/5 (and i2c0 on pins 27/28), up to 400 kHz and more | i2c1 and i2c0 on the same pins, 100 kHz, 256 bytes per message; see [Bus names](README.md#bus-names) |
| SPI | spi0, spi1 (`/dev/spidev0.x`, `1.x`) | the same two buses, slower: a USB round trip per 256 bytes ([below](#spi)) |
| UART | `/dev/serial0`, and more UARTs on the Pi 4 and 5 | one: `/dev/ttyACM*`, a USB serial port ([why](README.md#one-uart)) |
| I2S / PCM audio | yes | no |
| DPI display, GPCLK | yes | no |
| `config.txt`: `dtparam=i2c_arm=on`, `dtparam=spi=on`, `dtoverlay=spi1-3cs`, `dtoverlay=i2c0` | yes, buses off by default | the same lines in `/etc/limeboard/config.txt`, buses off by default ([Turning the buses on](README.md#turning-the-buses-on)) |
| Device tree overlays for chips (`dtoverlay=mcp2515`…) | yes | no: the buses come over USB. SPI chips: `spi0_cs0=mcp2515,irq=25` in `config.txt`; I2C chips: `new_device` |
| HAT ID EEPROM (GPIO0/1) | read at boot, configures the HAT | not read: GPIO0/1 are plain GPIOs |

### Kernel drivers and device tree overlays

Most HATs that are "plug and play" on a Pi rely on a kernel driver loaded by
a device tree overlay, which also tells the driver which pins carry the
chip's interrupt and reset lines. That mechanism does not exist for the
Limeboard's USB-attached buses, so those drivers do not load.

Two things still work:
- **Programs that drive the chip themselves,** through I2C, GPIO or the
  serial port. Most Python HAT libraries work this way.
- **Kernel drivers for simple I2C chips** that need no interrupt or extra
  pin. Add them by hand:

  ```sh
  echo ds3231 0x68 | sudo tee /sys/bus/i2c/devices/i2c-1/new_device
  ```

  (`i2c-1` is the Limeboard's bus here; `i2cdetect -l | grep dln2` shows its
  number.)

### SPI

The SPI buses work like a Pi's spi0 and spi1: `/dev/spidev0.0` and `0.1`,
`/dev/spidev1.0`, `1.1` and `1.2`, for py-spidev, gpiozero and Blinka. This
needs a kernel with the Limeboard's dln2 changes (`modinfo -p spi_dln2` lists
`spi0_cs0` to `spi1_cs3`). Older kernels have one SPI controller and no
`/dev/spidev`.

As on a Pi, the buses are off until `/etc/limeboard/config.txt` turns them
on (`dtparam=spi=on`, `dtoverlay=spi1-3cs`). A Pi puts a kernel driver on a
chip select with a `dtoverlay=` for that chip. On the Limeboard that is a
line in the same file, with the chip's name and optionally its interrupt
GPIO:

```sh
spi0_cs0=mcp2515,irq=25,speed=10000000
```

The driver must be in the kernel; the Lime kernels do not build SPI chip
drivers yet. See the [SPI example](examples/spi/README.md).

SPI is slower than on a Pi: every transfer of up to 256 bytes is a USB round
trip, so a few hundred KB/s at best, and the clock is 328 kHz to 42 MHz.

### Software that expects a Pi

Most HAT libraries are written for a Raspberry Pi: they import `RPi.GPIO`,
use gpiozero, or use Adafruit Blinka. On the Limeboard, the
[`limeboard-compat`](limeboard-compat/README.md) package, installed on Lime
images, makes all three work unchanged:

- **gpiozero**: the `limeboard` pin factory is selected automatically.
- **RPi.GPIO**: provided by rpi-lgpio (RPi.GPIO on lgpio), pointed at the
  Limeboard's GPIO chip.
- **Adafruit Blinka**: `board` is the Limeboard's, with the Raspberry Pi pin
  names. Install Blinka with pip; it is not part of the images.

The HAT's library therefore usually runs as is, within the limits of this
page. For example, there is no PWM, and I2C messages are at most 256 bytes.
Adafruit's SSD1306 OLED driver, for one, needs `page_addressing=True`.

**pigpio** and **wiringPi** access the Pi's processor directly and do not
work.

## HAT by HAT

### Works

| HAT | Uses | Notes |
|---|---|---|
| Relay HATs, LED and button HATs, Traffic HAT | GPIO | their gpiozero, RPi.GPIO or Blinka libraries |
| Active buzzers (on/off) | GPIO | passive buzzers need PWM, see below |
| I2C sensors: BME280, BME680, BMP280, SHT31, LTR559, IMUs | I2C | `smbus2`-based libraries |
| I2C ADC: ADS1115, ADS1015 | I2C | the board also has its own 8-channel ADC |
| PWM and servo HATs: PCA9685 (Adafruit Servo HAT, PWM HAT, Motor HAT) | I2C | **the way to get PWM** on the Limeboard: the chip generates it |
| I2C OLED displays: SSD1306, SH1106 | I2C | see the [OLED example](examples/i2c-oled/README.md): open the bus with `smbus2` |
| Real-time clocks: DS3231, DS1307, PCF8523 | I2C | kernel driver added with `new_device` (no interrupt needed) |
| I2C GPIO expanders: MCP23017, PCF8574 | I2C | from Python, or the kernel driver without interrupts |
| 1-Wire through an I2C bridge (DS2482) | I2C | kernel driver `ds2482` with `new_device` |
| GPS HATs: position data | UART | point gpsd at `/dev/ttyACM*` |
| RS-485 / serial HATs | UART | `/dev/ttyACM*`. Direction control on a GPIO is slow (about 1 ms) |

### Partly

| HAT | What works | What does not |
|---|---|---|
| Pimoroni Enviro+ | its I2C sensors | the SPI LCD, the particle sensor's control pins |
| Raspberry Pi Sense HAT | its I2C sensors, read directly | the LED matrix and joystick, which use kernel drivers |
| GPS HATs with PPS | position data | the PPS precise-time pulse (kernel driver and microsecond timing) |
| Fan HATs | on and off | speed control (PWM) |
| Automation HATs | relays, inputs and I2C ADC | anything driven by PWM or SPI |

### SPI

| HAT | Notes |
|---|---|
| E-paper displays (Waveshare, Inky) | their refreshes are slow anyway: usable |
| SPI ADCs: MCP3008, MCP3208 | gpiozero's `MCP3008` class, or py-spidev |
| LoRa HATs (SX127x, SX126x) | when their library drives SPI and GPIO from user space |
| SPI LCDs driven from Python | about half a second per full frame |

### No

| HAT | Why |
|---|---|
| Audio: HiFiBerry, IQaudio, pHAT DAC, ReSpeaker microphones | need I2S, which the header does not carry. Use a USB sound card instead |
| SPI displays with kernel drivers: PiTFT, Waveshare 3.5" LCD | need a kernel driver loaded by a device tree overlay |
| DPI displays | the Pi's parallel display signals are not on the header |
| CAN HATs (MCP2515) | possible with `spi0_cs0=mcp2515,irq=…`, but the Lime kernels do not build the CAN driver yet, and its oscillator clock comes from the device tree on a Pi |
| Addressable LEDs from the Pi: Unicorn HAT, NeoPixel HATs | driven by the Pi's PWM, PCM or SPI timing |
| Servos or motors straight on a GPIO, passive buzzers, dimmable LEDs | need PWM. Use a PCA9685 board |
| DHT11/DHT22, HC-SR04, IR receivers and transmitters, 1-Wire on a GPIO | need microsecond timing; USB adds about 1 ms per operation |
| UPS and power HATs that feed the 5 V pins | they would feed the board's 5 V rail, and how the board handles that is unknown: do not try |
| HATs configured by their ID EEPROM | that is a Pi firmware feature |

## What would make more HATs work

1. **PWM in the firmware** on a few pins, for fans, servos and LED dimming.
   Linux's `dln2` driver has no PWM, so this needs a new way to reach it.
