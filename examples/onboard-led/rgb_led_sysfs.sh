#!/bin/sh
# rgb_led_sysfs.sh <r> <g> <b>: set the onboard RGB LED (each 0 or 1) through
# /sys/class/gpio, for systems without the libgpiod tools.
set -e

for chip in /sys/class/gpio/gpiochip*; do
	[ "$(cat "$chip/label")" = dln2 ] && base=$(cat "$chip/base")
done
[ -n "$base" ] || { echo "no dln2 GPIO chip" >&2; exit 1; }

line=28
for value in "$1" "$2" "$3"; do
	gpio=/sys/class/gpio/gpio$((base + line))
	[ -d "$gpio" ] || echo $((base + line)) > /sys/class/gpio/export
	echo out > "$gpio/direction"
	echo "${value:-0}" > "$gpio/value"
	line=$((line + 1))
done
