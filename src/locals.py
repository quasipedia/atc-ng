#!/usr/bin/env python
# -*- coding: utf-8  -*-
'''
Globals variables and helper functions for the ATC game.

Typical usage: "from globals import *"
'''

import pygame.rect

__author__ = "Mac Ryan"
__copyright__ = "Copyright 2011, Mac Ryan"
#__credits__ = ["Name Lastname", "Name Lastname"]
__license__ = "GPL v3"
#__version__ = "1.0.0"
__maintainer__ = "Mac Ryan"
__email__ = "quasipedia@gmail.com"
__status__ = "Development"


# Timing
PING_PERIOD = 1000              # milliseconds between radar pings
MAX_FRAMERATE = 60              # FPS

# Dimensions
#WINDOW_SIZE = (1024, 768)       # in pixels
WINDOW_SIZE = (1200, 750)       # in pixels
CLI_HEIGHT = 0.07               # as a percentage of windows height
RADAR_RANGE = 40000             # radius in kilometres --> 80x80km = space

# Colours
WHITE = (255,255,255)
BLACK = (0,0,0)
RED = (255,0,0)

# Sprites
TRAIL_LENGTH = 15               # number of dots in the trail
SPRITE_SCALING = 0.1            # scaling factor (used for antialiasing)

# Aeroplane states
PLANE_STATES_NUM = 5            # number fo possible states for a plane
CONTROLLED = 0
INSTRUCTED = 1
NON_CONTROLLED = 2
PRIORITIZED = 3
COLLISION = 4

# Commandline
VALID_CHARS = \
    'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890./ '

# Fonts
# These are conventional chars that have been mapped in the font file to
# match arrow up and arrow down
CHAR_UP = '^'
CHAR_DOWN = '\\'
HUD_INFO_FONT_SIZE = 12

# Derivative values
RADAR_RECT = pygame.rect.Rect(
             (WINDOW_SIZE[0]-WINDOW_SIZE[1]*(1-CLI_HEIGHT))/2, 0,
              WINDOW_SIZE[1]*(1-CLI_HEIGHT), WINDOW_SIZE[1]*(1-CLI_HEIGHT))
METRES_PER_PIXELS = RADAR_RANGE*2.0/RADAR_RECT.width

CLI_RECT = pygame.rect.Rect(RADAR_RECT.x, RADAR_RECT.h+2,
                            RADAR_RECT.w, WINDOW_SIZE[1]-RADAR_RECT.h-2)
FONT_HEIGHT = int(round(CLI_RECT.h * 0.8))

def sc(vector):
    '''
    Return a version of a 2-elements iterable (coordinates) suitable for
    screen representation. That means:
    - Scaled (to window resolution)
    - Translated (to below x axis)
    - With the y sign reversed (y are positive under x, on screen)
    '''
    x, y = [int(round(c/METRES_PER_PIXELS)) for c in vector]
    return (x, -(y-RADAR_RECT.height))

def get_rect_at_centered_pos(img, pos):
    '''
    Return the rect based on where 'img' should be blit if 'pos' needs to be
    its centre.
    '''
    rect = img.get_rect()
    pos = [a - b for a, b in zip(pos, img.get_rect().center)]
    rect.x, rect.y = pos
    return rect