import pyb


class Joystick(object):
    def __init__(self, pin_x, pin_y, btn):
        self._pin_x = pyb.ADC(pin_x)
        self._pin_y = pyb.ADC(pin_y)
        self._btn = pyb.Pin(btn, pyb.Pin.PULL_UP)

    @property
    def y(self):
        return -(self._pin_x.read() - 2000) / 20

    @property
    def x(self):
        return -(self._pin_y.read() - 2000) / 20

    @property
    def clicked(self):
        return self._btn.value()
