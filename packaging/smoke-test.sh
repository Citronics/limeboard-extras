#!/bin/bash
# SPDX-License-Identifier: MIT
# Install dist/*.deb in Debian trixie and Ubuntu resolute armhf containers,
# with their dependencies from the distribution, and import what they ship.
# Needs docker with armhf emulation.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
FW=${FIRMWARE_DEB:-}
for image in debian:trixie ubuntu:resolute; do
	echo "== $image"
	docker run --rm --platform linux/arm/v7 -v "$ROOT/dist:/dist:ro" ${FW:+-v "$FW:/fw.deb:ro"} "$image" bash -euc '
		export DEBIAN_FRONTEND=noninteractive
		apt-get update -qq >/dev/null
		debs=$(ls /dist/*.deb)
		[ -f /fw.deb ] && debs="$debs /fw.deb"
		apt-get install -y -qq --no-install-recommends $debs >/dev/null
		python3 -c "
import os, limeboard_compat
# what the compat hook sets on a Limeboard; a container has none
os.environ.setdefault(\"RPI_LGPIO_REVISION\", limeboard_compat.PI_REVISION)
os.environ.setdefault(\"RPI_LGPIO_CHIP\", \"0\")
import gpiozero, lgpio, RPi.GPIO, limeboard_gpiozero
from importlib.metadata import entry_points
assert any(e.name == \"limeboard\" for e in entry_points(group=\"gpiozero_pin_factories\"))
print(\"gpiozero\", gpiozero.__version__ if hasattr(gpiozero, \"__version__\") else \"ok\", \"lgpio\", lgpio.LGPIO_PY_VERSION)
"
		limeboard-config show
		test -f /etc/limeboard-ha.conf && test "$(stat -c %a /etc/limeboard-ha.conf)" = 600
		systemctl is-enabled limeboard-ha.service
		getent group gpio spi i2c >/dev/null
		echo ok
	'
done
