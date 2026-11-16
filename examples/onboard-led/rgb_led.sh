#!/bin/sh
# SPDX-License-Identifier: MIT
# rgb_led.sh <colour>: set the Limeboard's onboard RGB LED.
# Colours: red green blue yellow cyan magenta white off.
# Needs the libgpiod v2 tools (Debian package: gpiod).
set -e

case "$1" in
	red)     rgb="1 0 0" ;;
	green)   rgb="0 1 0" ;;
	blue)    rgb="0 0 1" ;;
	yellow)  rgb="1 1 0" ;;
	cyan)    rgb="0 1 1" ;;
	magenta) rgb="1 0 1" ;;
	white)   rgb="1 1 1" ;;
	off)     rgb="0 0 0" ;;
	*) echo "usage: $0 red|green|blue|yellow|cyan|magenta|white|off" >&2; exit 1 ;;
esac
# shellcheck disable=SC2086 # split "1 0 0" into $1 $2 $3
set -- $rgb

chip=$(gpiodetect | awk '/\[citronics-dln2\]/ { print $1 }')
[ -n "$chip" ] || { echo "no citronics-dln2 GPIO chip" >&2; exit 1; }

# -t 0: set the lines and exit. The firmware keeps the output level after
# the lines are released.
gpioset -c "$chip" -t 0 28="$1" 29="$2" 30="$3"
