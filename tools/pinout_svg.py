#!/usr/bin/env python3
"""Generate images/limeboard-pinout.svg, the header pinout diagram.

Usage: python3 tools/pinout_svg.py
The pin data below is the same as in PINOUT.md; update both together.
"""
from pathlib import Path
from xml.sax.saxutils import escape

# Physical pin -> (label, kind, details)
# kind selects the colour; details is the small second line.
PINS = {
    1: ("3.3 V", "3v3", ""),
    2: ("5 V", "5v", ""),
    3: ("GPIO2", "i2c", "I2C1 SDA · PB9"),
    4: ("5 V", "5v", ""),
    5: ("GPIO3", "i2c", "I2C1 SCL · PB6"),
    6: ("GND", "gnd", ""),
    7: ("GPIO4", "gpio", "PC9"),
    8: ("GPIO14", "uart", "UART TXD · PA2"),
    9: ("GND", "gnd", ""),
    10: ("GPIO15", "uart", "UART RXD · PA3"),
    11: ("GPIO17", "spi_b", "SPI1 CE1 · ADC 4 · PC1"),
    12: ("GPIO18", "spi_b", "SPI1 CE0 · PC6"),
    13: ("GPIO27", "gpio", "PB8"),
    14: ("GND", "gnd", ""),
    15: ("GPIO22", "adc", "ADC 3 · PC0"),
    16: ("GPIO23", "adc", "ADC 7 · PC4"),
    17: ("3.3 V", "3v3", ""),
    18: ("GPIO24", "gpio", "PB5"),
    19: ("GPIO10", "spi", "SPI0 MOSI · PA7"),
    20: ("GND", "gnd", ""),
    21: ("GPIO9", "spi", "SPI0 MISO · PA6"),
    22: ("GPIO25", "adc", "ADC 5 · PC2"),
    23: ("GPIO11", "spi", "SPI0 SCLK · PA5"),
    24: ("GPIO8", "spi", "SPI0 CE0 · PA1"),
    25: ("GND", "gnd", ""),
    26: ("GPIO7", "spi", "SPI0 CE1 · PA4"),
    27: ("GPIO0", "i2c_b", "I2C0 SDA · PB4"),
    28: ("GPIO1", "i2c_b", "I2C0 SCL · PA8"),
    29: ("GPIO5", "adc", "ADC 0 · PA0"),
    30: ("GND", "gnd", ""),
    31: ("GPIO6", "gpio", "PA10"),
    32: ("GPIO12", "adc", "ADC 1 · PB0"),
    33: ("GPIO13", "gpio", "PB13"),
    34: ("GND", "gnd", ""),
    35: ("GPIO19", "spi_b", "SPI1 MISO · PB14"),
    36: ("GPIO16", "spi_b", "SPI1 CE2 · ADC 2 · PB1"),
    37: ("GPIO26", "gpio", "PB15"),
    38: ("GPIO20", "spi_b", "SPI1 MOSI · ADC 6 · PC3"),
    39: ("GND", "gnd", ""),
    40: ("GPIO21", "spi_b", "SPI1 SCLK · PB10"),
}

# One RGB LED: each colour channel is driven by its own STM32 pin
LED_CHANNELS = [
    ("Red", "line 28", "PC11", "led_r"),
    ("Green", "line 29", "PC12", "led_g"),
    ("Blue", "line 30", "PC7", "led_b"),
]
BUTTON = ("User button", "line 31", "PB2", "btn")

COLOURS = {  # fill, text on fill
    "3v3": ("#f0a830", "#2b1d00"),
    "5v": ("#d8433b", "#ffffff"),
    "gnd": ("#2f3437", "#ffffff"),
    "gpio": ("#7f9a4e", "#ffffff"),
    "i2c": ("#2f7fd0", "#ffffff"),
    "spi": ("#c4439a", "#ffffff"),
    "i2c_b": ("#8fbbe8", "#0d2f55"),   # second bus: a pin that is GPIO until used
    "spi_b": ("#e3a6cf", "#4d1239"),
    "uart": ("#7a52c7", "#ffffff"),
    "adc": ("#1f9e89", "#ffffff"),
    "led_r": ("#d8433b", "#ffffff"),
    "led_g": ("#3a9d4a", "#ffffff"),
    "led_b": ("#2f6fd0", "#ffffff"),
    "btn": ("#5b6770", "#ffffff"),
}

LEGEND = [
    ("3v3", "3.3 V"), ("5v", "5 V"), ("gnd", "Ground"), ("gpio", "GPIO"),
    ("adc", "GPIO + ADC"), ("uart", "UART (ttyACM, the only one)"), None,
    ("i2c", "I2C1"), ("i2c_b", "I2C0 (second bus)"), ("spi", "SPI0"), ("spi_b", "SPI1 (second bus)"),
]
LEGEND_WIDTH = {"uart": 220, "adc": 120, "i2c_b": 175, "spi_b": 175}

FONT = "DejaVu Sans, Helvetica, Arial, sans-serif"
W = 980
ROW = 30            # vertical distance between pin rows
TOP = 118           # y of the first pin row
HX = W // 2         # header centre
PITCH = 30          # horizontal distance between the two pin columns
LABEL_W = 250       # label box width
LABEL_GAP = 34      # gap between the header and the label boxes

out = []


def text(x, y, s, size=13, weight="normal", anchor="start", fill="#222", extra=""):
    out.append(f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" '
               f'font-weight="{weight}" text-anchor="{anchor}" fill="{fill}"{extra}>{escape(s)}</text>')


def label_box(x, y, w, pin, label, kind, details, align):
    fill, ink = COLOURS[kind]
    out.append(f'<rect x="{x}" y="{y - 12}" width="{w}" height="24" rx="12" fill="{fill}"/>')
    num_x = x + w - 16 if align == "end" else x + 16
    text(num_x, y + 4.5, str(pin), 11, "bold", "middle", ink, ' opacity="0.85"')
    if align == "end":   # left column: text right-aligned towards the header
        text(x + w - 34, y + 5, label, 13.5, "bold", "end", ink)
        if details:
            text(x - 10, y + 5, details, 12, "normal", "end", "#444")
    else:
        text(x + 34, y + 5, label, 13.5, "bold", "start", ink)
        if details:
            text(x + w + 10, y + 5, details, 12, "normal", "start", "#444")


H = TOP + 20 * ROW + 290
out.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
out.append(f'<rect width="{W}" height="{H}" fill="#ffffff"/>')

text(HX, 44, "Limeboard 40-pin header", 26, "bold", "middle")
text(HX, 72, "Limeboard I/O firmware · GPIO numbers = BCM = lines of the Linux GPIO chip \"dln2\"",
     13.5, "normal", "middle", "#555")

# Header body
body_top = TOP - ROW / 2 - 6
out.append(f'<rect x="{HX - PITCH / 2 - 21}" y="{body_top}" width="{PITCH + 42}" '
           f'height="{20 * ROW + 12}" rx="6" fill="#1d1f21"/>')
text(HX, body_top - 8, "pin 1", 11, "bold", "end", "#555", f' dx="-{PITCH / 2 + 6}"')

for row in range(20):
    y = TOP + row * ROW
    for col, pin in enumerate((2 * row + 1, 2 * row + 2)):
        label, kind, details = PINS[pin]
        px = HX - PITCH / 2 + col * PITCH
        fill = COLOURS[kind][0]
        if pin == 1:
            out.append(f'<rect x="{px - 10}" y="{y - 10}" width="20" height="20" rx="2" fill="#c9a24a"/>')
        else:
            out.append(f'<circle cx="{px}" cy="{y}" r="10" fill="#c9a24a"/>')
        out.append(f'<circle cx="{px}" cy="{y}" r="6.5" fill="{fill}" stroke="#111" stroke-width="1.5"/>')
        if col == 0:
            x = HX - PITCH / 2 - 21 - LABEL_GAP - LABEL_W
            out.append(f'<line x1="{x + LABEL_W}" y1="{y}" x2="{px - 10}" y2="{y}" stroke="#bbb" stroke-width="1.5"/>')
            bx = x + LABEL_W - 150
            label_box(bx, y, 150, pin, label, kind, details, "end")
        else:
            x = HX + PITCH / 2 + 21 + LABEL_GAP
            out.append(f'<line x1="{px + 10}" y1="{y}" x2="{x}" y2="{y}" stroke="#bbb" stroke-width="1.5"/>')
            label_box(x, y, 150, pin, label, kind, details, "start")

# Legend
ly = TOP + 20 * ROW + 28
lx = 70
for entry in LEGEND:
    if entry is None:  # next row
        lx, ly = 70, ly + 26
        continue
    kind, name = entry
    width = LEGEND_WIDTH.get(kind, 95)
    out.append(f'<circle cx="{lx}" cy="{ly}" r="7" fill="{COLOURS[kind][0]}" stroke="#111" stroke-width="1"/>')
    text(lx + 13, ly + 4.5, name, 12.5)
    lx += width

# Onboard signals
oy = ly + 46
text(70, oy, "On the board (not on the header)", 15, "bold")
y = oy + 34
# The RGB LED: one component, three channels side by side in one frame
out.append(f'<rect x="70" y="{y - 20}" width="610" height="40" rx="20" fill="#eef0f2" stroke="#c8ccd0"/>')
out.append('<defs><linearGradient id="rgb" x1="0" x2="1" y1="0" y2="1">'
           '<stop offset="0" stop-color="#d8433b"/><stop offset="0.5" stop-color="#3a9d4a"/>'
           '<stop offset="1" stop-color="#2f6fd0"/></linearGradient></defs>')
out.append(f'<circle cx="94" cy="{y}" r="11" fill="url(#rgb)" stroke="#111" stroke-width="1"/>')
text(112, y + 5, "RGB LED", 14, "bold")
for i, (name, line, stm, kind) in enumerate(LED_CHANNELS):
    x = 190 + i * 162
    fill, ink = COLOURS[kind]
    out.append(f'<rect x="{x}" y="{y - 13}" width="154" height="26" rx="13" fill="{fill}"/>')
    text(x + 12, y + 5, name, 12.5, "bold", "start", ink)
    text(x + 143, y + 5, f"{line} · {stm}", 11, "normal", "end", ink, ' opacity="0.9"')
name, line, stm, kind = BUTTON
fill, ink = COLOURS[kind]
out.append(f'<rect x="700" y="{y - 13}" width="210" height="26" rx="13" fill="{fill}"/>')
text(714, y + 5, name, 13, "bold", "start", ink)
text(896, y + 5, f"{line} · {stm}", 11.5, "normal", "end", ink, ' opacity="0.9"')
text(70, y + 40, "One RGB LED with three colour channels; each channel is a GPIO line (1 = on), "
     "which gives 8 colours.", 12.5, "normal", "start", "#444")

ny = oy + 104
for i, note in enumerate([
    "All signals are 3.3 V logic: never connect 5 V to a GPIO. The header works with switch S3 in DFLT.",
    "Bus pins stay plain GPIO until the bus is used. The second buses need the kernel's multi-port dln2 driver.",
    "ADC n = in_voltagen_raw of the IIO device \"dln2-adc\" (10-bit, 0-3.3 V). I2C1 also carries the board's",
    "power controller at 0x28. No hardware PWM. Pin positions follow the Raspberry Pi layout. Details: PINOUT.md",
]):
    text(70, ny + i * 19, note, 12.5, "normal", "start", "#444")

out.append("</svg>")

dest = Path(__file__).resolve().parent.parent / "images" / "limeboard-pinout.svg"
dest.parent.mkdir(exist_ok=True)
dest.write_text("\n".join(out) + "\n")
print(dest)
