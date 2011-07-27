#!/usr/bin/env python
# -*- coding: utf-8  -*-
'''
Globals variables and helper functions for the ATC game.

Typical usage: "from globals import *"
'''

#import  modules_names_here

__author__ = "Mac Ryan"
__copyright__ = "Copyright 2011, Mac Ryan"
#__credits__ = ["Name Lastname", "Name Lastname"]
__license__ = "GPL v3"
#__version__ = "1.0.0"
__maintainer__ = "Mac Ryan"
__email__ = "quasipedia@gmail.com"
__status__ = "Development"


PING_PERIOD = 3                 # seconds between radar pings
WINDOW_SIZE = (1024, 768)       # in pixel
SCALE_FACTOR = 200.0            # metres per pixel
WHITE = (255,255,255)
BLACK = (0,0,0)
RED = (255,0,0)
TRAIL_LENGTH = 20               # number of ghost radar signal in the trail
MAX_FRAMERATE = 200
PLANE_STATES_NUM = 5            # number fo possible states for a plane

SPRITE_SCALING = 0.1            # the scaling factor for sprites

# Aeroplane states
CONTROLLED = 0
INSTRUCTED = 1
NON_CONTROLLED = 2
PRIORITIZED = 3
COLLISION = 4


def sc(vector):
    '''
    Return a version of a 2-elements iterable (coordinates) suitable for
    screen representation. That means:
    - Scaled (to window resulution)
    - Translated (to below x axis)
    - With the y sign reversed (y are positive under x, on screen)
    '''
    x, y = [int(round(c/SCALE_FACTOR)) for c in vector]
    return (x, -(y-WINDOW_SIZE[1]))

def center_blit_position(img, pos):
    '''
    Return the coordinates where 'img' should be blit if 'pos' needs to be its
    centre.
    '''
    return [a - b for a, b in zip(pos, img.get_rect().center)]