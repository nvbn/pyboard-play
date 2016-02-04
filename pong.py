import pyb
import math
from lib.ssd1306 import Display
from lib.keyes import Joystick
from lib.engine import Game, rectangle, text

GAME_NOT_STARTED = 0
GAME_ACTIVE = 1
GAME_WIN = 2
GAME_LOSE = 3

BALL_SPEED = 5

BALL_W = 3
BALL_H = 3

PADDLE_W = 2
PADDLE_H = 15

MAX_ANGLE = 30


# Views:
def splash(w, h):
    for n in range(0, w, 20):
        yield from rectangle(x=n,
                             y=0,
                             w=10,
                             h=h,
                             fill=True)

    yield from rectangle(x=0,
                         y=17,
                         w=w,
                         h=30,
                         fill=False)
    yield from text(x=0, y=20, string='PONG!', size=3)
    yield from text(x=80, y=20, string='Click to')
    yield from text(x=80, y=30, string='START!')


def paddle(user):
    yield from rectangle(x=user['x'],
                         y=user['y'],
                         w=PADDLE_W,
                         h=PADDLE_H,
                         fill=True)


def ball(x, y):
    yield from rectangle(x=x,
                         y=y,
                         w=BALL_W,
                         h=BALL_H,
                         fill=True)


def deck(player, ai, ball_data):
    yield from paddle(player)
    yield from paddle(ai)
    yield from ball(ball_data['x'], ball_data['y'])


def view(state):
    if state['state'] == GAME_NOT_STARTED:
        yield from splash(w=state['display']['width'],
                          h=state['display']['height'])
    else:
        yield from deck(player=state['player'],
                        ai=state['ai'],
                        ball_data=state['ball'])
        if state['state'] == GAME_WIN:
            yield from text(0, 20, "YOU WIN!", 3)
        elif state['state'] == GAME_LOSE:
            yield from text(0, 20, "YOU LOSE!", 3)


# Works with state:
def intersects(ball, paddle):
    return paddle['x'] - BALL_W <= ball['x'] <= paddle['x'] + PADDLE_W and \
           paddle['y'] - BALL_H <= ball['y'] <= paddle['y'] + PADDLE_H


def get_velocity(angle):
    return {'vx': BALL_SPEED * math.cos(angle),
            'vy': BALL_SPEED * math.sin(angle)}


def velocity_for_intersection(ball, paddle):
    relative = paddle['y'] + PADDLE_H / 2 - ball['y']
    normalized = relative / (PADDLE_H / 2)
    angle = normalized * MAX_ANGLE
    return get_velocity(angle)


def get_new_game_state(w, h):
    angle = pyb.rng() % MAX_ANGLE + 360 - MAX_ANGLE
    return {'player': {'x': 0, 'y': 0},
            'ai': {'x': w - 2,
                   'y': h - 15},
            'ball': {'x': 5,
                     'y': 5,
                     'velocity': get_velocity(angle)},
            'score': 0}


def update_ball(ball, player, ai, h):
    ball['x'] += ball['velocity']['vx']
    ball['y'] += ball['velocity']['vy']

    if ball['y'] < 0 or ball['y'] > h:
        ball['velocity']['vy'] = -ball['velocity']['vy']

    if intersects(ball, player):
        ball['velocity'] = velocity_for_intersection(ball, player)
    elif intersects(ball, ai):
        ball['velocity'] = velocity_for_intersection(ball, ai)

    return ball


def update_paddle(paddle, h):
    if paddle['y'] < 0:
        paddle['y'] = 0
    elif paddle['y'] > (h - PADDLE_H):
        paddle['y'] = h - PADDLE_H
    return paddle


def update_player(player, joystick, h):
    player['y'] += int(joystick['y'] / 10)
    return update_paddle(player, h)


def update_ai(ai, ball, h):
    if ai['y'] < ball['y']:
        ai['y'] += (ball['y'] - ai['y']) % 10
    elif ai['y'] + PADDLE_H > ball['y']:
        ai['y'] += 0 - (ball['y'] - ai['y']) % 10
    return update_paddle(ai, h)


def update_game_state(ball, w):
    if ball['x'] < 0:
        return GAME_LOSE
    elif ball['x'] > w:
        return GAME_WIN
    else:
        return GAME_ACTIVE


def controller(state):
    if state['state'] == GAME_ACTIVE:
        state['ball'] = update_ball(
                state['ball'],
                state['player'],
                state['ai'],
                state['display']['height'])
        state['player'] = update_player(state['player'],
                                        state['joystick'],
                                        state['display']['height'])
        state['ai'] = update_ai(state['ai'],
                                state['ball'],
                                state['display']['height'])
        state['state'] = update_game_state(state['ball'],
                                           state['display']['width'])
    elif state['joystick']['clicked']:
        state.update(get_new_game_state(state['display']['width'],
                                        state['display']['height']))
        state['state'] = GAME_ACTIVE
    return state


pong = Game(display=Display(pinout={'sda': 'Y10',
                                    'scl': 'Y9'},
                            height=64,
                            external_vcc=False),
            joystick=Joystick('X1', 'X2', 'X3'),
            initial_state={'state': GAME_NOT_STARTED},
            view=view,
            controller=controller)

if __name__ == '__main__':
    pong.run()
