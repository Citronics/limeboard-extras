# Example 3: an LED on a header GPIO

This example blinks an external LED connected to GPIO17 (header pin 11),
the GPIO used by most Raspberry Pi tutorials.

## Wiring

You need an LED, a resistor of 330 Ω to 1 kΩ, and two jumper wires.

```
header pin 11 (GPIO17) ──── resistor ────►|──── header pin 9 (GND)
                                     LED anode (long leg)   cathode (short leg)
```

- GPIO17 is header pin 11. GND is pin 9, its neighbour in the same
  (odd-numbered) column.
- The resistor limits the current. Without it, the LED or the
  microcontroller pin can be damaged. With 330 Ω and a red LED the current
  is about 4 mA.
- The pins are 3.3 V. Never connect a GPIO to 5 V.

Any of GPIO0 to GPIO27 works the same way. Pass its BCM number to the
scripts below, and see [PINOUT.md](../../PINOUT.md) for its
pin.

## With gpiozero

This is the first example of most Raspberry Pi tutorials, unchanged.
[`blink_gpiozero.py`](blink_gpiozero.py):

```python
from signal import pause
from gpiozero import LED

led = LED(17)
led.blink(on_time=0.5, off_time=0.5)
pause()
```

```sh
GPIOZERO_PIN_FACTORY=limeboard python3 blink_gpiozero.py        # GPIO17
GPIOZERO_PIN_FACTORY=limeboard python3 blink_gpiozero.py 27     # GPIO27
```

See [gpiozero](../../README.md#gpiozero) for the pin factory. Use `LED`,
not `PWMLED`: the Limeboard has no PWM, and software PWM over USB flickers.

## With RPi.GPIO

[`blink_rpi_gpio.py`](blink_rpi_gpio.py), the RPi.GPIO version found in
older tutorials, runs as is:

```sh
python3 blink_rpi_gpio.py
```

## With Adafruit Blinka

[`blink_blinka.py`](blink_blinka.py), the CircuitPython way, after
`pip install adafruit-blinka` (see
[limeboard-compat](../../limeboard-compat/README.md#adafruit-blinka)):

```python
import board, digitalio

led = digitalio.DigitalInOut(board.D17)
led.direction = digitalio.Direction.OUTPUT
led.value = True
```

## From the shell

```sh
chip=$(gpiodetect | awk '/\[citronics-dln2\]/ { print $1 }')

gpioset -c $chip -t 0 17=1     # LED on
gpioset -c $chip -t 0 17=0     # LED off
gpioinfo -c $chip 17           # shows the line's direction and user
```

[`blink.sh`](blink.sh) blinks the LED at 1 Hz until Ctrl-C:

```sh
sudo ./blink.sh        # GPIO17
sudo ./blink.sh 27     # GPIO27, header pin 13
```

It runs `gpioset -t 500ms,500ms 17=1`, which repeats 500 ms on and 500 ms
off.

## From Python with libgpiod

[`blink.py`](blink.py) does the same with the libgpiod v2 Python bindings:

```sh
sudo python3 blink.py        # GPIO17
sudo python3 blink.py 27     # GPIO27
```

The essential part:

```python
import time
import gpiod
from gpiod.line import Direction, Value

with gpiod.request_lines(
    "/dev/gpiochip4",           # use find_chip() from blink.py
    consumer="blink",
    config={17: gpiod.LineSettings(direction=Direction.OUTPUT)},
) as led:
    while True:
        led.set_value(17, Value.ACTIVE)
        time.sleep(0.5)
        led.set_value(17, Value.INACTIVE)
        time.sleep(0.5)
```

## Reading a push button

Inputs work the same way. Wire a push button between GPIO27 (pin 13) and
3.3 V (pin 1 or 17), and a 10 kΩ resistor from GPIO27 to GND (pin 14) so
that the input reads 0 when the button is released:

```sh
gpioget -c $chip 27                 # 1 while pressed
gpiomon -c $chip -e both 27         # an event on each press and release
```

With gpiozero, `Button(27, pull_up=None, active_state=True)` (the resistor
on the board does the pulling) and `button.when_pressed = ...`.

With the libgpiod Python module, request the line with
`gpiod.LineSettings(direction=Direction.INPUT)` and read it with
`request.get_value(27)`.

## Notes

- A GPIO is on or off. The firmware has no PWM, so an LED on a GPIO
  cannot be dimmed. Every change also goes over USB and takes about a
  millisecond, so do not expect precise timing below a few milliseconds.
- If a request fails with `Device or resource busy`, another program owns
  the line. `gpioinfo -c $chip 17` shows which one.
