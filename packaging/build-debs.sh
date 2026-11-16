#!/bin/bash
# SPDX-License-Identifier: MIT
# Build the limeboard-io and limeboard-ha Debian packages into dist/.
# Version: the exact git tag (v1.2.3 -> 1.2.3, v1.2.3-rc1 -> 1.2.3~rc1), or
# VERSION from the environment.
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"
if [ -z "${VERSION:-}" ]; then
	TAG=$(git describe --tags --exact-match 2>/dev/null) || {
		echo "ERROR: no tag on this commit; tag it (git tag v1.0) or set VERSION" >&2
		exit 1
	}
	VERSION=$(echo "${TAG#v}" | sed 's/-rc/~rc/')
fi
DIST="$ROOT/dist"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
mkdir -p "$DIST"

copyright() {
	cat > "$1" <<COPYRIGHT
Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: limeboard-extras
Source: https://github.com/Citronics/limeboard-extras

Files: *
Copyright: 2026 Citronics
License: MIT

License: MIT
$(sed 's/^$/./; s/^/ /' "$ROOT/LICENSE" | tail -n +2)
COPYRIGHT
}

# The packages ship no conffiles: /etc/limeboard/config.txt and
# /etc/limeboard-ha.conf are the user's (limeboard-config edits the first),
# installed from /usr/share by postinst when missing and never replaced, so
# upgrades never stop to ask about them.

# limeboard-io -------------------------------------------------------------
P="$WORK/limeboard-io"
PY="$P/usr/lib/python3/dist-packages"
install -D -m 0755 limeboard-config/limeboard-config "$P/usr/bin/limeboard-config"
install -D -m 0755 limeboard-config/raspi-config "$P/usr/bin/raspi-config"
install -D -m 0755 limeboard-config/limeboard-serial-console "$P/usr/libexec/limeboard-serial-console"
install -D -m 0644 limeboard-config/limeboard-serial-console.service \
	"$P/usr/lib/systemd/system/limeboard-serial-console.service"
install -D -m 0644 limeboard-config/limeboard-firmware-update.service \
	"$P/usr/lib/systemd/system/limeboard-firmware-update.service"
install -D -m 0644 limeboard-config/config.txt "$P/usr/share/limeboard/config.txt"
install -D -m 0644 udev/90-limeboard-io.rules "$P/usr/lib/udev/rules.d/90-limeboard-io.rules"
install -D -m 0644 udev/91-limeboard-groups.rules "$P/usr/lib/udev/rules.d/91-limeboard-groups.rules"
install -D -m 0644 limeboard-compat/limeboard_compat.py "$PY/limeboard_compat.py"
install -D -m 0644 limeboard-compat/limeboard_compat.pth "$PY/limeboard_compat.pth"
for f in __init__.py board.py microcontroller/__init__.py microcontroller/pin.py; do
	install -D -m 0644 "limeboard-compat/limeboard_blinka/$f" "$PY/limeboard_blinka/$f"
done
install -D -m 0644 limeboard-gpiozero/limeboard_gpiozero.py "$PY/limeboard_gpiozero.py"
for f in METADATA entry_points.txt; do
	install -D -m 0644 "limeboard-gpiozero/limeboard_gpiozero-1.0.dist-info/$f" \
		"$PY/limeboard_gpiozero-1.0.dist-info/$f"
done
install -D -m 0644 README.md "$P/usr/share/doc/limeboard-io/README.md"
copyright "$P/usr/share/doc/limeboard-io/copyright"
for s in postinst postrm; do
	install -D -m 0755 "packaging/limeboard-io/$s" "$P/DEBIAN/$s"
done
sed "s/@VERSION@/$VERSION/" packaging/limeboard-io/control > "$P/DEBIAN/control"
dpkg-deb --root-owner-group --build "$P" "$DIST/limeboard-io_${VERSION}_all.deb"

# limeboard-ha -------------------------------------------------------------
P="$WORK/limeboard-ha"
install -D -m 0755 limeboard-ha/limeboard-ha "$P/usr/bin/limeboard-ha"
install -D -m 0644 limeboard-ha/limeboard-ha.conf "$P/usr/share/limeboard-ha/limeboard-ha.conf"
install -D -m 0644 limeboard-ha/limeboard-ha.service "$P/usr/lib/systemd/system/limeboard-ha.service"
install -D -m 0644 limeboard-ha/README.md "$P/usr/share/doc/limeboard-ha/README.md"
copyright "$P/usr/share/doc/limeboard-ha/copyright"
for s in postinst prerm postrm; do
	install -D -m 0755 "packaging/limeboard-ha/$s" "$P/DEBIAN/$s"
done
sed "s/@VERSION@/$VERSION/" packaging/limeboard-ha/control > "$P/DEBIAN/control"
dpkg-deb --root-owner-group --build "$P" "$DIST/limeboard-ha_${VERSION}_all.deb"

ls -l "$DIST"
