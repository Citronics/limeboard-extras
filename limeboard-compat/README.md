# limeboard-compat

Raspberry Pi GPIO code on the Citronics Limeboard, unchanged: gpiozero,
RPi.GPIO and Adafruit Blinka (Adafruit's CircuitPython libraries on Linux).

```python
import RPi.GPIO as GPIO              # works
from gpiozero import LED             # works
import board, busio, digitalio       # works (Blinka)
```

Nothing to configure: when the board's STM32 runs the Limeboard I/O
firmware, every Python program starts already set up for it. On Citronics
Lime images (Debian, Ubuntu, Buildroot) this package is installed.

## What it does

`limeboard_compat.pth` runs `limeboard_compat.setup()` when Python starts. If
the Limeboard I/O firmware's GPIO chip is present, it sets:

| Setting | Value | Effect |
|---|---|---|
| `GPIOZERO_PIN_FACTORY` | `limeboard` | gpiozero uses the [Limeboard pin factory](../limeboard-gpiozero/README.md) |
| `RPI_LGPIO_CHIP` | the chip's number, e.g. `4` | RPi.GPIO (rpi-lgpio) opens the Limeboard's chip |
| `RPI_LGPIO_REVISION` | `a03111` | RPi.GPIO starts, and reports a Raspberry Pi 4 Model B (same 40-pin header) |
| `BLINKA_FORCEBOARD` | `GENERIC_LINUX_PC` | Blinka uses its generic Linux I2C code |

It also installs an import hook. When Blinka is installed, `import board`,
`import microcontroller` and `microcontroller.pin` load the Limeboard's
definitions (`limeboard_blinka`) instead of Blinka's own. Those use
Blinka's lgpio pin code on the Limeboard's chip.

- Settings already in the environment are kept.
- `LIMEBOARD_COMPAT=0` turns everything off.
- Without the Limeboard I/O firmware it does nothing.
- It adds about 10 ms to Python's startup on the phone.

These settings are not just convenient, they are needed for safety: without
them, rpi-lgpio and Blinka's lgpio pins fall back to `gpiochip0`, which on
the phone is the SoC's own pins.

## Using it

Pins have their Raspberry Pi numbers (BCM): GPIO17 is header pin 11. The
onboard RGB LED and the user button have their own names.

### RPi.GPIO

```python
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)        # or GPIO.BOARD: GPIO.setup(11, ...) is GPIO17
GPIO.setup(17, GPIO.OUT)
GPIO.output(17, GPIO.HIGH)
GPIO.setup(27, GPIO.IN)       # wire an external pull resistor
GPIO.add_event_detect(27, GPIO.RISING, callback=lambda ch: print("pressed"))
GPIO.cleanup()
```

The onboard LED and button are lines 28-31 in `GPIO.BCM` mode (red, green,
blue, button).

### gpiozero

```python
from gpiozero import LED, RGBLED, Button

LED(17).blink()
RGBLED("LED_R", "LED_G", "LED_B", pwm=False).color = (0, 1, 1)
```

### Adafruit Blinka

Install Blinka once. On Debian and Ubuntu, Python packages from PyPI go into
a virtual environment that also sees the system's packages:

```sh
python3 -m venv --system-site-packages ~/blinka
~/blinka/bin/pip install adafruit-blinka adafruit-circuitpython-ssd1306   # and your device's library
```

Then the usual Blinka code runs:

```python
import board, digitalio

led = digitalio.DigitalInOut(board.D17)
led.switch_to_output(True)

i2c = board.I2C()                 # the header's I2C bus, pins 3 and 5
print([hex(a) for a in i2c.scan()])
```

`board` has the Raspberry Pi names (`D0`-`D27`, `SDA`, `SCL`, `MOSI`, `MISO`,
`SCLK`, `CE0`, `CE1`, `TX`, `RX`; for the second buses `SDA0`, `SCL0`,
`SCLK_1`, `MOSI_1`, `MISO_1`, `CE0_1`-`CE2_1`) plus `LED_R`, `LED_G`, `LED_B`
and `BUTTON`. `board.board_id` is `"LIMEBOARD"`. The second I2C bus is
`busio.I2C(board.SCL0, board.SDA0)`.

## Limits

These come from the Limeboard, not from the libraries:

- **No PWM.** `GPIO.PWM`, gpiozero's `PWMLED` and Blinka's `pwmio` would
  generate it in software over USB, which flickers. For PWM, use a PCA9685
  board on I2C.
- **No pull-up or pull-down resistors.** Library settings for them have no
  effect: wire the resistors.
- **GPIO is about 1 ms per operation.** Bit-banged protocols (DHT22,
  NeoPixel, 1-Wire on a GPIO) do not work.
- **I2C messages are limited to 256 bytes.** Most drivers send less. Drivers
  that send a whole frame buffer at once must split it. Adafruit's SSD1306
  driver does with `page_addressing=True`:
  `adafruit_ssd1306.SSD1306_I2C(128, 64, board.I2C(), page_addressing=True)`.
- **SPI** is `board.SPI()` (SPI0); the second bus is
  `busio.SPI(board.SCLK_1, board.MOSI_1, board.MISO_1)`. A library's chip
  select must be another GPIO than the bus's CE pins, which belong to it. SPI is
  slower than on a Pi: a USB round trip per 256 bytes.
- **The UART** is the USB serial port `/dev/ttyACM*`: open it with
  `serial.Serial("/dev/ttyACM0", 9600)`, not `busio.UART`.
- **Blinka's `analogio`** is not mapped. Read the board's ADC from
  `/sys/bus/iio/devices/` (device `dln2-adc`).
- **Blinka keeps a pin** until the program exits, even after `deinit()`. A
  later program, or gpiozero or RPi.GPIO in the same program, gets "GPIO busy"
  on that pin until then.
- **Only one program can use a pin at a time.** On images with the Home
  Assistant agent, the onboard LED and button belong to `limeboard-ha`.

## Installing elsewhere

It needs lgpio (see [limeboard-gpiozero](../limeboard-gpiozero/README.md#installing)),
and rpi-lgpio for RPi.GPIO:

```sh
pip install ./limeboard-compat[rpi-gpio]          # RPi.GPIO
pip install ./limeboard-compat[blinka]            # Adafruit Blinka
pip install ./limeboard-gpiozero                  # gpiozero
```

The `.pth` file is installed into the environment's `site-packages`, so the
setup applies to that environment's Python. A virtual environment created
with `--system-site-packages` also gets the system's copy.
