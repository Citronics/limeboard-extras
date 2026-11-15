# Example 6: SPI

The Limeboard's SPI bus is on the Raspberry Pi pins:

| Signal | GPIO | Header pin |
|---|---|---|
| MOSI | GPIO10 | 19 |
| MISO | GPIO9 | 21 |
| SCLK | GPIO11 | 23 |
| CE0 (chip select 0) | GPIO8 | 24 |
| CE1 (chip select 1) | GPIO7 | 26 |

As on a Raspberry Pi with SPI enabled, programs use it through
`/dev/spidev0.0` (CE0) and `/dev/spidev0.1` (CE1).

These need a kernel whose `spi-dln2` driver creates the devices on the chip
selects (Citronics kernels with "spi: dln2: add the devices on the chip
selects"). `modinfo -p spi_dln2` lists `cs0` to `cs3` on those. Older
kernels have the SPI controller but no `/dev/spidev`.

## Check the bus: loopback

Connect MOSI (pin 19) to MISO (pin 21) with a jumper wire, then:

```sh
sudo python3 loopback.py                    # /dev/spidev0.0
sudo python3 loopback.py /dev/spidev0.1
```

[`loopback.py`](loopback.py) sends random bytes at three speeds and checks
that they come back. Without the jumper, every byte reads 0xFF.

## Using SPI from Python

**py-spidev**, as on a Pi:

```python
import spidev

spi = spidev.SpiDev()
spi.open(0, 0)                  # bus 0, CE0: /dev/spidev0.0
spi.max_speed_hz = 1_000_000
print(spi.xfer2([0x01, 0x80, 0x00]))
```

**gpiozero**, for example an MCP3008 ADC on CE0:

```python
from gpiozero import MCP3008

pot = MCP3008(channel=0)
print(pot.value)
```

**Adafruit Blinka**: `board.SPI()` is this bus (see
[limeboard-compat](../../limeboard-compat/README.md)):

```python
import board, busio, digitalio
from adafruit_bus_device.spi_device import SPIDevice

spi = board.SPI()
device = SPIDevice(spi, digitalio.DigitalInOut(board.D5))  # chip select on GPIO5
```

With Blinka, use another GPIO than CE0 or CE1 for a library's chip select:
those two belong to the SPI bus.

## Choosing the devices on the chip selects

By default both chip selects are `spidev`. To use a kernel driver for a chip
instead, as a `dtoverlay=` line would on a Pi, set it in
`/etc/modprobe.d/limeboard-spi.conf`:

```sh
options spi_dln2 cs1=mcp3008
```

Each chip select takes `<device>[,irq=<gpio>][,speed=<hz>][,mode=<0-3>]`:

| Part | Meaning |
|---|---|
| `<device>` | `spidev` (default), `none`, or a kernel driver's device name, e.g. `mcp3008` (driver `mcp320x`), `mcp2515` (`mcp251x`) |
| `irq=<gpio>` | the header GPIO (BCM number) wired to the chip's interrupt pin |
| `speed=<hz>` | the chip's maximum clock |
| `mode=<0-3>` | SPI mode (clock polarity and phase) |

For example, an MCP2515 CAN controller on CE0 with its interrupt on GPIO25:

```sh
options spi_dln2 cs0=mcp2515,irq=25,speed=10000000 cs1=none
```

The settings apply when the firmware appears. After a change, reboot, or:

```sh
sudo udevadm control --reload                         # for later resets of the STM32
sudo rmmod spi_dln2 && sudo modprobe spi_dln2          # apply now
ls /sys/bus/spi/devices/                              # spi0.0, spi0.1
cat /sys/bus/spi/devices/spi0.1/modalias              # spi:mcp3008
```

The kernel driver itself must be available: `modinfo mcp320x` must find it.
The Lime kernels do not build SPI chip drivers yet, only spidev: a chip name
creates the device, which waits for its driver.

## Limits

- **Clock:** 328 kHz to 42 MHz (84 MHz divided by 2 to 256). Slower
  requests fail with "Invalid argument".
- **Speed:** every transfer goes over USB, 256 bytes at a time (the driver
  splits longer ones, keeping the chip selected). Expect a few hundred KB/s
  at best, and about 1 ms per transfer.
- **Interrupts** from `irq=` arrive over USB, about 1 ms late.
- **Drivers that need more than an interrupt**, such as reset or enable
  pins, clocks or regulators, cannot get them this way. On a Pi they come
  from the device tree.
