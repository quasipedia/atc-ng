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


# State-machine constants
MS_QUIT   = 0
MS_RUN    = 1
MS_PAUSED = 2

# Timing
PING_PERIOD = 3000              # milliseconds between radar pings
MAX_FRAMERATE = 60              # FPS

# Dimensions
#WINDOW_SIZE = (1024, 768)       # in pixels
#WINDOW_SIZE = (800, 500)       # in pixels
WINDOW_SIZE = (1200, 750)       # in pixels
#WINDOW_SIZE = (1800, 1125)      # in pixels
RADAR_RANGE = 40000             # radius in kilometres --> 80x80km = space
RADAR_RING_STEP = 10000         # space between radar rings

# Console
CONSOLE_HEIGHT = 0.14           # as a percentage of windows height
CONSOLE_LINES_NUM = 5
CONSOLE_FONT_SIZE_RATIO = 0.60  # as a percentage of CLI
VALID_CHARS = \
    'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890./ '
OUTBOUND_ID = 'TOWER'
PROMPT_SEPARATOR = '>>>'

# Game logic
OUTBOUND = 0
INBOUND = 1
VERTICAL_CLEARANCE = 500        # minimum distance in metres between planes
HORIZONTAL_CLEARANCE = 5000     # minimum distance in metres between planes

# Colours
WHITE = (255,255,255)
GRAY = (128,128,128)
DARK_GRAY = (50,50,50)
MAGENTA = (255,0,255)
YELLOW = (255,255,0)
PALE_YELLOW = (255,255,224)
RED = (255,0,0)
DARK_RED = (150,0,0)
PALE_RED = (255,224,224)
GREEN = (0,255,0)
PALE_GREEN = (224,255,224)
DARK_GREEN = (0,150,0)
BLACK = (0,0,0)

# Sprites
TRAIL_LENGTH = 15                 # number of dots in the trail
SPRITE_SCALING = 0.1              # scaling factor (used for antialiasing)
MIN_PLANE_ICON_SIZE = 10          # minimum size of aeroplan icons in pixels
AEROPORT_MASTER_IMG_SCALING = 10  # scaling of master images for aeroports

# Aeroplane states and colors
PLANE_STATES_NUM = 5            # number fo possible states for a plane
CONTROLLED = 0
INSTRUCTED = 1
NON_CONTROLLED = 2
PRIORITIZED = 3
COLLISION = 4
STATUS_COLORS = [WHITE, GRAY, MAGENTA, YELLOW, RED]

# Fonts
MAIN_FONT = '../data/ex_modenine.ttf'
# These are conventional chars that have been mapped in the font file to
# match arrow up and arrow down
CHAR_UP = '^'
CHAR_DOWN = '\\'
HUD_INFO_FONT_SIZE = 12    # Font size for textual info on radar screen

# Derivative values
RADAR_RECT = pygame.rect.Rect(
     (WINDOW_SIZE[0]-WINDOW_SIZE[1]*(1-CONSOLE_HEIGHT))/2, 0,
      WINDOW_SIZE[1]*(1-CONSOLE_HEIGHT), WINDOW_SIZE[1]*(1-CONSOLE_HEIGHT))
METRES_PER_PIXELS = RADAR_RANGE*2.0/RADAR_RECT.width
CLI_RECT = pygame.rect.Rect(RADAR_RECT.x, RADAR_RECT.h+2,
                            RADAR_RECT.w, WINDOW_SIZE[1]-RADAR_RECT.h-2)
STRIPS_RECT = pygame.rect.Rect(0, 0,
                    # -2 for the lines separating BUI elements
                    (WINDOW_SIZE[0] - RADAR_RECT.w - 2) / 2, WINDOW_SIZE[1])
MAPS_RECT = pygame.rect.Rect(RADAR_RECT.x + RADAR_RECT.w + 1, 0,
        # -3 for the lines separating BUI elements
        (WINDOW_SIZE[0] - RADAR_RECT.w - STRIPS_RECT.w - 2), WINDOW_SIZE[1])

def rint(float_):
    '''
    Return the rounded integer of the float_.
    '''
    return int(round(float_))

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