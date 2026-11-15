# Raspberry Pi HATs on the Limeboard

The Limeboard's header has the Raspberry Pi layout, so most HATs fit
mechanically. Whether a HAT *works* depends on what it needs from the Pi:
some need only the signals the Limeboard I/O firmware provides, others need
parts of the Pi that the board does not have.

In short:

| | |
|---|---|
| **Out of the box** | HATs that use GPIO, I2C, SPI or the serial port through their usual Python library (gpiozero, RPi.GPIO, Blinka, smbus2, spidev, pyserial): relays, buttons, LEDs, sensors, ADCs, PCA9685 PWM and servo boards, e-paper displays, GPS data |
| **One extra step** | I2C OLED displays (one driver setting), kernel drivers for simple I2C chips such as real-time clocks (one command) |
| **No** | audio (I2S), displays driven by kernel drivers or DPI, HATs that need the Pi's PWM or microsecond timing, HATs whose kernel driver needs a device tree overlay |

"Out of the box" means the same steps as on a Pi: turn the HAT's bus on
(`sudo limeboard-config enable i2c1`, like `raspi-config`), install the
HAT's library, run it. Pi software finds the same devices:

| Pi software uses | On the Limeboard (Fairphone 2) |
|---|---|
| `/dev/i2c-1`, `SMBus(1)` | i2c1, pins 3/5 |
| `/dev/spidev0.0`, `spidev.open(0, 0)` | spi0, CE0 |
| `/dev/serial0` | the header UART (a link to `/dev/ttyACM*`) |
| GPIO numbers (BCM) | the same GPIOs |

Only the I2C pins (header pins 3 and 5) have been checked with real hardware.
The other pins follow the Raspberry Pi layout as defined by the firmware.
Check the power pins with a multimeter before plugging in a HAT: the current
the board's 3.3 V and 5 V pins can supply is not documented.

## Why: what is different from a Pi

On a Raspberry Pi, the header pins belong to the main processor. On the
Limeboard, they belong to an STM32 microcontroller, which reaches the phone
over USB. The `citronics-dln2` driver of Citronics kernels makes it look like
a Pi header, with these differences:

| | Raspberry Pi | Limeboard |
|---|---|---|
| GPIO | direct, microsecond timing | over USB: about 1 ms per operation. Edge events work |
| Pull-up / pull-down resistors | internal, per pin | none: use external resistors |
| PWM | 2 hardware channels | none |
| I2C | i2c1 on pins 3/5 (and i2c0 on pins 27/28), up to 400 kHz and more | i2c1 and i2c0 on the same pins, 100 kHz, 256 bytes per message; see [Bus names](README.md#bus-names) |
| SPI | spi0, spi1 (`/dev/spidev0.x`, `1.x`) | the same two buses, slower: a USB round trip per 256 bytes ([below](#spi)) |
| UART | `/dev/serial0`, and more UARTs on the Pi 4 and 5 | one: `/dev/serial0`, a link to the USB serial port `/dev/ttyACM*` ([why only one](README.md#one-uart)) |
| I2S / PCM audio | yes | no |
| DPI display, GPCLK | yes | no |
| `config.txt`: `dtparam=i2c_arm=on`, `dtparam=spi=on`, `dtoverlay=spi1-3cs`, `dtoverlay=i2c0` | yes, buses off by default | the same lines in `/etc/limeboard/config.txt`, buses off by default ([Turning the buses on](README.md#turning-the-buses-on)) |
| Device tree overlays for chips (`dtoverlay=mcp2515`…) | yes | no: the buses come over USB. SPI chips: `spi0_cs0=mcp2515,irq=25` in `config.txt`; I2C chips: `new_device` |
| HAT ID EEPROM (GPIO0/1) | read at boot, configures the HAT | not read: GPIO0/1 are i2c0, a plain I2C bus |

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

  (`i2c-1` is the Limeboard's bus here; `i2cdetect -l | grep citronics-dln2` shows its
  number.)

### SPI

The SPI buses work like a Pi's spi0 and spi1: `/dev/spidev0.0` and `0.1`,
`/dev/spidev1.0`, `1.1` and `1.2`, for py-spidev, gpiozero and Blinka.

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

Installers that run `raspi-config nonint do_i2c 0` or `do_spi 0` work too:
the Limeboard's `raspi-config` turns the bus on through `limeboard-config`
([raspi-config](README.md#serial-console-firmware-and-raspi-config)).

The HAT's library therefore usually runs as is, within the limits of this
page. For example, there is no PWM, and I2C messages are at most 256 bytes.
Adafruit's SSD1306 OLED driver, for one, needs `page_addressing=True`.

**pigpio** and **wiringPi** access the Pi's processor directly and do not
work.

## HAT by HAT

✔ marks what has been run on a Limeboard. The rest follows from the
interfaces and libraries the HAT uses. A library that looks for the
Raspberry Pi's own GPIO chip by name, instead of going through RPi.GPIO,
gpiozero or Blinka, needs to be pointed at the Limeboard's `citronics-dln2` chip.

### Out of the box

Turn on the bus the HAT uses, install its library, run it.

| HAT | Bus | Notes |
|---|---|---|
| Relay HATs, LED and button HATs, Traffic HAT | GPIO | gpiozero, RPi.GPIO or Blinka libraries ✔ (LED, button) |
| Active buzzers (on/off) | GPIO | passive buzzers need PWM, see below |
| I2C sensors: BME280, BME680, BMP280, SHT31, LTR559, IMUs | i2c1 | `smbus2` or Blinka libraries ✔ (Blinka I2C) |
| I2C ADCs: ADS1115, ADS1015 | i2c1 | the board also has its own 8-channel ADC |
| PWM and servo HATs: PCA9685 (Adafruit Servo HAT, PWM HAT, Motor HAT) | i2c1 | **the way to get PWM** on the Limeboard: the chip generates it |
| SPI ADCs: MCP3008, MCP3208 | spi0 | gpiozero's `MCP3008` class, or py-spidev ✔ (the bus, with a loopback) |
| Waveshare e-paper displays | spi0 + GPIO | their RPi.GPIO/gpiozero and spidev drivers; refreshes are slow anyway |
| LoRa HATs (SX127x, SX126x) | spi0 + GPIO | when their library drives SPI and GPIO from user space |
| GPS HATs: position data | UART | `gpsd /dev/serial0` |
| RS-485 / serial HATs, the RS485 side of the RS485 CAN HAT | UART | `/dev/serial0`. Automatic direction switching works as is; direction control on a GPIO is slow (about 1 ms) |

### One extra step

| HAT | Step |
|---|---|
| I2C OLED displays: SSD1306, SH1106 ✔ | their driver writes a whole frame in one message; make it send smaller ones: `page_addressing=True` for Adafruit's driver, an `SMBus` for luma ([OLED example](examples/i2c-oled/README.md)) |
| Real-time clocks: DS3231, DS1307, PCF8523 | instead of `dtoverlay=i2c-rtc`: `echo ds3231 0x68 \| sudo tee /sys/bus/i2c/devices/i2c-1/new_device` |
| I2C GPIO expanders: MCP23017, PCF8574 | from Python as is, or the kernel driver with `new_device` (without interrupts) |
| 1-Wire through an I2C bridge (DS2482) | `new_device` with the kernel driver `ds2482` |
| SPI chips with a kernel driver (MCP3008 as IIO, …) | a `spi0_cs0=mcp3008` line in `config.txt` instead of `dtoverlay=`; the Lime kernels do not build these drivers yet |
| CAN HATs: MCP2515 (PiCAN2, Waveshare RS485 CAN HAT ✔), MCP2518FD (Waveshare 2-CH CAN FD HAT) | their usual `dtoverlay=mcp2515-can0,…` or `dtoverlay=mcp251xfd,…` line in `config.txt`, a kernel with CAN and firmware 1.3; about 250-330 frames per second ([CAN example](examples/can/README.md)) |
| Software that opens `/dev/ttyAMA0` | give it `/dev/serial0` |

### Partly

| HAT | What works | What does not |
|---|---|---|
| Pimoroni Enviro+ | its I2C sensors and gas ADC, its SPI LCD (slowly), the particle sensor on `/dev/serial0` | the microphone, which uses I2S |
| Raspberry Pi Sense HAT | its I2C sensors, read directly | the LED matrix and joystick, which use kernel drivers |
| GPS HATs with PPS | position data | the PPS precise-time pulse (kernel driver and microsecond timing) |
| Fan HATs | on and off | speed control (PWM) |
| Automation HATs | relays, inputs, ADC | PWM outputs |

### No

| HAT | Why |
|---|---|
| Audio: HiFiBerry, IQaudio, pHAT DAC, ReSpeaker microphones | need I2S, which the header does not carry. Use a USB sound card instead |
| SPI displays with kernel drivers: PiTFT, Waveshare 3.5" LCD | need a kernel driver loaded by a device tree overlay |
| DPI displays | the Pi's parallel display signals are not on the header |
| Addressable LEDs from the Pi: Unicorn HAT, NeoPixel HATs | driven by the Pi's PWM, PCM or SPI timing |
| Servos or motors straight on a GPIO, passive buzzers, dimmable LEDs | need PWM. Use a PCA9685 board |
| DHT11/DHT22, HC-SR04, IR receivers and transmitters, 1-Wire on a GPIO | need microsecond timing; USB adds about 1 ms per operation |
| UPS and power HATs that feed the 5 V pins | they would feed the board's 5 V rail, and how the board handles that is unknown: do not try |
| HATs configured by their ID EEPROM | that is a Pi firmware feature |

## What would make more HATs work

1. **PWM in the firmware** on a few pins, for fans, servos and LED dimming.
   The `citronics-dln2` driver has no PWM either: both need it.
