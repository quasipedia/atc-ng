#!/usr/bin/env python
# -*- coding: utf-8  -*-
'''
Provides the game logic for the ATC game.

Amongst others:
    - manage the appearance / disappearance of planes on the world
    - keep track of score
    - invokes AI support for planes in emergency
'''

from locals import *
import aerospace

__author__ = "Mac Ryan"
__copyright__ = "Copyright 2011, Mac Ryan"
#__credits__ = ["Name Lastname", "Name Lastname"]
__license__ = "GPL v3"
#__version__ = "1.0.0"
__maintainer__ = "Mac Ryan"
__email__ = "quasipedia@gmail.com"
__status__ = "Development"


class GameLogic(object):

    '''
    Docstring.
    '''

    def __init__(self, surface):
        self.global_surface = surface
        self.radar_surface = surface.subsurface(RADAR_RECT)
        self.aerospace = aerospace.Aerospace(self.radar_surface)
        self.ms_from_last_ping = 0
        self.__quick_start()

    def __quick_start(self):
        for i in range(100):
            self.aerospace.add_plane()

    def update(self, milliseconds):
        self.ms_from_last_ping += milliseconds
        if self.ms_from_last_ping > PING_PERIOD:
            pings = self.ms_from_last_ping / PING_PERIOD
            self.ms_from_last_ping %= PING_PERIOD
            self.aerospace.update(pings)

    def draw(self):
        self.aerospace.draw()


