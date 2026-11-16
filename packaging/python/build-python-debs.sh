#!/bin/bash
# SPDX-License-Identifier: MIT
# Build python3-gpiozero, python3-rpi-lgpio and python3-lgpio into dist/ from
# the PyPI versions in versions, for Debian trixie and Ubuntu resolute armhf.
# lgpio's C extension is built in both distributions' containers (Python
# 3.13 and 3.14) and both go into one package. Needs docker with armhf
# emulation (binfmt/qemu).
set -euo pipefail

HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$HERE/../.." && pwd)
DIST="$ROOT/dist"
REV=$(cat "$HERE/revision")
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
mkdir -p "$DIST"

# license_in <dir>: the first license file in it
license_in() {
	local f
	f=$(find "$1" -maxdepth 2 -type f \( -iname 'LICEN[CS]E*' -o -iname 'UNLICEN[CS]E*' -o -iname 'COPYING*' \) | sort | head -1)
	[ -n "$f" ] || { echo "no license file in $1" >&2; return 1; }
	echo "$f"
}

version_of() { awk -v p="$1" '$1 == p {print $2}' "$HERE/versions"; }

# pypi_get <project> <version> <packagetype> <dest dir>: download the file
# of that type, verified against PyPI's sha256; prints its path
pypi_get() {
	python3 - "$@" <<'PY'
import hashlib, json, sys, urllib.request
project, version, ptype, dest = sys.argv[1:]
meta = json.load(urllib.request.urlopen(f"https://pypi.org/pypi/{project}/{version}/json"))
files = [f for f in meta["urls"] if f["packagetype"] == ptype
         and (ptype != "bdist_wheel" or f["filename"].endswith("-none-any.whl"))]
if not files:
    sys.exit(f"{project} {version}: no {ptype} on PyPI")
f = files[0]
data = urllib.request.urlopen(f["url"]).read()
if hashlib.sha256(data).hexdigest() != f["digests"]["sha256"]:
    sys.exit(f"{f['filename']}: sha256 mismatch")
path = f"{dest}/{f['filename']}"
open(path, "wb").write(data)
print(path)
PY
}

# deb_copyright <file> <upstream name> <source url> <license name> <license file>
deb_copyright() {
	{
		echo "Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/"
		echo "Upstream-Name: $2"
		echo "Source: $3"
		echo
		echo "Files: *"
		echo "License: $4"
		echo
		echo "License: $4"
		sed 's/^$/./; s/^/ /' "$5"
		echo
		echo "Files: debian/*"
		echo "Copyright: 2026 Citronics"
		echo "License: MIT"
		echo " Packaged by Citronics (https://github.com/Citronics/limeboard-extras)."
	} > "$1"
}

# install_wheel <wheel> <package dir>: unpack into dist-packages, with
# /usr/bin wrappers for its console scripts
install_wheel() {
	local py="$2/usr/lib/python3/dist-packages"
	mkdir -p "$py"
	python3 -m zipfile -e "$1" "$py"
	local info=$(ls -d "$py"/*.dist-info)
	echo dpkg > "$info/INSTALLER"
	rm -f "$info/RECORD"
	python3 - "$info/entry_points.txt" "$2/usr/bin" <<'PY'
import configparser, os, sys
ep, bindir = sys.argv[1:]
if not os.path.exists(ep):
    sys.exit(0)
c = configparser.ConfigParser(); c.optionxform = str; c.read(ep)
if "console_scripts" not in c:
    sys.exit(0)
os.makedirs(bindir, exist_ok=True)
for name, target in c["console_scripts"].items():
    mod, func = target.split(":")
    path = os.path.join(bindir, name)
    with open(path, "w") as f:
        f.write(f"#!/usr/bin/python3\nimport sys\nfrom {mod} import {func}\nsys.exit({func}())\n")
    os.chmod(path, 0o755)
PY
}

control() { # control <dir> <package> <version> <arch> <depends> <description> [extra]
	mkdir -p "$1/DEBIAN"
	{
		echo "Package: $2"
		echo "Version: $3"
		echo "Architecture: $4"
		echo "Maintainer: Citronics <info@citronics.eu>"
		echo "Depends: $5"
		[ -n "${7:-}" ] && echo "$7"
		echo "Section: python"
		echo "Priority: optional"
		echo "Description: $6"
		echo " Packaged by Citronics for the Limeboard from the PyPI release."
	} > "$1/DEBIAN/control"
}

# gpiozero -------------------------------------------------------------------
V=$(version_of gpiozero); P="$WORK/python3-gpiozero"
W=$(pypi_get gpiozero "$V" bdist_wheel "$WORK")
install_wheel "$W" "$P"
LIC=$(license_in "$P"/usr/lib/python3/dist-packages/gpiozero-*.dist-info)
mkdir -p "$P/usr/share/doc/python3-gpiozero"
deb_copyright "$P/usr/share/doc/python3-gpiozero/copyright" gpiozero https://github.com/gpiozero/gpiozero BSD-3-Clause "$LIC"
control "$P" python3-gpiozero "$V-$REV" all "python3, python3-colorzero" \
	"simple interface to GPIO devices with Raspberry Pi"
dpkg-deb --root-owner-group --build "$P" "$DIST/python3-gpiozero_${V}-${REV}_all.deb"

# rpi-lgpio ------------------------------------------------------------------
V=$(version_of rpi-lgpio); P="$WORK/python3-rpi-lgpio"
W=$(pypi_get rpi-lgpio "$V" bdist_wheel "$WORK")
install_wheel "$W" "$P"
LIC=$(license_in "$P"/usr/lib/python3/dist-packages/rpi_lgpio-*.dist-info)
mkdir -p "$P/usr/share/doc/python3-rpi-lgpio"
deb_copyright "$P/usr/share/doc/python3-rpi-lgpio/copyright" rpi-lgpio https://github.com/waveform80/rpi-lgpio MIT "$LIC"
control "$P" python3-rpi-lgpio "$V-$REV" all "python3, python3-lgpio" \
	"RPi.GPIO API on top of lgpio" "Conflicts: python3-rpi.gpio"
dpkg-deb --root-owner-group --build "$P" "$DIST/python3-rpi-lgpio_${V}-${REV}_all.deb"

# lgpio ----------------------------------------------------------------------
# The C extension, built once per Python: the alert thread polls every 10 ms
# instead of 0.5 ms (about 16% of a CPU on an MSM8974 otherwise).
V=$(version_of lgpio); P="$WORK/python3-lgpio"
SDIST=$(pypi_get lgpio "$V" sdist "$WORK")
mkdir -p "$WORK/lgpio-build"
for image in debian:trixie ubuntu:resolute; do
	docker run --rm --platform linux/arm/v7 -v "$WORK:/w" -e SDIST="/w/$(basename "$SDIST")" "$image" bash -euc '
		export DEBIAN_FRONTEND=noninteractive
		apt-get update -qq >/dev/null
		apt-get install -y -qq --no-install-recommends gcc libc6-dev python3-dev python3-pip python3-setuptools swig >/dev/null
		mkdir /src && tar -xzf "$SDIST" -C /src && cd /src/lgpio-*
		sed -i "s#{0, 5e5}; /\* 0.5 ms timeout \*/#{0, 1e7}; /* 10 ms timeout */#" src/lgPthAlerts.c
		grep -q "{0, 1e7}" src/lgPthAlerts.c
		PYPI=1 CFLAGS="-std=gnu17" pip3 wheel --no-deps --no-build-isolation -w /w/lgpio-build . >/dev/null
	'
done
mkdir -p "$P/usr/lib/python3/dist-packages"
for w in "$WORK"/lgpio-build/lgpio-*.whl; do
	python3 -m zipfile -e "$w" "$P/usr/lib/python3/dist-packages"
done
INFO=$(ls -d "$P"/usr/lib/python3/dist-packages/lgpio-*.dist-info)
echo dpkg > "$INFO/INSTALLER"; rm -f "$INFO/RECORD" "$INFO/WHEEL"
ls "$P"/usr/lib/python3/dist-packages/_lgpio.cpython-313-*.so "$P"/usr/lib/python3/dist-packages/_lgpio.cpython-314-*.so >/dev/null
tar -xzf "$SDIST" -C "$WORK"
LIC=$(license_in "$WORK/lgpio-$V" 2>/dev/null || true)
[ -n "$LIC" ] || { printf 'This is free and unencumbered software released into the public domain.\n\nSee https://unlicense.org\n' > "$WORK/UNLICENSE"; LIC="$WORK/UNLICENSE"; }
mkdir -p "$P/usr/share/doc/python3-lgpio"
deb_copyright "$P/usr/share/doc/python3-lgpio/copyright" lgpio http://abyz.me.uk/lg/py_lgpio.html Unlicense "$LIC"
control "$P" python3-lgpio "$V-$REV" armhf "python3 (>= 3.13), python3 (<< 3.15), libc6" \
	"Linux GPIO library (lg) for Python"
dpkg-deb --root-owner-group --build "$P" "$DIST/python3-lgpio_${V}-${REV}_armhf.deb"

ls -l "$DIST"/python3-*.deb
