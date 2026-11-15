# Example 5: your own devices in Home Assistant

Citronics Lime images already make the board a Home Assistant device with
`limeboard-ha`: the phone's system values and sensors, and the onboard LED
and button. This example shows how to add your own hardware: an LED and a
push button on the header, with gpiozero, MQTT discovery and about 120 lines
of Python.

[`ha_gpio.py`](ha_gpio.py) publishes three entities under a device
"Limeboard GPIO example":

| Entity | Hardware | Home Assistant |
|---|---|---|
| LED | LED on GPIO17 (pin 11), as in the [LED example](../gpio-led/README.md) | switch |
| Button | push button on GPIO27 (pin 13) | binary sensor |
| CPU temperature | the phone, via psutil | sensor (Diagnostics) |

## Wiring

- **LED:** GPIO17 (pin 11) → 330 Ω resistor → LED → GND (pin 9).
- **Button:** between GPIO27 (pin 13) and 3.3 V (pin 1 or 17), with a
  10 kΩ resistor from GPIO27 to GND (pin 14). The input then reads 0 when
  the button is released and 1 when it is pressed. Without the resistor the
  input floats and the button state is random.

## Running it

Home Assistant needs the Mosquitto broker add-on, the MQTT integration, and
an MQTT user for the board. `limeboard-ha`'s settings in
`/etc/limeboard-ha.conf` work as well:

```sh
export MQTT_HOST=192.168.1.10 MQTT_USER=board MQTT_PASSWORD=secret
GPIOZERO_PIN_FACTORY=limeboard python3 ha_gpio.py
```

The device appears under Settings > Devices & services > MQTT. Switching
the LED in Home Assistant switches GPIO17, and pressing the button shows up
at once. Stop the script with Ctrl-C: the entities become unavailable.

To delete the device and its entities from Home Assistant:

```sh
python3 ha_gpio.py --remove
```

## How it works

[MQTT discovery](https://www.home-assistant.io/integrations/mqtt/#mqtt-discovery):
the script publishes one retained JSON message per entity on
`homeassistant/<component>/<node>/<object>/config`. That message names the
topics the entity reads and writes. Home Assistant creates the entity and
follows those topics:

| Topic | Direction | Content |
|---|---|---|
| `limeboard/<node>/status` | board → HA | `online`, or `offline` (also the MQTT last will) |
| `limeboard/<node>/led` | board → HA | `ON` or `OFF` |
| `limeboard/<node>/led/set` | HA → board | `ON` or `OFF` |
| `limeboard/<node>/button` | board → HA | `ON` while pressed |
| `limeboard/<node>/cpu_temp` | board → HA | °C, every 30 s |

To add another device, add an entry to `ENTITIES` with its
[Home Assistant MQTT component](https://www.home-assistant.io/integrations/mqtt/)
settings, and publish its state. `limeboard-ha` uses the same approach for
the phone, at a larger scale; its README describes it.

## Notes

- **The node id.** `NODE_ID` (default `limeboard_gpio_example`) must be
  unique on the broker. Give each board its own.
- **The onboard LED and button.** `limeboard-ha` uses them, so this example
  uses header pins. The two programs run side by side.
- **paho-mqtt.** The script works with versions 1 (Debian bookworm) and
  2.
