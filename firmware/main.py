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


from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS


# time.sleep(3)


# An input action. This can be a keycode, consumer control code, or lambda.
class InputActionType:
    KEYCODE = 1
    CONSUMER_CONTROL = 2
    LAMBDA = 3
    MACRO = 4


class InputAction:
    def __init__(self, value, action_type: int = InputActionType.KEYCODE):
        self.action_type = action_type
        self.value = value

    def perform(
        self,
        keyboard: Keyboard,
        consumer: ConsumerControl,
        layout: KeyboardLayoutUS,
        btn_value: bool = None,
    ):
        if self.action_type == InputActionType.KEYCODE:
            if btn_value is not None:
                if btn_value is False:
                    keyboard.press(self.value)
                else:
                    keyboard.release(self.value)
            else:
                keyboard.press(self.value)
                time.sleep(0.05)
                keyboard.release(self.value)
        elif self.action_type == InputActionType.CONSUMER_CONTROL:
            consumer.send(self.value)
        elif self.action_type == InputActionType.LAMBDA:
            if btn_value is not None:
                if btn_value is True:
                    self.value()
            else:
                self.value()  # I sure do love python dynamic typing
        elif self.action_type == InputActionType.MACRO:
            # type using layout
            if btn_value is not None:
                if btn_value is True:
                    layout.write(self.value)
            else:
                layout.write(self.value)
        else:
            raise ValueError("Unknown action type")


# a series of modes, each mode has a name and a mapping of inputs to actions (tl, tr, bl, br, enc+enc-)
# extra switches modes
# display current mode
class InputMap:
    def __init__(self, name: str, button_map):
        self.name = name
        self.button_map = button_map

    def get_action_for_button(self, button_index: int):
        return self.button_map.get(button_index, None)


MAPS = [
    InputMap(
        "WASD",
        {
            0: InputAction(Keycode.W),
            1: InputAction(Keycode.D),
            2: InputAction(Keycode.A),
            3: InputAction(Keycode.S),
            4: InputAction(
                ConsumerControlCode.VOLUME_INCREMENT, InputActionType.CONSUMER_CONTROL
            ),
            5: InputAction(
                ConsumerControlCode.VOLUME_DECREMENT, InputActionType.CONSUMER_CONTROL
            ),
        },
    ),
    InputMap(
        "test",
        {
            0: InputAction(Keycode.A),
            1: InputAction(Keycode.B),
            2: InputAction(Keycode.C),
            3: InputAction("hello, world!!", InputActionType.MACRO),
            4: InputAction(Keycode.E),
            5: InputAction(Keycode.F),
        },
    ),
]

MAP = MAPS[0]


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
        steps_per_detent: int = 2,
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

encoder = RotaryEncoder(enc_a, enc_b)

# buttons = [
#     (btn_tl, Keycode.W),
#     (btn_tr, Keycode.D),
#     (btn_bl, Keycode.A),
#     (btn_br, Keycode.S),
# ]

buttons = [btn_tl, btn_tr, btn_bl, btn_br]


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
    for btn in buttons:
        if btn.update(now):
            InputAction.perform(
                MAP.get_action_for_button(buttons.index(btn)),
                keyboard,
                consumer,
                layout,
                btn.value,
            )
    if extra_btn.update(now) and extra_btn.value is False:
        MAP = MAPS[(MAPS.index(MAP) + 1) % len(MAPS)]
        _set_status(MAP.name)
    detent = encoder.update()
    if detent == +1:
        InputAction.perform(
            MAP.get_action_for_button(len(buttons)),
            keyboard,
            consumer,
            layout,
        )
    elif detent == -1:
        InputAction.perform(
            MAP.get_action_for_button(len(buttons) + 1),
            keyboard,
            consumer,
            layout,
        )
    # if enc_sw.update(now) and enc_sw.value is False:
    #     consumer.send(ConsumerControlCode.MUTE)
    #     _set_status("mute")
    time.sleep(0.001)
