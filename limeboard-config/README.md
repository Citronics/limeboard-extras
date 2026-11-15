# limeboard-config

Turns the Limeboard header's I2C and SPI buses on and off, the Raspberry Pi
way: they are off until `/etc/limeboard/config.txt` turns them on with the
lines of a Pi's `config.txt` (`dtparam=i2c_arm=on`, `dtparam=spi=on`,
`dtoverlay=spi1-3cs`, `dtoverlay=i2c0`). See
[Turning the buses on](../README.md#turning-the-buses-on).

| File | Installed as |
|---|---|
| `limeboard-config` | `/usr/bin/limeboard-config` |
| `config.txt` | `/etc/limeboard/config.txt`, every bus off |
| `limeboard.conf` | `/etc/modprobe.d/limeboard.conf`: what `limeboard-config` generates from that `config.txt` |

`limeboard-config` writes the parameters of the kernel's `i2c_dln2` (`ports`)
and `spi_dln2` (`spi<bus>_cs<n>`) modules to `/etc/modprobe.d/limeboard.conf`,
reloads udev's module settings, and reloads the two modules when no program
is using them. Lime images (Buildroot, Debian, Ubuntu) install all three.
