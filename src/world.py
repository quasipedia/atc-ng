#!/usr/bin/env python
# -*- coding: utf-8  -*-
'''
World modelling and representation for the ATC game.

- Manage the association between aeroplanes models and their sprites.
- Represent the radar.
'''

from settings import *
import pygame.sprite
import pygame.surface
import aeroplane
import flyingsprites

__author__ = "Mac Ryan"
__copyright__ = "Copyright 2011, Mac Ryan"
#__credits__ = ["Name Lastname", "Name Lastname"]
__license__ = "GPL v3"
#__version__ = "1.0.0"
__maintainer__ = "Mac Ryan"
__email__ = "quasipedia@gmail.com"
__status__ = "Development"


class Aerospace(object):

    '''
    The aerospace is the modelling part of the world.

    It is a container for the aeroplanes, and manage the intereaction between
    planes, and between ground and air (takeoffs, landings).

    The internal __planes dictionary has the following structure:
    {flight_number : (Aeroplane(), PlaneIcon(), TrailingDot() * ...}
    '''

    def __init__(self):
        self.bkground = pygame.surface.Surface(WINDOW_SIZE)
        self.sprite_group = pygame.sprite.LayeredUpdates()
        self.__planes = {}

    def add_plane(self, **kwargs):
        '''
        Add aeroplanes to the aerospace.
        '''
        record = []
        plane = aeroplane.Aeroplane()
        record.append(plane)
        icon = flyingsprites.AeroplaneIcon(plane, 'jet')
        self.sprite_group.add(icon, layer=0)
        record.append(icon)
        for time_shift in range(1, TRAIL_LENGTH):
            dot = flyingsprites.TrailingDot(plane, layer=time_shift)
            self.sprite_group.add(dot, time_shift)
            record.append(dot)
        self.__planes[plane.icao] = tuple(record)

    def remove_plane(self, icao):
        '''
        Remove aeroplanes from the aerospace.
        '''
        for sprite in self.__planes[icao][1:]:
            sprite.kill()
        del self.__planes[icao]

    def update(self):
        for record in self.__planes.values():
            record[0].update()

    def draw(self, surface):
        self.sprite_group.clear(surface, self.bkground)
        self.sprite_group.draw(surface)

    def ping(self):
        '''
        Execute a ping of the radar.
        '''
        pass
