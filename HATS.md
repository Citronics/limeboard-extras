# Raspberry Pi HATs on the Limeboard

The Limeboard's header has the Raspberry Pi layout, so most HATs fit
mechanically. Whether a HAT *works* depends on what it needs from the Pi:
some need only the signals the Limeboard I/O firmware provides, others need
parts of the Pi that the board does not have.

In short:

| | |
|---|---|
| **Works** | HATs that use only GPIO, I2C or the serial port, with software that drives the chips itself: relays, buttons, LEDs, I2C sensors, I2C ADCs, PCA9685 PWM and servo boards, I2C OLED displays, real-time clocks, GPS data |
| **Not yet** | SPI HATs: the Limeboard has no `/dev/spidev` yet |
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
| I2C | up to 400 kHz and more | one bus, 100 kHz, 256 bytes per message |
| SPI | `/dev/spidev0.0`, `/dev/spidev0.1` | the controller exists, but no `/dev/spidev` yet ([below](#spi)) |
| UART | `/dev/serial0` | `/dev/ttyACM*`, a USB serial port |
| I2S / PCM audio | yes | no |
| DPI display, GPCLK, second SPI bus | yes | no |
| Device tree overlays (`dtoverlay=`) | yes | no: the buses come over USB |
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

The `dln2` driver creates the SPI controller (`/sys/class/spi_master/spi0`),
but no device on it. On a Pi, the device tree creates the `spidev` devices
that programs open (`/dev/spidev0.0` and `/dev/spidev0.1`). On the Limeboard
nothing does yet, and Linux has no command to add one by hand. Until a small
kernel change provides them, programs cannot use SPI.

When they exist, SPI will be slow by Pi standards: every transfer of up to
256 bytes is a USB round trip. A 320×240 colour frame takes about 600
transfers, so roughly half a second.

### Software that expects a Pi

Many HAT libraries check that they run on a Raspberry Pi, or import
`RPi.GPIO`, which only works on a Pi. On the Limeboard:

- **gpiozero** works with the [`limeboard` pin factory](README.md#gpiozero).
  Libraries built on gpiozero work.
- **RPi.GPIO**: Ubuntu's `python3-rpi-lgpio` provides the same module on top
  of lgpio. Its `RPI_LGPIO_CHIP` setting should point it at the Limeboard's
  GPIO chip. This is not tested.
- **Adafruit Blinka** (Adafruit's CircuitPython libraries on Linux) detects
  the board and does not know the Limeboard. Use a library built on `smbus2`
  for the same chip, or talk to it directly.
- **pigpio** and **wiringPi** access the Pi's processor directly and do not
  work.

## HAT by HAT

### Works

| HAT | Uses | Notes |
|---|---|---|
| Relay HATs, LED and button HATs, Traffic HAT | GPIO | gpiozero. RPi.GPIO libraries need the shim above |
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

### Not yet (SPI)

These need `/dev/spidev`. Once it exists, the ones driven from user space
will work, slowly:

| HAT | Notes |
|---|---|
| E-paper displays (Waveshare, Inky) | refreshes are slow anyway: usable |
| SPI ADCs: MCP3008, MCP3208 | usable |
| LoRa HATs (SX127x, SX126x) | usable, if their library drives SPI and GPIO from user space |
| SPI LCDs driven from Python | about half a second per full frame |

### No

| HAT | Why |
|---|---|
| Audio: HiFiBerry, IQaudio, pHAT DAC, ReSpeaker microphones | need I2S, which the header does not carry. Use a USB sound card instead |
| SPI displays with kernel drivers: PiTFT, Waveshare 3.5" LCD | need a kernel driver loaded by a device tree overlay |
| DPI displays | the Pi's parallel display signals are not on the header |
| CAN HATs (MCP2515) | the kernel CAN driver needs a device tree overlay and an interrupt |
| Addressable LEDs from the Pi: Unicorn HAT, NeoPixel HATs | driven by the Pi's PWM, PCM or SPI timing |
| Servos or motors straight on a GPIO, passive buzzers, dimmable LEDs | need PWM. Use a PCA9685 board |
| DHT11/DHT22, HC-SR04, IR receivers and transmitters, 1-Wire on a GPIO | need microsecond timing; USB adds about 1 ms per operation |
| UPS and power HATs that feed the 5 V pins | they would feed the board's 5 V rail, and how the board handles that is unknown: do not try |
| HATs configured by their ID EEPROM | that is a Pi firmware feature |

## What would make more HATs work

1. **`spidev` devices** on the SPI bus: a small kernel change would unlock
   the user-space SPI HATs above.
2. **PWM in the firmware** on a few pins, for fans, servos and LED dimming.
   Linux's `dln2` driver has no PWM, so this needs a new way to reach it.
3. **RPi.GPIO on lgpio** (`rpi-lgpio`), set up for the Limeboard's chip, so
   libraries written for RPi.GPIO run unchanged.
