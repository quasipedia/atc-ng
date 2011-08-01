#!/usr/bin/env python
# -*- coding: utf-8  -*-
'''
World modelling and representation for the ATC game.

- Manage the association between aeroplanes models and their sprites.
- Represent the radar.
'''

from locals import *
import pygame.sprite
import pygame.surface
import aeroplane
import aeroport
import radarsprites

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

    def __init__(self, surface):
        self.surface = surface
        self.bkground = pygame.surface.Surface((RADAR_RECT.w, RADAR_RECT.h))
        self.flying_sprites = pygame.sprite.LayeredUpdates()
        self.top_layer = pygame.sprite.Group()
        self.tags = pygame.sprite.Group()
        self.__planes = {}
        self.__aeroports = {}

    def add_plane(self, **kwargs):
        '''
        Add aeroplanes to the aerospace.
        '''
        record = []
        plane = aeroplane.Aeroplane()
        record.append(plane)
        icon = radarsprites.AeroplaneIcon(plane, plane.model)
        self.flying_sprites.add(icon, layer=0)
        self.top_layer.add(icon)
        record.append(icon)
        for time_shift in range(1, TRAIL_LENGTH):
            dot = radarsprites.TrailingDot(plane, time_shift)
            self.flying_sprites.add(dot, layer=time_shift)
            record.append(dot)
        tag = radarsprites.Tag(plane)
        record.append(tag)
        self.flying_sprites.add(tag, layer=0)
        self.top_layer.add(tag)
        self.tags.add(tag)
        self.__planes[plane.icao] = tuple(record)

    def remove_plane(self, icao):
        '''
        Remove aeroplanes from the aerospace.
        '''
        for sprite in self.__planes[icao][1:]:
            sprite.kill()
        del self.__planes[icao]

    def add_aeroport(self, iata, runaways):
        '''
        Add aeroports to the aerospace.
        There is no need for a `remove` function
        '''
        self.__aeroports[iata] = aeroport.Aeroport(iata, runaways)

    def untangle_tags(self):
        '''
        Spread plane tags so as not to overlap with other tags or planes.
        (This should guarantee it's always possible to read them).
        '''
        collisions = pygame.sprite.groupcollide(self.tags, self.top_layer,
                                                False, False)
        for k,v in collisions.items():
            # Remove self-collision
            if [k] == v:
                del collisions[k]
            else:
                v.remove(k)
        print(collisions)

    def update(self, pings):
        for record in self.__planes.values():
            record[0].update(pings)
        self.flying_sprites.update()
        self.untangle_tags()

    def draw(self):
        self.flying_sprites.clear(self.surface, self.bkground)
        self.flying_sprites.draw(self.surface)

    def ping(self):
        '''
        Execute a ping of the radar.
        '''
        pass

    @property
    def aeroports(self):
        '''
        Return a list of the available airports on the map.
        '''
        return self.__aeroports

    @property
    def beacons(self):
        '''
        Return a list of the available airports on the map.
        '''
        return []



