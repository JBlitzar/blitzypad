import time
import board
from kmk.extensions.display.ssd1306 import SSD1306
from kmk.extensions.display import Display, TextEntry
from kmk.keys import KC
from kmk.kmk_keyboard import KMKKeyboard
import busio
from kmk.scanners.keypad import KeysScanner
from kmk.modules.macros import Press, Release, Tap, Macros
import neopixel


btn_tl = board.D7  # SW1 - GPIO1/RX
btn_tr = board.D8  # SW2 - GPIO2/SCK
btn_bl = board.D9  # SW3 - GPIO4/MISO
btn_br = board.D10  # SW4 - GPIO3/MOSI

extra_btn = board.D3  # SW5 - GPIO29/ADC3/A3

PINS = [btn_tl, btn_tr, btn_bl, btn_br, extra_btn]


try:
    i2c = busio.I2C(board.SCL, board.SDA)

    while not i2c.try_lock():
        pass
    print(
        "I2C addresses found:", [hex(device_address) for device_address in i2c.scan()]
    )
    i2c.unlock()

    display = SSD1306(128, 64, i2c, addr=0x3C)
except Exception as e:
    print(f"I2C setup failed: {e}")
    display = None


keyboard = KMKKeyboard()
keyboard.pixels = None


pixels = neopixel.NeoPixel(board.D0, 2, brightness=0.3, auto_write=False)


if display:
    display_ext = Display(
        display=display,
        width=128,
        height=32,
        dim_time=10,
        dim_target=0.2,
        off_time=1200,
        brightness=0.8,
    )
    display_ext.entries = [
        TextEntry(text="Hello, world!1", x=0, y=0, x_anchor="M"),
    ]
    keyboard.extensions.append(display_ext)

macros = Macros()
keyboard.modules.append(macros)

KEYMAP = [
    KC.W,
    KC.D,
    KC.A,
    KC.S,
    KC.MACRO("wow!"),
]

keyboard.matrix = KeysScanner(
    pins=PINS,
    value_when_pressed=False,
)

keyboard.keymap = [KEYMAP]

if __name__ == "__main__":
    keyboard.go()
    pixels[0] = (0, 0, 255)
    pixels[1] = (255, 0, 255)
    pixels.show()
