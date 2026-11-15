#!/usr/bin/env python3
"""ha_gpio.py: an LED and a push button on the Limeboard header, in Home
Assistant, with gpiozero and MQTT discovery.

- The LED on GPIO17 (header pin 11) becomes a switch.
- The button on GPIO27 (header pin 13) becomes a binary sensor.
- The phone's CPU temperature (psutil) becomes a sensor.

Settings come from the environment: MQTT_HOST (required), MQTT_PORT,
MQTT_USER, MQTT_PASSWORD, NODE_ID (default limeboard_gpio_example).

    MQTT_HOST=192.168.1.10 MQTT_USER=board MQTT_PASSWORD=... \\
        GPIOZERO_PIN_FACTORY=limeboard python3 ha_gpio.py

--remove deletes the entities from Home Assistant and exits.
"""
import json
import os
import sys
import time

import paho.mqtt.client as mqtt
import psutil
from gpiozero import LED, Button

NODE = os.environ.get("NODE_ID", "limeboard_gpio_example")
BASE = f"limeboard/{NODE}"
DEVICE = {"identifiers": [NODE], "name": "Limeboard GPIO example", "manufacturer": "Citronics"}

# Home Assistant entities: component, object id, configuration
ENTITIES = [
    ("switch", "led", {"name": "LED", "command_topic": f"{BASE}/led/set",
                       "state_topic": f"{BASE}/led", "icon": "mdi:led-on"}),
    ("binary_sensor", "button", {"name": "Button", "state_topic": f"{BASE}/button"}),
    ("sensor", "cpu_temp", {"name": "CPU temperature", "state_topic": f"{BASE}/cpu_temp",
                            "device_class": "temperature", "unit_of_measurement": "°C",
                            "state_class": "measurement", "entity_category": "diagnostic"}),
]


def discovery_topic(component, obj):
    return f"homeassistant/{component}/{NODE}/{obj}/config"


def make_client():
    if hasattr(mqtt, "CallbackAPIVersion"):  # paho-mqtt 2
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    else:  # paho-mqtt 1
        client = mqtt.Client()
    if os.environ.get("MQTT_USER"):
        client.username_pw_set(os.environ["MQTT_USER"], os.environ.get("MQTT_PASSWORD", ""))
    return client


def cpu_temp():
    temps = psutil.sensors_temperatures()
    cpu = [t.current for name, ts in temps.items() if name.startswith("cpu") for t in ts]
    return max(cpu) if cpu else None


def remove(client):
    """Delete the entities and the retained states: an empty retained
    message deletes the previous one, and an empty config the entity."""
    topics = [discovery_topic(component, obj) for component, obj, _ in ENTITIES]
    topics += [f"{BASE}/{t}" for t in ("status", "led", "button", "cpu_temp")]
    for topic in topics:
        client.publish(topic, "", qos=1, retain=True).wait_for_publish()


def main():
    client = make_client()
    host, port = os.environ["MQTT_HOST"], int(os.environ.get("MQTT_PORT", 1883))
    if "--remove" in sys.argv:
        client.connect(host, port)
        client.loop_start()
        remove(client)
        client.loop_stop()
        return

    led = LED(17)
    button = Button(27, pull_up=None, active_state=True)  # external 10 kΩ pull-down

    def publish(topic, value):
        client.publish(f"{BASE}/{topic}", value, qos=1, retain=True)

    def on_connect(client, *_):
        for component, obj, config in ENTITIES:
            config = dict(config, unique_id=f"{NODE}_{obj}", device=DEVICE,
                          availability_topic=f"{BASE}/status")
            client.publish(discovery_topic(component, obj), json.dumps(config), qos=1, retain=True)
        client.subscribe(f"{BASE}/led/set")
        publish("status", "online")
        publish("led", "ON" if led.is_lit else "OFF")
        publish("button", "ON" if button.is_pressed else "OFF")

    def on_message(client, userdata, msg):
        led.value = msg.payload == b"ON"
        publish("led", "ON" if led.is_lit else "OFF")

    client.on_connect, client.on_message = on_connect, on_message
    client.will_set(f"{BASE}/status", "offline", retain=True)
    client.connect(host, port)
    client.loop_start()  # reconnects by itself, and on_connect publishes again
    button.when_pressed = lambda: publish("button", "ON")
    button.when_released = lambda: publish("button", "OFF")

    try:
        while True:
            publish("cpu_temp", cpu_temp())
            time.sleep(30)
    except KeyboardInterrupt:
        publish("status", "offline")
        time.sleep(0.5)
        led.off()


if __name__ == "__main__":
    main()
