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
    3: ("GPIO2", "i2c", "I2C SDA · PB9"),
    4: ("5 V", "5v", ""),
    5: ("GPIO3", "i2c", "I2C SCL · PB6"),
    6: ("GND", "gnd", ""),
    7: ("GPIO4", "gpio", "PC9"),
    8: ("GPIO14", "uart", "UART TXD · PA2"),
    9: ("GND", "gnd", ""),
    10: ("GPIO15", "uart", "UART RXD · PA3"),
    11: ("GPIO17", "adc", "ADC 4 · PC1"),
    12: ("GPIO18", "gpio", "PC6"),
    13: ("GPIO27", "gpio", "PB8"),
    14: ("GND", "gnd", ""),
    15: ("GPIO22", "adc", "ADC 3 · PC0"),
    16: ("GPIO23", "adc", "ADC 7 · PC4"),
    17: ("3.3 V", "3v3", ""),
    18: ("GPIO24", "gpio", "PB5"),
    19: ("GPIO10", "spi", "SPI MOSI · PA7"),
    20: ("GND", "gnd", ""),
    21: ("GPIO9", "spi", "SPI MISO · PA6"),
    22: ("GPIO25", "adc", "ADC 5 · PC2"),
    23: ("GPIO11", "spi", "SPI SCLK · PA5"),
    24: ("GPIO8", "spi", "SPI CE0 · PA1"),
    25: ("GND", "gnd", ""),
    26: ("GPIO7", "spi", "SPI CE1 · PA4"),
    27: ("GPIO0", "gpio", "PB4"),
    28: ("GPIO1", "gpio", "PA8"),
    29: ("GPIO5", "adc", "ADC 0 · PA0"),
    30: ("GND", "gnd", ""),
    31: ("GPIO6", "gpio", "PA10"),
    32: ("GPIO12", "adc", "ADC 1 · PB0"),
    33: ("GPIO13", "gpio", "PB13"),
    34: ("GND", "gnd", ""),
    35: ("GPIO19", "gpio", "PB14"),
    36: ("GPIO16", "adc", "ADC 2 · PB1"),
    37: ("GPIO26", "gpio", "PB15"),
    38: ("GPIO20", "adc", "ADC 6 · PC3"),
    39: ("GND", "gnd", ""),
    40: ("GPIO21", "gpio", "PB10"),
}

ONBOARD = [
    ("line 28", "LED red", "PC11", "led_r"),
    ("line 29", "LED green", "PC12", "led_g"),
    ("line 30", "LED blue", "PC7", "led_b"),
    ("line 31", "User button", "PB2", "btn"),
]

COLOURS = {  # fill, text on fill
    "3v3": ("#f0a830", "#2b1d00"),
    "5v": ("#d8433b", "#ffffff"),
    "gnd": ("#2f3437", "#ffffff"),
    "gpio": ("#7f9a4e", "#ffffff"),
    "i2c": ("#2f7fd0", "#ffffff"),
    "spi": ("#c4439a", "#ffffff"),
    "uart": ("#7a52c7", "#ffffff"),
    "adc": ("#1f9e89", "#ffffff"),
    "led_r": ("#d8433b", "#ffffff"),
    "led_g": ("#3a9d4a", "#ffffff"),
    "led_b": ("#2f6fd0", "#ffffff"),
    "btn": ("#5b6770", "#ffffff"),
}

LEGEND = [
    ("3v3", "3.3 V"), ("5v", "5 V"), ("gnd", "Ground"), ("gpio", "GPIO"),
    ("i2c", "I2C"), ("spi", "SPI"), ("uart", "UART (ttyACM)"), ("adc", "GPIO + ADC"),
]

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


H = TOP + 20 * ROW + 250
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
for kind, name in LEGEND:
    out.append(f'<circle cx="{lx}" cy="{ly}" r="7" fill="{COLOURS[kind][0]}" stroke="#111" stroke-width="1"/>')
    text(lx + 13, ly + 4.5, name, 12.5)
    lx += 106 if kind != "uart" else 130

# Onboard signals
oy = ly + 46
text(70, oy, "On the board (not on the header)", 15, "bold")
for i, (line, name, stm, kind) in enumerate(ONBOARD):
    x = 70 + i * 215
    y = oy + 30
    fill, ink = COLOURS[kind]
    out.append(f'<rect x="{x}" y="{y - 13}" width="200" height="26" rx="13" fill="{fill}"/>')
    text(x + 14, y + 5, name, 13, "bold", "start", ink)
    text(x + 186, y + 5, f"{line} · {stm}", 11.5, "normal", "end", ink, ' opacity="0.9"')

ny = oy + 78
for i, note in enumerate([
    "All signals are 3.3 V logic: never connect 5 V to a GPIO. The header works with switch S3 in DFLT.",
    "ADC n = in_voltagen_raw of the IIO device \"dln2-adc\" (10-bit, 0-3.3 V). The I2C bus also carries the board's",
    "power controller at 0x28. No hardware PWM. Pin positions follow the Raspberry Pi layout. Details: PINOUT.md",
]):
    text(70, ny + i * 19, note, 12.5, "normal", "start", "#444")

out.append("</svg>")

dest = Path(__file__).resolve().parent.parent / "images" / "limeboard-pinout.svg"
dest.parent.mkdir(exist_ok=True)
dest.write_text("\n".join(out) + "\n")
print(dest)
