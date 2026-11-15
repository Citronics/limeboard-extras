# Example 6: SPI

The Limeboard has two SPI buses, on the Raspberry Pi's spi0 and spi1 pins:

| Signal | SPI0: GPIO (pin) | SPI1: GPIO (pin) |
|---|---|---|
| MOSI | GPIO10 (19) | GPIO20 (38) |
| MISO | GPIO9 (21) | GPIO19 (35) |
| SCLK | GPIO11 (23) | GPIO21 (40) |
| CE0 | GPIO8 (24) | GPIO18 (12) |
| CE1 | GPIO7 (26) | GPIO17 (11) |
| CE2 | – | GPIO16 (36) |
| Device files | `/dev/spidev0.0`, `0.1` | `/dev/spidev1.0`, `1.1`, `1.2` |
| Clock | 328 kHz to 42 MHz | 164 kHz to 21 MHz |

Both buses are off by default, as on a Pi. Turn them on with the same
lines as a Pi's `config.txt`, in `/etc/limeboard/config.txt`, or with
`limeboard-config` (see [Turning the buses on](../../README.md#turning-the-buses-on)):

```sh
sudo limeboard-config enable spi0       # dtparam=spi=on: /dev/spidev0.0, 0.1
sudo limeboard-config enable spi1       # dtoverlay=spi1-3cs: /dev/spidev1.0, 1.1, 1.2
```

Programs then open the `/dev/spidevB.C` of their bus B and chip select C. A
bus's pins stay plain GPIOs until a program uses the bus, and each chip
select's pin until that chip select is used, so SPI1 only takes GPIO16/17 if
you use its CE1/CE2. For SPI1 with fewer chip selects, use
`dtoverlay=spi1-1cs` or `spi1-2cs` in the file.

These need a kernel with the Limeboard's dln2 changes (Citronics kernels
with "spi: dln2: add the devices on the chip selects" and "mfd: dln2: add a
cell for each I2C and SPI port"): `modinfo -p spi_dln2` lists `spi0_cs0` to
`spi1_cs3` on those. Older kernels have one SPI controller and no
`/dev/spidev`.

## Check the bus: loopback

Turn the bus on first (`sudo limeboard-config enable spi0`, or `spi1`).

Connect MOSI to MISO with a jumper wire, pin 19 to 21 for SPI0, pin 38 to
35 for SPI1, then:

```sh
sudo python3 loopback.py                    # SPI0, CE0: /dev/spidev0.0
sudo python3 loopback.py /dev/spidev0.1     # SPI0, CE1
sudo python3 loopback.py /dev/spidev1.0     # SPI1, CE0
```

[`loopback.py`](loopback.py) sends random bytes at three speeds and checks
that they come back. Without the jumper, every byte reads 0xFF.

## Using SPI from Python

**py-spidev**, as on a Pi:

```python
import spidev

spi = spidev.SpiDev()
spi.open(0, 0)                  # SPI0, CE0: /dev/spidev0.0 (SPI1: spi.open(1, 0))
spi.max_speed_hz = 1_000_000
print(spi.xfer2([0x01, 0x80, 0x00]))
```

**gpiozero**, for example an MCP3008 ADC on CE0:

```python
from gpiozero import MCP3008

pot = MCP3008(channel=0)                    # SPI0, CE0
pot1 = MCP3008(channel=0, clock_pin=21, mosi_pin=20, miso_pin=19,
               select_pin=18)               # SPI1, CE0
print(pot.value)
```

For SPI1, give the pins: gpiozero 2.0.1's `port=`/`device=` arguments
always take SPI0's clock and data pins, also on a Raspberry Pi.

**Adafruit Blinka**: `board.SPI()` is this bus (see
[limeboard-compat](../../limeboard-compat/README.md)):

```python
import board, busio, digitalio
from adafruit_bus_device.spi_device import SPIDevice

spi = board.SPI()                                          # SPI0
spi1 = busio.SPI(board.SCLK_1, board.MOSI_1, board.MISO_1)  # SPI1
device = SPIDevice(spi, digitalio.DigitalInOut(board.D5))  # chip select on GPIO5
```

With Blinka, use another GPIO than the bus's CE pins for a library's chip
select: those belong to the SPI bus once used.

## Choosing the devices on the chip selects

`dtparam=spi=on` and the `spi1-Ncs` overlays put `spidev` on the chip
selects. To use a kernel driver for a chip instead, as a `dtoverlay=` for
that chip would on a Pi, add a line to `/etc/limeboard/config.txt` with
`spi<bus>_cs<chip select>`:

```sh
spi0_cs1=mcp3008
```

Each takes `<device>[,irq=<gpio>][,speed=<hz>][,mode=<0-3>]`:

| Part | Meaning |
|---|---|
| `<device>` | `spidev`, `none`, or a kernel driver's device name, e.g. `mcp3008` (driver `mcp320x`), `mcp2515` (`mcp251x`) |
| `irq=<gpio>` | the header GPIO (BCM number) wired to the chip's interrupt pin |
| `speed=<hz>` | the chip's maximum clock |
| `mode=<0-3>` | SPI mode (clock polarity and phase) |

A chip select set this way is on even if its bus is not. For example, an
MCP2515 CAN controller on SPI1 CE0 with its interrupt on GPIO25:

```sh
spi1_cs0=mcp2515,irq=25,speed=10000000
```

Then apply and check:

```sh
sudo limeboard-config
ls /sys/bus/spi/devices/                              # spi1.0
cat /sys/bus/spi/devices/spi1.0/modalias              # spi:mcp2515
```

The kernel driver itself must be available: `modinfo mcp320x` must find it.
The Lime kernels do not build SPI chip drivers yet, only spidev: a chip name
creates the device, which waits for its driver.

## Limits

- **Clock:** SPI0 328 kHz to 42 MHz, SPI1 164 kHz to 21 MHz (the STM32's
  bus clock divided by 2 to 256). Slower requests fail with "Invalid
  argument".
- **Speed:** every transfer goes over USB, 256 bytes at a time (the driver
  splits longer ones, keeping the chip selected). Expect a few hundred KB/s
  at best, and about 1 ms per transfer.
- **Interrupts** from `irq=` arrive over USB, about 1 ms late.
- **Drivers that need more than an interrupt**, such as reset or enable
  pins, clocks or regulators, cannot get them this way. On a Pi they come
  from the device tree.
