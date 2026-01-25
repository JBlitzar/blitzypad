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
from kmk.modules.encoder import EncoderHandler
from kmk.extensions.media_keys import MediaKeys
import board, busio, displayio, os, terminalio
import adafruit_displayio_ssd1306
from adafruit_display_text import label
import i2cdisplaybus
from adafruit_display_text import bitmap_label


btn_tl = board.D7  # SW1 - GPIO1/RX
btn_tr = board.D8  # SW2 - GPIO2/SCK
btn_bl = board.D9  # SW3 - GPIO4/MISO
btn_br = board.D10  # SW4 - GPIO3/MOSI

extra_btn = board.D3  # SW5 - GPIO29/ADC3/A3

PINS = [btn_tl, btn_tr, btn_bl, btn_br, extra_btn]


#


keyboard = KMKKeyboard()
keyboard.pixels = None

keyboard.extensions.append(MediaKeys())

ENC_A = board.A1  # GPIO27
ENC_B = board.A0  # GPIO26
ENC_SW = board.A3  # GPIO28

encoder = EncoderHandler()
encoder.pins = ((ENC_A, ENC_B, ENC_SW),)

encoder.map = ((KC.VOLD, KC.VOLU, KC.MUTE),)


keyboard.modules.append(encoder)


pixels = neopixel.NeoPixel(board.D0, 2, brightness=0.3, auto_write=False)


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
sda, scl = board.SDA, board.SCL

i2c = busio.I2C(scl, sda)
display_bus = i2cdisplaybus.I2CDisplayBus(i2c, device_address=0x3C)
display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=128, height=64)

lbl = bitmap_label.Label(
    terminalio.FONT,
    text="\nhello world\n",
    color=0xFFFFFF,
    label_direction="UPD",  # upside down
)

lbl.anchor_point = (0.5, 0.5)
lbl.scale = 2
lbl.anchored_position = (display.width // 2, display.height // 2)

group = displayio.Group()
group.append(lbl)
display.root_group = group

if __name__ == "__main__":
    pixels[0] = (0, 0, 255)
    pixels[1] = (255, 0, 255)
    pixels.show()

    keyboard.go()
