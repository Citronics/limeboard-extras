# limeboard-config

`raspi-config` for the Limeboard: it sets up the header's buses, the serial
console and the STM32 firmware. See
[Turning the buses on](../README.md#turning-the-buses-on) and
[Serial console, firmware and raspi-config](../README.md#serial-console-firmware-and-raspi-config).

The buses are off until `/etc/limeboard/config.txt` turns them on with the
lines of a Pi's `config.txt` (`dtparam=i2c_arm=on`, `dtparam=spi=on`,
`dtoverlay=spi1-3cs`, `dtoverlay=i2c0`); `serial_console=on` adds a login
console on `/dev/serial0`.

| File | Installed as |
|---|---|
| `limeboard-config` | `/usr/bin/limeboard-config` |
| `raspi-config` | `/usr/bin/raspi-config`: `raspi-config nonint` commands, answered by `limeboard-config` |
| `config.txt` | `/etc/limeboard/config.txt`, everything off |
| `limeboard.conf` | `/etc/modprobe.d/limeboard.conf`: what `limeboard-config` generates from that `config.txt` |
| `limeboard-serial-console` | `/usr/libexec/limeboard-serial-console`: waits for `/dev/serial0`, runs `getty` on it |
| `limeboard-serial-console.service` | the systemd service running it (Debian, Ubuntu); Buildroot uses an `/etc/inittab` line |
| `limeboard-io.version` | `/usr/share/limeboard/limeboard-io.version`, next to the firmware `limeboard-io.bin` built from `limeboard-firmware` |

For the buses, `limeboard-config` writes the options of the `citronics-dln2`
driver (`i2c_ports`, `spi<bus>_cs<n>`) to `/etc/modprobe.d/limeboard.conf`
for the next boot, and applies them at once: it sets them in
`/sys/module/citronics_dln2/parameters/` and binds the I2C and SPI ports
whose settings changed again, leaving the GPIO chip, the other ports and the
programs using them alone. The firmware update uses
`dfu-util`. Lime images (Buildroot, Debian, Ubuntu) install all of these.
