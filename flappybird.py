from itertools import cycle
import random
import sys
import time
import pygame
from utils import *
from pygame.locals import *
from q_learning import q_learning
from datetime import datetime, timedelta


pygame.init()
clock = pygame.time.Clock() # Initialise clock

WINDOW_WIDTH  = 288 # Width of window
WINDOW_HEIGHT = 512 # Height of window
PIPE_GAP = 125 # gap between pipes
BASE = WINDOW_HEIGHT * 0.79 # Where the base starts
START_PIPE = WINDOW_WIDTH - 100 # Where the pipe starts

IMAGES, SOUNDS, HITMASKS = {}, {}, {}

crash_reward = -500 # Reward for dying
score_reward = 15 # Reward for passing pipe
factor = 4  # Divides the no. of screen pixels by 10

# Import images
BIRD_LIST = (('assets/sprites/redbird-upflap.png','assets/sprites/redbird-midflap.png','assets/sprites/redbird-downflap.png'),('assets/sprites/bluebird-upflap.png','assets/sprites/bluebird-midflap.png','assets/sprites/bluebird-downflap.png'),('assets/sprites/yellowbird-upflap.png','assets/sprites/yellowbird-midflap.png','assets/sprites/yellowbird-downflap.png')) # Import yellow bird
BACKGROUNDS_LIST = ('assets/sprites/background-day.png','assets/sprites/background-night.png',)
PIPES_LIST = ('assets/sprites/pipe-green.png','assets/sprites/pipe-red.png',)

SCREEN = load_window(WINDOW_WIDTH, WINDOW_HEIGHT) # Load window
IMAGES['numbers'], IMAGES['gameover'], IMAGES['message'], IMAGES['base'] = load_flappy_bird_animations(IMAGES) # Load bird animations
SOUNDS['die'], SOUNDS['hit'], SOUNDS['point'], SOUNDS['swoosh'], SOUNDS['wing'] = load_flappy_bird_sounds(SOUNDS) # Load bird sounds

IMAGES['background'] = randomise_background(BACKGROUNDS_LIST, IMAGES) # Select random background
IMAGES['bird'] = randomise_bird_colour(BIRD_LIST, IMAGES) # Select random bird
IMAGES['pipe'] = randomise_pipe_colour(PIPES_LIST, IMAGES) #Select random pipe colour
HITMASKS['pipe'] = (get_hit_mask(IMAGES['pipe'][0]),get_hit_mask(IMAGES['pipe'][1])) # Hitmask for pipe
HITMASKS['bird'] = (get_hit_mask(IMAGES['bird'][0]),get_hit_mask(IMAGES['bird'][1]),get_hit_mask(IMAGES['bird'][2])) # Hitmask for bird

game = setup_game(WINDOW_WIDTH, WINDOW_HEIGHT, IMAGES)

bird = q_learning() # Initialise bird for Q-Learning

def main():
    sum_score = 0
    time_start = time.time()

    EPISODES = 0
    while EPISODES < 2000: # 2,000 episodes of training
        sum_score = start_training(time_start, EPISODES, sum_score)
        EPISODES += 1

def start_training(time_start, EPISODES, sum_score):
    score = bird_index = loop_iteration = 0
    bird_index_iteration = game['bird_index_iteration']
    bird_x, bird_y = int(WINDOW_WIDTH * 0.2), game['bird_y']
    base_x = game['base_x']
    base_shift = IMAGES['base'].get_width() - IMAGES['background'].get_width()
    new_pipe1 = get_random_pipe(BASE, PIPE_GAP, IMAGES, WINDOW_WIDTH)
    new_pipe2 = get_random_pipe(BASE, PIPE_GAP, IMAGES, WINDOW_WIDTH)

    upper_pipes = [{'x': START_PIPE, 'y': new_pipe1[0]['y']}, {'x': START_PIPE + (WINDOW_WIDTH / 2), 'y': new_pipe2[0]['y']}] # List of upper pipes
    lower_pipes = [{'x': START_PIPE, 'y': new_pipe1[1]['y']},{'x': START_PIPE + (WINDOW_WIDTH / 2), 'y': new_pipe2[1]['y']}] # List of lower pipes

    pipe_vel_x             = -4    # Velocity of pipe
    bird_vel_y             =  -9   # Bird velocity along Y
    bird_max_vel_y         =  5   # Max bird velocity along Y, descend speed
    bird_min_vel_y         =  -8   # Max bird velocity along Y, max ascend speed
    bird_acc_y             =   1   # Bird downward acceleration
    bird_rotate            =  45   # Bird rotation
    bird_vel_rotate        =   3   # Bird angular speed
    bird_rotate_threshold  =  20   # Bird rotation threshold
    bird_flap_acc          =  -9   # Bird speed on flapping
    bird_flapped           = False # True when Bird flaps

    bird_tuple = [] # Initialise tuple
    active_pipe = 0

    while True:
        #clock.tick(30)
        reward = 0
        current_state = (round((bird_y-lower_pipes[active_pipe]['y'])/factor), round((lower_pipes[active_pipe]['x']-bird_x)/factor), bird_vel_y)
        bird.append_state(current_state)
        action, max_val = bird.max_Qvalue(current_state)

        if action:
                if bird_y > -2 * IMAGES['bird'][0].get_height():
                    bird_vel_y = bird_flap_acc
                    bird_flapped = True

        # Increment score for a new pipe passed
        bird_mid_pos = bird_x + IMAGES['bird'][0].get_width() / 2
        #Iterate through each of the pipes
        for pipe in upper_pipes:
            pipe_mid_pos = pipe['x'] + IMAGES['pipe'][0].get_width() / 2
            if pipe_mid_pos <= bird_mid_pos < pipe_mid_pos + 4: #Increment score only if the pipe has 'just' passed
                score += 1
                active_pipe+=1
                reward +=score_reward

        # bird index base_x change
        if (loop_iteration + 1) % 3 == 0:
            bird_index = next(bird_index_iteration)
        loop_iteration = (loop_iteration + 1) % 30
        base_x = -((-base_x + 100) % base_shift)

        # rotate the bird
        if bird_rotate > -90:
            bird_rotate -= bird_vel_rotate

        # bird's movement
        if bird_vel_y < bird_max_vel_y and not bird_flapped:
            bird_vel_y += bird_acc_y
        if bird_flapped:
            bird_flapped = False

            # more rotation to cover the threshold (calculated in visible rotation)
            bird_rotate = 45

        # Drop the bird due to gravity
        bird_height = IMAGES['bird'][bird_index].get_height()
        bird_y += min(bird_vel_y, BASE - bird_y - bird_height) # Check if drop height is more than the space between bird and base

        # move pipes to left
        for u_pipe, l_pipe in zip(upper_pipes, lower_pipes):
            u_pipe['x'] += pipe_vel_x
            l_pipe['x'] += pipe_vel_x

        # add new pipe when first pipe is about to touch left of screen
        if 0 < upper_pipes[0]['x'] < 5:
            newPipe = get_random_pipe(BASE, PIPE_GAP, IMAGES, WINDOW_WIDTH)
            upper_pipes.append(newPipe[0])
            lower_pipes.append(newPipe[1])

        # remove first pipe if its out of the screen
        if upper_pipes[0]['x'] < -IMAGES['pipe'][0].get_width():
            upper_pipes.pop(0)
            lower_pipes.pop(0)
            active_pipe-=1

        # check for crash here
        crash_check = check_crash({'x': bird_x, 'y': bird_y, 'index': bird_index}, upper_pipes, lower_pipes, IMAGES, BASE, HITMASKS)

        # Check for crash, if crashed then assign die reward
        if crash_check[0]:
            reward += crash_reward

        future_state = (round((bird_y-lower_pipes[active_pipe]['y'])/factor), round((lower_pipes[active_pipe]['x']-bird_x)/factor), bird_vel_y)
        bird.append_state(future_state)
        bird_tuple.append((current_state, action, reward, future_state))

        # draw sprites
        SCREEN.blit(IMAGES['background'], (0,0))

        for u_pipe, l_pipe in zip(upper_pipes, lower_pipes):
            SCREEN.blit(IMAGES['pipe'][0], (u_pipe['x'], u_pipe['y']))
            SCREEN.blit(IMAGES['pipe'][1], (l_pipe['x'], l_pipe['y']))

        SCREEN.blit(IMAGES['base'], (base_x, BASE))
        show_score(score, IMAGES, WINDOW_WIDTH, WINDOW_HEIGHT)

        # bird rotation has a threshold
        visible_rotate = bird_rotate_threshold
        if bird_rotate <= bird_rotate_threshold:
            visible_rotate = bird_rotate

        bird_surface = pygame.transform.rotate(IMAGES['bird'][bird_index], visible_rotate)
        SCREEN.blit(bird_surface, (bird_x, bird_y))

        pygame.display.update()

        # Update the Q table values using exp list and pipe crash
        if crash_check[0]:
            bird.update_Q_table(bird_tuple, not crash_check[1], score)
            sum_score = print_training_log(score, time_start, EPISODES, sum_score)
            return sum_score

        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                bird.saveQ()
                pygame.quit()
                sys.exit()



main()
