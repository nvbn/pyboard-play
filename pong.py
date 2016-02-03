import pyb
from lib.ssd1306 import Display
from lib.joystick import Joystick

LIMIT_X = 127
LIMIT_Y = 63


class Unit(object):
    def __init__(self):
        self.reset()

    def reset(self):
        raise NotImplementedError

    def render(self, display):
        for x in range(int(self.x), int(self.x + self.w)):
            for y in range(int(self.y), int(self.y + self.h)):
                display.set_pixel(x, y, True)

    def intersects(self, other):
        return ((self.x <= other.x <= self.x + self.w)
                or (self.x <= (other.x + other.w) <= (self.x + self.w))) \
               and ((self.y <= other.y <= self.y + self.h)
                    or (self.y <= (other.y + other.h) <= (self.y + self.h)))


class Racket(Unit):
    def move(self, delta):
        updated = self.y + delta
        if updated < 0:
            updated = 0
        elif updated > LIMIT_Y - self.h:
            updated = LIMIT_Y - self.h
        self.y = updated


class Player(Racket):
    def reset(self):
        self.x, self.y, self.w, self.h = 3, 0, 3, 15

    def update(self, joystick):
        self.move(int(joystick.y / 10))


class Ai(Racket):
    def reset(self):
        self.x, self.y, self.w, self.h = 124, 0, 3, 15

    def update(self, ball):
        if self.y >= ball.y >= self.y + self.h:
            return
        elif self.y < ball.y:
            self.move((ball.y - self.y) % 10)
        else:
            self.move(0 - (self.y - ball.y) % 10)


class Ball(Unit):
    def reset(self):
        self.x, self.y, self.w, self.h = 10, 10, 5, 5
        self.delta_x = self.new_delta()
        self.delta_y = self.new_delta()

    def new_delta(self, previous=-1):
        delta = pyb.rng() % 5 + 5
        if previous > 0:
            return -delta
        else:
            return delta

    def bounce_with_wall(self):
        if self.y > LIMIT_Y:
            self.y = LIMIT_Y
            self.delta_y = -self.delta_y
        elif self.y < 0:
            self.y = 0
            self.delta_y = -self.delta_y

    def bounce_with_racket(self, racket):
        if racket.intersects(self):
            self.delta_y = self.new_delta(self.delta_y)
            self.delta_x = self.new_delta(self.delta_x)

    def update(self, player, ai):
        self.x += self.delta_x
        self.y += self.delta_y

        if self.x > LIMIT_X or self.x < 0:
            return True

        self.bounce_with_wall()

        self.bounce_with_racket(player)
        self.bounce_with_racket(ai)


class Game(object):
    def __init__(self):
        self.display = Display(pinout={'sda': 'Y10',
                                       'scl': 'Y9'},
                               height=64,
                               external_vcc=False)
        self.joystick = Joystick('X1', 'X2')
        self.started = False
        self.player = Player()
        self.ai = Ai()
        self.ball = Ball()

    def reset(self):
        self.started = False
        self.player.reset()
        self.ai.reset()
        self.ball.reset()

    def render(self):
        with self.display as display:
            self.player.render(display)
            self.ai.render(display)
            self.ball.render(display)

    def update(self):
        if not self.started:
            if self.joystick.x > 5:
                self.started = True
            return

        self.player.update(self.joystick)
        self.ai.update(self.ball)
        if self.ball.update(self.player, self.ai):
            self.reset()


if __name__ == '__main__':
    game = Game()

    while True:
        game.render()
        game.update()
        pyb.delay(100)
