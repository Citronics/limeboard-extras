#!/bin/sh
# blink.sh [gpio]: blink an LED wired to a header GPIO (default GPIO17, pin 11)
# until Ctrl-C. Needs the libgpiod v2 tools (Debian package: gpiod).
gpio=${1:-17}

chip=$(gpiodetect | awk '/\[citronics-dln2\]/ { print $1 }')
[ -n "$chip" ] || { echo "no citronics-dln2 GPIO chip" >&2; exit 1; }

# -t 500ms,500ms: on for 500 ms, off for 500 ms, repeated.
exec gpioset -c "$chip" -t 500ms,500ms "$gpio"=1
