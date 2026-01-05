# inspired from https://github.com/hackclub/hackpad/blob/main/hackpads/cyaopad/firmware/main.py + https://blueprint.hackclub.com/hackpad#firmware
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


btn_tl = board.GP1
btn_tr = board.GP2
btn_bl = board.GP4
btn_br = board.GP3

extra_btn = board.GP29

pixels = neopixel.NeoPixel(board.GP0, 2, brightness=0.3, auto_write=False)


PINS = [btn_tl, btn_tr, btn_bl, btn_br, extra_btn]


bus = busio.I2C(board.GP_SCL, board.GP_SDA)
driver = SSD1306(i2c=bus, device_address=0x3C)

display = Display(
    display=driver,
    width=128,
    height=32,
    dim_time=10,
    dim_target=0.2,
    off_time=1200,
    brightness=0.8,
)

display.entries = [
    TextEntry(text="Hello, world!1", x=0, y=0, x_anchor="M"),
]
keyboard = KMKKeyboard()
keyboard.extensions.append(display)

macros = Macros()
keyboard.modules.append(macros)

# placeholder for now, I plan on addressing these in client-side software
KEYMAP = [
    KC.W,
    KC.A,
    KC.S,
    KC.D,
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
