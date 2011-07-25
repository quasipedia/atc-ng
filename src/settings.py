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


PING_PERIOD = 3                # seconds between radar pings
WINDOW_SIZE = (1024, 768)      # in pixel
SCALE_FACTOR = 200.0           # metres per pixel
WHITE = (255,255,255)
BLACK = (0,0,0)
RED = (255,0,0)
TRAIL_LENGTH = 20              # number of ghost radar signal in the trail
MAX_FRAMERATE = 200
SPRITE_RADIUS = 7

def sc(vector):
    '''
    Return a scaled version of the tuple-representation of the vector.
    '''
    return tuple([int(round(c/SCALE_FACTOR)) for c in vector])
