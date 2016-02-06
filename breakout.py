import pyb
import math
from lib.ssd1306 import Display
from lib.keyes import Joystick
from lib.engine import Game, rectangle, text

GAME_NOT_STARTED = 0
GAME_ACTIVE = 1
GAME_OVER = 2

BRICK_W = 12
BRICK_H = 6
BRICK_BORDER = 4
BRICK_ROWS = 3

PADDLE_W = 16
PADDLE_H = 4

BALL_W = 3
BALL_H = 3
BALL_SPEED = 6
BALL_SPEED_BORDER = 0.5


def splash(w, h):
    for n in range(0, w, 20):
        yield from rectangle(x=n, y=0, w=10, h=h, fill=True)

    yield from rectangle(x=0, y=17, w=w, h=30, fill=False)
    yield from text(x=0, y=20, string='BREAKOUT', size=3)


def brick(data):
    yield from rectangle(x=data['x'] + BRICK_BORDER,
                         y=data['y'] + BRICK_BORDER,
                         w=BRICK_W - BRICK_BORDER,
                         h=BRICK_H - BRICK_BORDER,
                         fill=True)


def paddle(data):
    yield from rectangle(x=data['x'], y=data['y'],
                         w=PADDLE_W, h=PADDLE_H,
                         fill=True)


def ball(data):
    yield from rectangle(x=data['x'], y=data['y'],
                         w=BALL_W, h=BALL_H, fill=True)


def deck(state):
    for brick_data in state['bricks']:
        yield from brick(brick_data)

    yield from paddle(state['paddle'])
    yield from ball(state['ball'])


def game_over():
    yield from text(x=0, y=20, string='GAMEOVER', size=3)


def view(state):
    if state['status'] == GAME_NOT_STARTED:
        yield from splash(state['display']['width'],
                          state['display']['height'])
    else:
        yield from deck(state)
        if state['status'] == GAME_OVER:
            yield from game_over()


def get_initial_game_state(state):
    state['status'] = GAME_ACTIVE
    state['bricks'] = [{'x': x, 'y': yn * BRICK_H}
                       for x in range(0, state['display']['width'], BRICK_W)
                       for yn in range(BRICK_ROWS)]
    state['paddle'] = {'x': (state['display']['width'] - PADDLE_W) / 2,
                       'y': state['display']['height'] - PADDLE_H}

    ball_vx = BALL_SPEED_BORDER + pyb.rng() % (BALL_SPEED - BALL_SPEED_BORDER)
    ball_vy = -math.sqrt(BALL_SPEED ** 2 - ball_vx ** 2)
    state['ball'] = {'x': (state['display']['width'] - BALL_W) / 2,
                     'y': state['display']['height'] - PADDLE_H * 2 - BALL_W,
                     'vx': ball_vx,
                     'vy': ball_vy}
    return state


def update_paddle(paddle, joystick, w):
    paddle['x'] += int(joystick['x'] / 10)
    if paddle['x'] < 0:
        paddle['x'] = 0
    elif paddle['x'] > (w - PADDLE_W):
        paddle['x'] = w - PADDLE_W
    return paddle


def calculate_velocity(ball, item_x, item_w):
    intersection = (item_x + item_w - ball['x']) / item_w
    vx = ball['vx'] + BALL_SPEED * (0.5 - intersection)
    if vx > BALL_SPEED - BALL_SPEED_BORDER:
        vx = BALL_SPEED - BALL_SPEED_BORDER
    elif vx < BALL_SPEED_BORDER - BALL_SPEED:
        vx = BALL_SPEED_BORDER - BALL_SPEED

    vy = math.sqrt(BALL_SPEED ** 2 - vx ** 2)
    if ball['vy'] > 0:
        vy = - vy
    return vx, vy


def collide(ball, item, item_w, item_h):
    return item['x'] - BALL_W < ball['x'] < item['x'] + item_w \
           and item['y'] - BALL_H < ball['y'] < item['y'] + item_h


def update_ball(state):
    state['ball']['x'] += state['ball']['vx']
    state['ball']['y'] += state['ball']['vy']

    # Collide with left/right wall
    if state['ball']['x'] <= 0 or state['ball']['x'] >= state['display']['width']:
        state['ball']['vx'] = - state['ball']['vx']

    # Collide with top wall
    if state['ball']['y'] <= 0:
        state['ball']['vy'] = -state['ball']['vy']

    # Collide with paddle
    if collide(state['ball'], state['paddle'], PADDLE_W, PADDLE_H):
        vx, vy = calculate_velocity(state['ball'], state['paddle']['x'], PADDLE_W)
        state['ball'].update(vx=vx, vy=vy)

    # Collide with brick
    if state['ball']['y'] <= BRICK_ROWS * BRICK_W:
        for n, brick in enumerate(state['bricks']):
            if collide(state['ball'], brick, BRICK_W, BRICK_H):
                vx, vy = calculate_velocity(state['ball'], brick['x'], BRICK_W)
                state['ball'].update(vx=vx, vy=vy)
                state['bricks'].pop(n)

    return state


def is_game_over(state):
    return not state['bricks'] or state['ball']['y'] > state['display']['height']


def controller(state):
    if state['status'] in (GAME_NOT_STARTED, GAME_OVER)\
            and state['joystick']['clicked']:
        state = get_initial_game_state(state)
    elif state['status'] == GAME_ACTIVE:
        state['paddle'] = update_paddle(state['paddle'], state['joystick'],
                                        state['display']['width'])
        state = update_ball(state)
        if is_game_over(state):
            state['status'] = GAME_OVER
    return state


initial_state = {'status': GAME_NOT_STARTED}
breakout = Game(display=Display(pinout={'sda': 'Y10',
                                    'scl': 'Y9'},
                                height=64,
                                external_vcc=False),
                joystick=Joystick('X1', 'X2', 'X3'),
                initial_state=initial_state,
                view=view,
                controller=controller)

if __name__ == '__main__':
    breakout.run()
