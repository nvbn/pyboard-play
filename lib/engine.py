import pyb


# Primitives:

class Point(object):
    def __init__(self, x, y, fill):
        self.x = int(x)
        self.y = int(y)
        self.fill = bool(fill)

    def draw(self, display):
        display.set_pixel(self.x, self.y, self.fill)

    def translate(self, x, y):
        return Point(x + self.x, y + self.y, self.fill)


class Text(object):
    def __init__(self, x, y, string, size=1, space=1):
        self.x = x
        self.y = y
        self.string = string
        self.size = size
        self.space = space

    def draw(self, display):
        display.draw_text(self.x, self.y, self.string, self.size, self.space)

    def translate(self, x, y):
        return Text(x + self.x, y + self.y, self.string, self.size, self.space)


def relative(fn):
    def wrapper(x, y, *args, **kwargs):
        for primitive in fn(*args, **kwargs):
            yield primitive.translate(x, y)

    return wrapper


# Components:
@relative
def rectangle(w, h, fill):
    for x in range(w):
        for y in range(h):
            yield Point(x, y, fill)


def point(x, y, fill):
    yield Point(x, y, fill)


def text(x, y, string, size=1, space=1):
    yield Text(x, y, string, size, space)


class Game(object):
    def __init__(self, display, joystick, initial_state, controller, view):
        self.display = display
        self.joystick = joystick
        self.initial_state = initial_state
        self.controller = controller
        self.view = view

    def _draw(self, primitives):
        for primitive in primitives:
            primitive.draw(self.display)

    def _update_devices_info(self, state):
        return dict(state,
                    display={'width': self.display.width,
                             'height': self.display.height},
                    joystick={'x': self.joystick.x,
                              'y': self.joystick.y,
                              'clicked': self.joystick.clicked})

    def run(self):
        state = self.initial_state
        while True:
            state = self._update_devices_info(state)
            state = self.controller(state)
            primitives = self.view(state)
            with self.display:
                self._draw(primitives)
            pyb.wfi()
