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
from euclid import Vector3
import pygame.draw
import pygame.sprite
import aerospace
import commander
import guisprites

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
        self.strips_surface = surface.subsurface(STRIPS_RECT)
        x, y, w, h = RADAR_RECT
        pygame.draw.line(surface, WHITE, (x-1, y), (x-1, WINDOW_SIZE[1]))
        pygame.draw.line(surface, WHITE, (x+w+1, y), (x+w+1, WINDOW_SIZE[1]))
        pygame.draw.line(surface, WHITE, (x-1, y+h+1), (x+w+1, y+h+1))
        self.aerospace = aerospace.Aerospace(self.radar_surface)
        self.cli = commander.CommandLine(self.cli_surface, self.aerospace)
        self.ms_from_last_ping = PING_PERIOD+1  #force update on first run
        self.strips = guisprites.StripsGroup()
        self.__quick_start()

    def __quick_start(self):
        d = RADAR_RANGE/9
        self.aerospace.add_plane(position=Vector3(RADAR_RANGE-d,RADAR_RANGE),
                                 velocity=Vector3(170,0,0))
        self.aerospace.add_plane(position=Vector3(RADAR_RANGE+d,RADAR_RANGE),
                                 velocity=Vector3(-70,0,0))
        self.aerospace.add_plane(position=Vector3(RADAR_RANGE,RADAR_RANGE-d),
                                 velocity=Vector3(0,370,0))
        self.aerospace.add_plane(position=Vector3(RADAR_RANGE,RADAR_RANGE+d),
                                 velocity=Vector3(0,-290,0))
        for plane in self.aerospace.aeroplanes:
            self.strips.add(guisprites.FlightStrip(plane))

    def key_pressed(self, key):
        self.cli.process_keystroke(key)

    def update(self, milliseconds):
        self.ms_from_last_ping += milliseconds
        if self.ms_from_last_ping > PING_PERIOD:
            pings = self.ms_from_last_ping / PING_PERIOD
            self.ms_from_last_ping %= PING_PERIOD
            self.aerospace.update(pings)
        self.strips.draw(self.strips_surface)

    def draw(self):
        self.aerospace.draw()
        self.cli.draw()


