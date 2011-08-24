#!/usr/bin/env python
# -*- coding: utf-8  -*-
'''
World modelling and representation for the ATC game.

- Manage the association between aeroplanes models and their sprites.
- Represent the radar.
'''

from settings import *
from itertools import combinations
from lib.euclid import Vector3
import pygame.sprite
import pygame.surface
import entities.aeroplane
import entities.aeroport
import sprites.radarsprites

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
        centre = sc((RADAR_RANGE, RADAR_RANGE))
        for radius in range(RADAR_RING_STEP, rint(RADAR_RANGE*2**0.5),
                            RADAR_RING_STEP):
            radius /= METRES_PER_PIXELS
            pygame.draw.circle(self.surface,DARK_GRAY,centre,rint(radius),1)
        self.flying_sprites = pygame.sprite.LayeredUpdates()
        self.top_layer = pygame.sprite.Group()
        self.tags = pygame.sprite.Group()
        self.__planes = {}
        self.__aeroports = {}
        self.collide_func = pygame.sprite.collide_rect_ratio(1.6)

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
        plane = entities.aeroplane.Aeroplane(**kwargs)
        record['plane'] = plane
        record['sprites'] = []
        # Icon sprite
        icon = sprites.radarsprites.AeroplaneIcon(plane, plane.model)
        self.flying_sprites.add(icon, layer=0)
        self.top_layer.add(icon)
        record['sprites'].append(icon)
        # Trail dots sprites
        for time_shift in range(1, TRAIL_LENGTH):
            dot = sprites.radarsprites.TrailingDot(plane, time_shift)
            self.flying_sprites.add(dot, layer=time_shift)
            record['sprites'].append(dot)
        # Plane tag
        tag = sprites.radarsprites.Tag(plane, self.surface.get_rect())
        self.flying_sprites.add(tag, layer=0)
        self.top_layer.add(tag)
        self.tags.add(tag)
        record['sprites'].append(tag)
        # Tag connector
        tag_c = sprites.radarsprites.TagConnector(tag)
        self.flying_sprites.add(tag_c, layer=0)
        record['sprites'].append(tag_c)
        # Storage of plane info in internal dictionary
        self.__planes[plane.icao] = record
        return plane

    def remove_plane(self, icao):
        '''
        Remove aeroplanes from the aerospace.
        '''
        for sprite in self.__planes[icao]['sprites']:
            sprite.kill()
        del self.__planes[icao]

    def add_aeroport(self, a_port):
        '''
        Add an aeroport to the aerospace.
        '''
        self.__aeroports[a_port.iata] = a_port
        a_image = a_port.get_image(scale=1.0/METRES_PER_PIXELS,
                                   with_labels=False)
        # Place aeroport on radar
        offset = Vector3(-a_image.get_width()/2, -a_image.get_height()/2).xy
        centre = sc(a_port.location.xy)
        pos = (centre[0]+offset[0], centre[1]+offset[1])
        for a in range(1):  #blitting multiple times increases visibility
            self.surface.blit(a_image, pos)
        # Draw IATA name
        fontobj = pygame.font.Font(MAIN_FONT, HUD_INFO_FONT_SIZE)
        label = fontobj.render(a_port.iata, True, GREEN)
        pos = centre[0]-label.get_width()/2, centre[1]-label.get_height()/2
        self.surface.blit(label, pos)

    def add_gate(self, gate):
        '''
        Add a gate to the aerospace.
        '''
        gate.draw(self.surface)

    def add_beacon(self, beacon):
        '''
        Add a gate to the aerospace.
        '''
        beacon.draw(self.surface)

    def connect_tags(self):
        '''
        Connect tags to their plane icon.
        '''
        for value in self.__planes.values():
            ppos = value['sprites'][0].position
            tpos = value['sprites'][-1].position
            pygame.draw.aaline(self.surface, WHITE, ppos, tpos)

    def place_tags(self):
        '''
        Spread plane tags so as not to overlap with other tags or planes.
        (This should guarantee it's always possible to read them).
        '''
        is_colliding = lambda tag : \
            self.__filter_self_collisions(tag,
                       pygame.sprite.spritecollide(tag, self.top_layer,
                                                   False, self.collide_func))
        angle_step = 5
        radius_step = 10
        for tag in self.tags:
            start_angle = tag.angle
            while not tag.place() or is_colliding(tag):
                tag.angle = (tag.angle + angle_step) % 360
                if tag.angle == start_angle:
                    tag.radius += radius_step
            tag.connector.update()

    def kill_escaped(self):
        '''
        Kill all sprites related to a plane that left the aerospace.
        '''
        for icao, plane in self.__planes.items():
            s = self.surface.get_rect()
            x, y = plane['sprites'][0].position
            if x < 0 or x > s.width or y < 0 or y > s.height:
                self.remove_plane(icao)

    @property
    def aeroplanes(self):
        '''
        Return a list of the planes existing in the aerospace.
        '''
        return [v['plane'] for v in self.__planes.values()]

    def get_plane_by_icao(self, icao):
        icao = icao.upper()
        return self.__planes[icao]['plane']

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

    def acas(self):
        '''
        ACAS = Airborne Collision Avoidance System. Verify if any plane is
        about to collide with another one and take appropriate counter-
        measures.
        '''
        # Reset all collision data
        for p in self.aeroplanes:
            if p.flags.collision == True:
                p.flags.collision = False
                p.colliding_planes = []
                p.set_target_conf_to_current()
        # Recalculate it
        for p1, p2 in combinations(self.aeroplanes, 2):
            distance = p1.position - p2.position
            if abs(distance.z) < VERTICAL_CLEARANCE and \
               distance.x**2 + distance.y**2 < HORIZONTAL_CLEARANCE**2:
                p1.set_aversion(p2)
                p2.set_aversion(p1)

    def update(self, pings):
        for plane in self.__planes.values():
            plane['plane'].update(pings)
        self.acas()
        self.flying_sprites.update()
        self.kill_escaped()
        self.place_tags()
        for tag in self.tags:
            tag.connector.generate()

    def draw(self):
        self.flying_sprites.clear(self.surface, self.bkground)
        self.flying_sprites.draw(self.surface)
