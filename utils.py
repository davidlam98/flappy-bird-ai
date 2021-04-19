from itertools import cycle
import random
import sys
import time
import pygame
from datetime import datetime, timedelta
from pygame.locals import *
import matplotlib.pyplot as plt
plt.ion()

def load_window(WINDOW_WIDTH, WINDOW_HEIGHT):
    global SCREEN
    SCREEN = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption('Q-Learning Flappy Bird AI') # Set the window name
    return SCREEN

def load_flappy_bird_animations(IMAGES):
    IMAGES['numbers'] = (
        pygame.image.load('assets/sprites/0.png').convert_alpha(),
        pygame.image.load('assets/sprites/1.png').convert_alpha(),
        pygame.image.load('assets/sprites/2.png').convert_alpha(),
        pygame.image.load('assets/sprites/3.png').convert_alpha(),
        pygame.image.load('assets/sprites/4.png').convert_alpha(),
        pygame.image.load('assets/sprites/5.png').convert_alpha(),
        pygame.image.load('assets/sprites/6.png').convert_alpha(),
        pygame.image.load('assets/sprites/7.png').convert_alpha(),
        pygame.image.load('assets/sprites/8.png').convert_alpha(),
        pygame.image.load('assets/sprites/9.png').convert_alpha()
    )

    IMAGES['gameover'] = pygame.image.load('assets/sprites/gameover.png').convert_alpha()
    IMAGES['message'] = pygame.image.load('assets/sprites/message.png').convert_alpha()
    IMAGES['base'] = pygame.image.load('assets/sprites/base.png').convert_alpha()
    return IMAGES['numbers'], IMAGES['gameover'], IMAGES['message'], IMAGES['base']

def load_flappy_bird_sounds(SOUNDS):
    if 'win' in sys.platform:
        soundExt = '.wav'
    else:
        soundExt = '.ogg'
    SOUNDS['die']    = pygame.mixer.Sound('assets/audio/die' + soundExt)
    SOUNDS['hit']    = pygame.mixer.Sound('assets/audio/hit' + soundExt)
    SOUNDS['point']  = pygame.mixer.Sound('assets/audio/point' + soundExt)
    SOUNDS['swoosh'] = pygame.mixer.Sound('assets/audio/swoosh' + soundExt)
    SOUNDS['wing']   = pygame.mixer.Sound('assets/audio/wing' + soundExt)
    return SOUNDS['die'], SOUNDS['hit'], SOUNDS['point'], SOUNDS['swoosh'], SOUNDS['wing']

def randomise_background(BACKGROUNDS_LIST, IMAGES):
    random_background = random.randint(0, 1)
    IMAGES['background'] = pygame.image.load(BACKGROUNDS_LIST[random_background]).convert()
    return IMAGES['background']

def randomise_bird_colour(BIRD_LIST, IMAGES):
    # select random bird sprites
    rand_bird = random.randint(0, len(BIRD_LIST) - 1)
    IMAGES['bird'] = (
        pygame.image.load(BIRD_LIST[rand_bird][0]).convert_alpha(),
        pygame.image.load(BIRD_LIST[rand_bird][1]).convert_alpha(),
        pygame.image.load(BIRD_LIST[rand_bird][2]).convert_alpha(),
    )
    return IMAGES['bird']

def randomise_pipe_colour(PIPES_LIST, IMAGES):
    # select random pipe sprites
    pipeindex = random.randint(0, len(PIPES_LIST) - 1)
    IMAGES['pipe'] = (pygame.transform.rotate(pygame.image.load(PIPES_LIST[pipeindex]).convert_alpha(), 180),pygame.image.load(PIPES_LIST[pipeindex]).convert_alpha())
    return IMAGES['pipe']


# Returns a list of two pipes, upper and lower in the form of x-y coordinates
def get_random_pipe(BASE, PIPE_GAP, IMAGES, WINDOW_WIDTH):
    """returns a randomly generated pipe"""
    # y of gap between upper and lower pipe
    gapY = random.randrange(0, int(BASE * 0.6 - PIPE_GAP))
    gapY += int(BASE * 0.2)
    pipeHeight = IMAGES['pipe'][0].get_height()
    pipeX = WINDOW_WIDTH + 10

    return [
        {'x': pipeX, 'y': gapY - pipeHeight},  # upper pipe
        {'x': pipeX, 'y': gapY + PIPE_GAP}, # lower pipe
    ]

def show_score(score, IMAGES, WINDOW_WIDTH, WINDOW_HEIGHT):
    """displays score in center of screen"""
    scoreDigits = [int(x) for x in list(str(score))]
    totalWidth = 0 # total width of all numbers to be printed

    for digit in scoreDigits:
        totalWidth += IMAGES['numbers'][digit].get_width()

    Xoffset = (WINDOW_WIDTH - totalWidth) / 2

    for digit in scoreDigits:
        SCREEN.blit(IMAGES['numbers'][digit], (Xoffset, WINDOW_HEIGHT * 0.1))
        Xoffset += IMAGES['numbers'][digit].get_width()

def check_crash(bird, upper_pipes, lower_pipes, IMAGES, BASE, HITMASKS):
    """returns True if bird collders with base or pipes."""
    pi = bird['index']
    bird['w'] = IMAGES['bird'][0].get_width()
    bird['h'] = IMAGES['bird'][0].get_height()

    # if bird crashes into ground
    if bird['y'] + bird['h'] >= BASE - 1:
        return [True, True]
    else:

        bird_rect = pygame.Rect(bird['x'], bird['y'],bird['w'], bird['h'])
        pipe_W = IMAGES['pipe'][0].get_width()
        pipe_H = IMAGES['pipe'][0].get_height()

        for u_pipe, l_pipe in zip(upper_pipes, lower_pipes):
            # upper and lower pipe rects
            u_pipe_rect = pygame.Rect(u_pipe['x'], u_pipe['y'], pipe_W, pipe_H)
            l_pipe_rect = pygame.Rect(l_pipe['x'], l_pipe['y'], pipe_W, pipe_H)

            # bird and upper/lower pipe hitmasks
            p_hit_mask = HITMASKS['bird'][pi]
            u_hit_mask = HITMASKS['pipe'][0]
            l_hit_mask = HITMASKS['pipe'][1]

            # if bird collided with upipe or lpipe
            uCollide = pixelCollision(bird_rect, u_pipe_rect, p_hit_mask, u_hit_mask)
            lCollide = pixelCollision(bird_rect, l_pipe_rect, p_hit_mask, l_hit_mask)

            if uCollide:
                return [True, False]
            elif lCollide:
                return [True, True]

    return [False, False]

def pixelCollision(rect1, rect2, hitmask1, hitmask2):
    """Checks if two objects collide and not just their rects"""
    rect = rect1.clip(rect2)

    if rect.width == 0 or rect.height == 0:
        return False

    x1, y1 = rect.x - rect1.x, rect.y - rect1.y
    x2, y2 = rect.x - rect2.x, rect.y - rect2.y
    xrange = range
    for x in xrange(rect.width):
        for y in xrange(rect.height):
            if hitmask1[x1+x][y1+y] and hitmask2[x2+x][y2+y]:
                return True
    return False

def get_hit_mask(image):
    mask = []
    xrange = range
    for x in xrange(image.get_width()):
        mask.append([])
        for y in xrange(image.get_height()):
            mask[x].append(bool(image.get_at((x,y))[3]))
    return mask

def setup_game(WINDOW_WIDTH, WINDOW_HEIGHT, IMAGES):
    bird_index = 0
    bird_index_iteration = cycle([0, 1, 2, 1])
    loop_iteration = 0

    bird_x = int(WINDOW_WIDTH * 0.2)
    bird_y = int((WINDOW_HEIGHT - IMAGES['bird'][0].get_height()) / 2)

    base_x = 0
    base_shift = IMAGES['base'].get_width() - IMAGES['background'].get_width()
    bird_shm_vals = {'val': 0, 'dir': 1}
    return {'bird_y': bird_y + bird_shm_vals['val'], 'base_x': base_x, 'bird_index_iteration': bird_index_iteration}

def print_training_log(score, time_start, EPISODES, sum_score):
    sum_score += score
    plt.plot(EPISODES, score, 'r.')
    if EPISODES % 50 == 0:
        print("Episode:", EPISODES, "Average Score:", sum_score/50, "Time Elapsed:",str(timedelta(seconds=time.time() - time_start)))
        plt.plot(EPISODES, sum_score/50, 'b*')
        plt.title('Every Score and Average Score per 50 episodes')
        plt.xlabel('Episodes')
        plt.ylabel('Score')
        sum_score = 0
    return sum_score
