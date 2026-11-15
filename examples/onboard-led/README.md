# Example 1: the onboard RGB LED

The Limeboard has an RGB LED driven by the STM32. It appears as three
lines of the `dln2` GPIO chip:

| Line | Colour |
|---|---|
| 28 | red |
| 29 | green |
| 30 | blue |

Each colour is on or off (1 = on), which gives 8 colours: off, red,
green, blue, yellow, cyan, magenta, white. The LED has no brightness
control. The firmware does not expose PWM, so the LED cannot be dimmed.

No wiring is needed. If the Home Assistant agent is running, stop it first:
it uses the LED. See [the main page](../../README.md#the-home-assistant-agent-and-the-onboard-led).

## With gpiozero

[`rgb_led_gpiozero.py`](rgb_led_gpiozero.py) cycles through the colours.
Pressing the user button stops it:

```sh
GPIOZERO_PIN_FACTORY=limeboard python3 rgb_led_gpiozero.py
```

The essential part, the same code as for an RGB LED on a Raspberry Pi:

```python
from time import sleep
from gpiozero import RGBLED

led = RGBLED("LED_R", "LED_G", "LED_B", pwm=False)
led.color = (1, 0, 1)    # magenta: red and blue on
sleep(2)
led.blink()              # white, on and off every second, in the background
sleep(5)
led.off()
```

`pwm=False` is needed: each channel is on or off, so `color` takes 0 or 1
per channel. See [gpiozero](../../README.md#gpiozero) for the pin factory.

## From the shell

```sh
chip=$(gpiodetect | awk '/\[dln2\]/ { print $1 }')

gpioset -c $chip -t 0 28=1 29=0 30=0    # red
gpioset -c $chip -t 0 28=1 29=1 30=0    # yellow
gpioset -c $chip -t 0 28=0 29=0 30=0    # off
```

`-t 0` sets the lines and exits immediately, and the LED keeps its colour.
Without `-t 0`, `gpioset` holds the lines until it is stopped with Ctrl-C.

[`rgb_led.sh`](rgb_led.sh) wraps this with colour names:

```sh
sudo ./rgb_led.sh magenta
sudo ./rgb_led.sh off
```

To blink red at 1 Hz until Ctrl-C:

```sh
gpioset -c $chip -t 500ms,500ms 28=1
```

## From Python with libgpiod

[`rgb_led.py`](rgb_led.py) cycles through the 8 colours with the libgpiod
v2 Python bindings:

```sh
sudo python3 rgb_led.py
```

The essential part:

```python
import gpiod
from gpiod.line import Direction, Value

RED, GREEN, BLUE = 28, 29, 30

with gpiod.request_lines(
    "/dev/gpiochip4",           # use find_chip() from rgb_led.py
    consumer="rgb-led",
    config={(RED, GREEN, BLUE): gpiod.LineSettings(direction=Direction.OUTPUT)},
) as led:
    led.set_values({RED: Value.ACTIVE, GREEN: Value.INACTIVE, BLUE: Value.ACTIVE})  # magenta
```

The lines stay requested while the `with` block runs. Other programs then
cannot use them.

## Without libgpiod (sysfs)

On a system without the libgpiod tools, such as the Buildroot image,
[`rgb_led_sysfs.sh`](rgb_led_sysfs.sh) sets the LED through
`/sys/class/gpio`:

```sh
./rgb_led_sysfs.sh 0 1 1    # cyan
./rgb_led_sysfs.sh 0 0 0    # off
```

The sysfs interface numbers lines globally (chip base + line), and the
script looks up the base of the `dln2` chip. The lines stay exported
afterwards. Unexport them before using libgpiod:
`echo N > /sys/class/gpio/unexport`.

## The user button

Line 31 is the board's user button, an input. With gpiozero:

```python
from gpiozero import Button

button = Button("BUTTON", pull_up=None, active_state=True)
button.wait_for_press()
```

With the libgpiod tools:

```sh
gpioget -c $chip 31                      # current state
gpiomon -c $chip -e both 31              # print an event on each change
```

Holding the button while the board powers up starts the STM32's
bootloader (for firmware updates) instead of the Limeboard I/O firmware.
