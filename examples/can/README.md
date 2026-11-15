# Example 7: CAN with an SPI CAN HAT

CAN HATs for the Raspberry Pi put a CAN controller on SPI: an MCP2515 (classic
CAN) or an MCP2518FD (CAN FD), with an interrupt on a GPIO. On the Limeboard
the kernel's own drivers (`mcp251x`, `mcp251xfd`) run them, and Linux sees an
ordinary CAN interface, `can0`, for `ip`, `candump` and `cansend`, as on a
Pi.

Tested with a Waveshare RS485 CAN HAT (rev 2.1, MCP2515, 12 MHz crystal) on
a 500 kbit/s bus with a Waveshare USB-CAN-A on a PC: standard and extended
frames in both directions, no errors. Sending sustained about 330 frames per
second; receiving, 250 frames per second arrived complete.

## What it needs

- A kernel with CAN support (`modinfo mcp251x` finds the driver; Lime kernels
  build the CAN core, `can-raw`, `vcan`, `mcp251x` and `mcp251xfd` as
  modules) and the Limeboard's dln2 changes (the `clock=` and `trigger=`
  chip select settings).
- Limeboard I/O firmware 1.3 or later: `limeboard-config firmware` shows the
  version, `sudo limeboard-config firmware update` installs it.
- `iproute2` (a BusyBox `ip` cannot set a CAN bitrate) and `can-utils`.
- **Power the board off before plugging a HAT.** Do not use a HAT's own DC
  input if it has one: it would feed the board's 5 V rail.

## Turning it on

Add the HAT's line from its manufacturer's instructions to
`/etc/limeboard/config.txt`, as in a Pi's `config.txt`, then apply:

```sh
# Waveshare RS485 CAN HAT (12 MHz crystal; 8 MHz on boards bought before 2019-08)
dtoverlay=mcp2515-can0,oscillator=12000000,interrupt=25,spimaxfrequency=2000000
```

```sh
sudo limeboard-config
dmesg | grep mcp251         # mcp251x spi0.0 can0: MCP2515 successfully initialized.
```

Other HATs, with their usual lines:

| HAT | `config.txt` |
|---|---|
| MCP2515 HATs (PiCAN2, Waveshare RS485 CAN HAT, …) | `dtoverlay=mcp2515-can0,oscillator=<crystal Hz>,interrupt=25` |
| Waveshare 2-CH CAN FD HAT (mode A) | `dtoverlay=mcp251xfd,spi0-0,interrupt=25` and `dtoverlay=mcp251xfd,spi1-0,interrupt=24` |

`limeboard-config` turns these lines into the chip select settings
`spi0_cs0=mcp2515,irq=25,clock=12000000,speed=2000000`, which can also be
written directly. Lines it does not support are reported.

## Using it

Check the HAT without a bus, in the controller's loopback mode:

```sh
sudo ip link set can0 up type can bitrate 500000 loopback on
candump can0 &
cansend can0 123#DEADBEEF        # appears twice: the local echo and the frame received back
```

On a real bus (120 Ω termination at both ends):

```sh
sudo ip link set can0 down
sudo ip link set can0 up type can bitrate 500000
candump can0
```

A CAN FD controller also takes a data bitrate:

```sh
sudo ip link set can0 up type can bitrate 500000 dbitrate 2000000 fd on
cansend can0 123##1.DEADBEEF
```

In Python, `socket.AF_CAN` or the `python-can` library work as on a Pi.

## Limits

- **Throughput.** Every frame means an interrupt and several SPI transfers
  over USB, about a millisecond each. The MCP2515 sends about 330 frames per
  second and receives at least 250 complete, while a busy 500 kbit/s bus can
  carry 4000. Fine for tests,
  diagnostics and lightly loaded buses; a busy bus loses frames, as the
  MCP2515 holds only two received frames.
- **Interrupt latency** is about a millisecond.
- **One controller per chip select and interrupt line.** HATs that use the
  same chip select and interrupt (most MCP2515 HATs: spi0 CE0, GPIO25)
  cannot be stacked.

## The RS485 side of the RS485 CAN HAT

The RS485 transceiver is on the board's UART, `/dev/serial0`, and switches
between sending and receiving by itself:

```sh
stty -F /dev/serial0 9600 raw -echo
echo hello > /dev/serial0          # to the device on A/B
cat /dev/serial0                   # from it
```

RS485 needs a second device on the A/B pair, such as a USB-RS485 adapter on
a PC: the HAT does not hear itself while sending. GPIO4 (RSE) only matters
when the board's resistor is moved to manual direction control.
