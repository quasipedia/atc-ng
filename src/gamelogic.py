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
import pygame.draw
import aerospace
import commander

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
        self.cli_surface = surface.subsurface(CLI_RECT)
        x, y, w, h = RADAR_RECT
        pygame.draw.line(surface, WHITE, (x-1, y), (x-1, WINDOW_SIZE[1]))
        pygame.draw.line(surface, WHITE, (x+w+1, y), (x+w+1, WINDOW_SIZE[1]))
        pygame.draw.line(surface, WHITE, (x-1, y+h+1), (x+w+1, y+h+1))
        self.aerospace = aerospace.Aerospace(self.radar_surface)
        self.cli = commander.CommandLine(self.cli_surface)
        self.ms_from_last_ping = 0
        self.__quick_start()

    def __quick_start(self):
        for i in range(10):
            self.aerospace.add_plane()

    def key_pressed(self, key):
        self.cli.process_keystroke(key)

    def update(self, milliseconds):
        self.ms_from_last_ping += milliseconds
        if self.ms_from_last_ping > PING_PERIOD:
            pings = self.ms_from_last_ping / PING_PERIOD
            self.ms_from_last_ping %= PING_PERIOD
            self.aerospace.update(pings)

    def draw(self):
        self.aerospace.draw()
        self.cli.draw()


