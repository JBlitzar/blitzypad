import time

import board
import busio
import digitalio
import displayio
import terminalio
import usb_hid

import adafruit_displayio_ssd1306
import i2cdisplaybus
from adafruit_display_text import bitmap_label
from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode

try:
    from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
except ImportError:
    KeyboardLayoutUS = None


# time.sleep(3)


class DebouncedInput:
    def __init__(self, pin: digitalio.DigitalInOut, debounce_s: float = 0.02):
        self.pin = pin
        self.debounce_s = debounce_s
        self._last_raw = pin.value
        self.value = pin.value
        self._last_change_t = time.monotonic()

    def update(self, now: float) -> bool:
        raw = self.pin.value
        if raw != self._last_raw:
            self._last_raw = raw
            self._last_change_t = now
        if (now - self._last_change_t) >= self.debounce_s and raw != self.value:
            self.value = raw
            return True
        return False


class RotaryEncoder:
    _TRANSITIONS = {
        (0b00, 0b01): +1,
        (0b01, 0b11): +1,
        (0b11, 0b10): +1,
        (0b10, 0b00): +1,
        (0b00, 0b10): -1,
        (0b10, 0b11): -1,
        (0b11, 0b01): -1,
        (0b01, 0b00): -1,
    }

    def __init__(
        self,
        a: digitalio.DigitalInOut,
        b: digitalio.DigitalInOut,
        steps_per_detent: int = 4,
    ):
        self.a = a
        self.b = b
        self.steps_per_detent = steps_per_detent
        self._prev = self._read_state()
        self._accum = 0

    def _read_state(self) -> int:
        return ((1 if self.a.value else 0) << 1) | (1 if self.b.value else 0)

    def update(self) -> int:
        cur = self._read_state()
        if cur == self._prev:
            return 0
        step = self._TRANSITIONS.get((self._prev, cur), 0)
        self._prev = cur
        if step == 0:
            return 0
        self._accum += step
        if self._accum >= self.steps_per_detent:
            self._accum = 0
            return +1
        if self._accum <= -self.steps_per_detent:
            self._accum = 0
            return -1
        return 0


def _make_input(pin_id) -> digitalio.DigitalInOut:
    pin = digitalio.DigitalInOut(pin_id)
    pin.direction = digitalio.Direction.INPUT
    pin.pull = digitalio.Pull.UP
    return pin


keyboard = Keyboard(usb_hid.devices)
consumer = ConsumerControl(usb_hid.devices)
layout = KeyboardLayoutUS(keyboard) if KeyboardLayoutUS else None

btn_tl = DebouncedInput(_make_input(board.D7))
btn_tr = DebouncedInput(_make_input(board.D8))
btn_bl = DebouncedInput(_make_input(board.D9))
btn_br = DebouncedInput(_make_input(board.D10))
extra_btn = DebouncedInput(_make_input(board.D3))

enc_a = _make_input(board.A1)
enc_b = _make_input(board.A0)
# enc_sw = DebouncedInput(_make_input(board.A3))
encoder = RotaryEncoder(enc_a, enc_b)

buttons = [
    (btn_tl, Keycode.W),
    (btn_tr, Keycode.D),
    (btn_bl, Keycode.A),
    (btn_br, Keycode.S),
]


# try:
#     import neopixel
#     pixels = neopixel.NeoPixel(board.D0, 2, brightness=0.3, auto_write=True)
#     pixels.fill((0, 0, 20))
# except ImportError:
#     pixels = None


sda, scl = board.SDA, board.SCL
i2c = busio.I2C(scl, sda)
display_bus = i2cdisplaybus.I2CDisplayBus(i2c, device_address=0x3C)
display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=128, height=64)

lbl = bitmap_label.Label(
    terminalio.FONT,
    text="\nready\n",
    color=0xFFFFFF,
    label_direction="UPD",
)
lbl.anchor_point = (0.5, 0.5)
lbl.scale = 2
lbl.anchored_position = (display.width // 2, display.height // 2)

group = displayio.Group()
group.append(lbl)
display.root_group = group


def _set_status(text: str) -> None:
    try:
        lbl.text = f"\n{text}\n"
    except Exception:
        pass


while True:
    now = time.monotonic()
    for btn, keycode in buttons:
        if btn.update(now):
            if btn.value is False:
                keyboard.press(keycode)
            else:
                keyboard.release(keycode)
    if extra_btn.update(now) and extra_btn.value is False:
        if layout:
            layout.write("wow!")
        else:
            for kc in (Keycode.W, Keycode.O, Keycode.W):
                keyboard.send(kc)
            keyboard.press(Keycode.SHIFT)
            keyboard.send(Keycode.ONE)
            keyboard.release(Keycode.SHIFT)
        _set_status("wow!")
    detent = encoder.update()
    if detent == +1:
        consumer.send(ConsumerControlCode.VOLUME_INCREMENT)
        _set_status("vol+")
    elif detent == -1:
        consumer.send(ConsumerControlCode.VOLUME_DECREMENT)
        _set_status("vol-")
    # if enc_sw.update(now) and enc_sw.value is False:
    #     consumer.send(ConsumerControlCode.MUTE)
    #     _set_status("mute")
    time.sleep(0.001)
