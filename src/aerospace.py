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

    def __filter_self_collisions(self, sprite, collisions):
        '''
        Filter the list of collisions eliminating false positive (sprite will
        always "collide" with self!).
        '''
        try:
            collisions.remove(sprite)
        except ValueError:
            pass
        return collisions

    def add_plane(self, **kwargs):
        '''
        Add aeroplanes to the aerospace.
        '''
        # This record will contain all info relative to a given plane
        record = {}
        # Aeroplane object
        plane = aeroplane.Aeroplane()
        record['plane'] = plane
        record['sprites'] = []
        # Icon sprite
        icon = radarsprites.AeroplaneIcon(plane, plane.model)
        self.flying_sprites.add(icon, layer=0)
        self.top_layer.add(icon)
        record['sprites'].append(icon)
        # Trail dots sprites
        for time_shift in range(1, TRAIL_LENGTH):
            dot = radarsprites.TrailingDot(plane, time_shift)
            self.flying_sprites.add(dot, layer=time_shift)
            record['sprites'].append(dot)
        # Plane tag
        tag = radarsprites.Tag(plane, self.surface.get_rect())
        self.flying_sprites.add(tag, layer=0)
        self.top_layer.add(tag)
        self.tags.add(tag)
        record['sprites'].append(tag)
        # Storage of plane info in internal dictionary
        self.__planes[plane.icao] = record

    def remove_plane(self, icao):
        '''
        Remove aeroplanes from the aerospace.
        '''
        for sprite in self.__planes[icao]['sprites']:
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
            self.__filter_self_collisions(k, v)
            if not v:
                del collisions[k]
        is_colliding = lambda tag : \
            self.__filter_self_collisions(tag,
                       pygame.sprite.spritecollide(tag, self.top_layer, False))
        for tag in collisions.keys():
            # Since "A collides with B" also means "B collides with A", solving
            # the first means solving the second, so we need to re-check for
            # collisions at the beginning of each iteration.
            start_angle = tag.angle
            angle_step = 5
            radius_step = 10
            while is_colliding(tag):
                tag.angle = (tag.angle + angle_step) % 360
                if tag.angle == start_angle:
                    tag.radius += radius_step
                tag.place()

    def kill_escaped(self):
        '''
        Kill all sprites related to a plane that left the aerospace.
        '''
        for icao, plane in self.__planes.items():
            s = self.surface.get_rect()
            x, y = plane['sprites'][0].position
            if x < 0 or x > s.width or y < 0 or y > s.height:
                self.remove_plane(icao)

    def update(self, pings):
        for plane in self.__planes.values():
            plane['plane'].update(pings)
        self.flying_sprites.update()
        self.kill_escaped()
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



