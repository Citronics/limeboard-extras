# limeboard-gpiozero

A [gpiozero](https://gpiozero.readthedocs.io/) pin factory for the Citronics
Limeboard. With it, Raspberry Pi gpiozero code drives the Limeboard's header
and its onboard RGB LED and button:

```sh
GPIOZERO_PIN_FACTORY=limeboard python3 my_script.py
GPIOZERO_PIN_FACTORY=limeboard pinout
```

The board's STM32 must run the Limeboard I/O firmware, which makes the
header a Linux GPIO chip labelled `citronics-dln2`. The factory is gpiozero's lgpio
factory (the default on a Raspberry Pi 5) opened on that chip, with the
Limeboard header's description:

- pins have the Raspberry Pi names: `17`, `"GPIO17"`, `"BCM17"`, `"BOARD11"`;
- the onboard RGB LED's channels are `"LED_R"`, `"LED_G"` and `"LED_B"`, and
  the user button is `"BUTTON"`.

## Installing

Citronics Lime images (Debian, Ubuntu, Buildroot) already include it, with
gpiozero 2.0.1 and lgpio.

Elsewhere, it needs gpiozero 2.0.1 or later, and lgpio:

- **Ubuntu:** `sudo apt install python3-lgpio`.
- **Debian:** Debian does not package lgpio, so build it from PyPI's source
  with its C library linked in:
  `sudo apt install swig python3-dev gcc`, then
  `PYPI=1 CFLAGS=-std=gnu17 pip install --no-binary lgpio lgpio`.

Then install this package, which also installs gpiozero:

```sh
pip install ./limeboard-gpiozero
```

The `pip install` registers the factory under the name `limeboard`, for
`GPIOZERO_PIN_FACTORY`. Without installing, copy `limeboard_gpiozero.py` next
to your script and select the factory in Python:

```python
from gpiozero import Device, LED
from limeboard_gpiozero import LimeboardFactory

Device.pin_factory = LimeboardFactory()
led = LED(17)
```

## Notes

- Use `LED` and `RGBLED(..., pwm=False)`, not `PWMLED`: the firmware has no
  PWM, and gpiozero's software PWM over USB flickers.
- Use `Button(..., pull_up=None, active_state=...)` with an external pull
  resistor: the firmware has no pull-up or pull-down resistors.
- lgpio's event thread wakes every 0.5 ms while a pin watches for edges
  (any `Button`), which costs about 16% of a CPU core on the phone. The Lime
  images patch it to 10 ms; see the `limeboard-ha` README.
- When the STM32 resets (firmware update, USB reset), the chip disappears.
  Close the devices and the factory, and open a new `LimeboardFactory()` once
  the firmware is back: it finds the chip by its label.

## How it differs from gpiozero's lgpio factory

- It finds the chip by its label, because its number can change.
- It opens the chip itself: gpiozero 2.0.1's `LGPIOFactory` ignores its
  `chip` argument and opens gpiochip0, which on the phone is the SoC's own
  pins. It refuses any chip not labelled `citronics-dln2`.
- It keeps its own pin cache. gpiozero's local factories share one cache,
  which would hand a new factory the dead pins of a chip that disappeared.
