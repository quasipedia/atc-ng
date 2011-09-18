#!/usr/bin/env python
# -*- coding: utf-8  -*-
'''
World modelling and representation for the ATC game.

- Manage the association between aeroplanes models and their sprites.
- Represent the radar.
'''

from engine.settings import *
from lib.utils import *
from itertools import combinations
from lib.euclid import Vector3
import pygame.sprite
import entities.aeroplane
import sprites.radarsprites

__author__ = "Mac Ryan"
__copyright__ = "Copyright 2011, Mac Ryan"
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

    def __init__(self, gamelogic, surface):
        self.gamelogic = gamelogic
        self.surface = surface
        self.__draw_radar_aid()
        self.flying_sprites = pygame.sprite.LayeredUpdates()
        self.top_layer = pygame.sprite.Group()
        self.tags = pygame.sprite.Group()
        self.__planes = {}
        self.__airports = {}
        self.__beacons = {}
        self.__gates = {}
        self.tcas_data = {}
        entities.pilot.Pilot.set_aerospace(self)

    def __draw_radar_aid(self):
        '''
        Draw the radar aid.
        '''
        if not RADAR_AID:
            return
        centre = sc((RADAR_RANGE, RADAR_RANGE))
        # Find how many metres a step consist of, making sure the final value
        # is sensible (not 12735.5, for example...)
        sensibles = [n*1000 for n in (1, 5, 10, 20, 25, 50, 100)]
        attempts = [RADAR_RANGE*2/n for n in sensibles]
        closest = min(attempts, key = lambda x : abs(x-RADAR_AID_STEPS))
        metres_per_step = sensibles[attempts.index(closest)]
        if RADAR_AID == 'circles':
            step_range = range(metres_per_step, rint(RADAR_RANGE*2**0.5),
                               metres_per_step)
            for radius in step_range:
                pygame.draw.circle(self.surface, RADAR_AID_COLOUR, centre,
                                   rint(radius/METRES_PER_PIXEL), 1)
        elif RADAR_AID in ('grid', 'crosses', 'dots'):
            # In the following line: since division is integer division, this
            # will ensure that on marking will pass from the radar position
            first = RADAR_RANGE - RADAR_RANGE/metres_per_step*metres_per_step
            step_range = range(first, RADAR_RANGE*2+metres_per_step,
                               metres_per_step)
            draw = lambda fm, to : pygame.draw.aaline(self.surface,
                                          RADAR_AID_COLOUR, sc(fm), sc(to))
            for step in step_range:
                if RADAR_AID == 'grid':
                    draw((step, 0), (step, RADAR_RANGE*2))
                    draw((0, step), (RADAR_RANGE*2, step))
                elif RADAR_AID in ('dots', 'crosses'):
                    for step2 in step_range:
                        if RADAR_AID == 'dots':
                            pygame.draw.circle(self.surface, RADAR_AID_COLOUR,
                                               sc((step, step2)), 2)
                        elif RADAR_AID == 'crosses':
                            x, y = step, step2
                            offset = metres_per_step / 10
                            draw((x-offset, y), (x+offset, y))
                            draw((x, y-offset), (x, y+offset))
        else:
                msg = 'Wrong value of `RADAR_AID` in config file!'
                raise BaseException(msg)

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

    def add_plane(self, plane):
        '''
        Add aeroplanes to the aerospace.
        '''
        # This record will contain all info relative to a given plane
        record = dict(plane = plane, sprites = [])
        # Icon sprite
        icon = sprites.radarsprites.AeroplaneIcon(plane, plane.category)
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

    def remove_plane(self, plane, event):
        '''
        Remove aeroplanes from the aerospace.
        '''
        for sprite in self.__planes[plane.icao]['sprites']:
            sprite.kill()
        del self.__planes[plane.icao]

    def add_airport(self, a_port):
        '''
        Add an airport to the aerospace.
        '''
        self.__airports[a_port.iata] = a_port
        a_image = a_port.get_image(scale=1.0/METRES_PER_PIXEL,
                                   with_labels=False)
        # Place airport on radar
        offset = Vector3(-a_image.get_width()/2, -a_image.get_height()/2).xy
        centre = sc(a_port.location.xy)
        pos = (centre[0]+offset[0], centre[1]+offset[1])
        self.surface.blit(a_image, pos)
        # Draw IATA name
        fontobj = pygame.font.Font(MAIN_FONT, HUD_INFO_FONT_SIZE)
        label = fontobj.render(a_port.iata, True, GREEN)
        pos = centre[0]-label.get_width()/2, centre[1]-label.get_height()/2
        self.surface.blit(label, pos)
        # Draw RNWY feet and PORT centre (debugging purposes)
#        for rnwy in a_port.runways.values():
#            pos1 = a_port.location + rnwy['location']
#            pos2 = a_port.location + rnwy['to_point']
#            pygame.draw.circle(self.surface, WHITE, sc(pos1.xy), 1)
#            pygame.draw.circle(self.surface, YELLOW, sc(pos2.xy), 1)
#        pygame.draw.circle(self.surface, RED, sc(a_port.location.xy), 1)

    def add_gate(self, gate):
        '''
        Add a gate to the aerospace.
        '''
        self.__gates[gate.name] = gate
        gate.draw(self.surface)

    def add_beacon(self, beacon):
        '''
        Add a gate to the aerospace.
        '''
        self.__beacons[beacon.id] = beacon
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
                           False, pygame.sprite.collide_rect_ratio(1.6)))
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
                msg = 'Tower? ... Tower? ... Aaaaahhhh!'
                plane['plane'].pilot.say(msg, KO_COLOUR)
                self.gamelogic.remove_plane(plane['plane'],
                                            PLANE_LEAVES_RANDOM)

    def get_plane_by_icao(self, icao):
        icao = icao.upper()
        return self.__planes[icao]['plane']

    @property
    def aeroplanes(self):
        '''
        Return a list of the planes existing in the aerospace.
        '''
        return [v['plane'] for v in self.__planes.values()]

    @property
    def airports(self):
        '''
        Return a list of the available airports on the map.
        '''
        return self.__airports

    @property
    def gates(self):
        '''
        Return a list of the available gates on the map.
        '''
        return self.__gates

    @property
    def beacons(self):
        '''
        Return a list of the available beacons on the map.
        '''
        return self.__beacons

    def check_proximity(self, point):
        '''
        Check if a given point is near enough to another plane to trigger the
        TCAS alarm.
        '''
        for plane in self.aeroplanes:
            distance = point - plane.position
            if abs(distance.z) < VERTICAL_CLEARANCE and \
               distance.x**2 + distance.y**2 < HORIZONTAL_CLEARANCE**2:
                return True
        return False

    def set_tcas_data(self):
        '''
        TCAS = Traffic Collision Avoidance System. Set the data that will be
        queried by individual TCAS onboard each plane.
        '''
        data = {}
        # Filter out aeroplanes that are on ground
        planes = [p for p in self.aeroplanes if p.position.z > 0]
        for p1, p2 in combinations(planes, 2):
            distance = p1.position - p2.position
            if abs(distance.z) < VERTICAL_CLEARANCE and \
               distance.x**2 + distance.y**2 < HORIZONTAL_CLEARANCE**2:
                try:
                    data[p1.icao].append(p2)
                except KeyError:
                    data[p1.icao] = [p2]
                try:
                    data[p2.icao].append(p1)
                except KeyError:
                    data[p2.icao] = [p1]
        self.tcas_data = data

    def update(self, pings):
        for plane in self.__planes.values():
            plane['plane'].update(pings)
        self.set_tcas_data()
        self.flying_sprites.update()
        self.kill_escaped()
        self.place_tags()
        for tag in self.tags:
            tag.connector.generate()

    def draw(self):
        self.flying_sprites.clear(self.surface, self.bkground)
        self.flying_sprites.draw(self.surface)
