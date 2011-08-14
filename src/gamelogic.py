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
import aeroport
import commander
import guisprites
import yaml

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
        self.maps_surface = surface.subsurface(MAPS_RECT)
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
        # PLANES
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
        # AEROPORTS
        pos1 = (RADAR_RANGE/2, RADAR_RANGE/2)
        pos2 = (RADAR_RANGE*1.5, RADAR_RANGE*1.5)
        for iata, pos in (('ARN',pos1), ('FRA',pos2)):
            data = yaml.load(open('../descriptions/aeroports/%s.yml' % iata))
            rws = [aeroport.AsphaltStrip(**rw) for rw in data['runways']]
            port = aeroport.Aeroport(pos,
                                     asphalt_strips=rws, **data['aeroport'])
            self.aerospace.add_aeroport(port)
            self.__add_aeroport_map(port)
            port.del_cached_images()

    def __add_aeroport_map(self, port):
        '''
        Add an aeroport map to the game screen.
        '''
        margin = 7
        # Prepare the label and get its size
        fontobj = pygame.font.Font(MAIN_FONT, margin*2)
        text = '%s ] %s' % (port.iata, port.name)
        label = fontobj.render(text, True, WHITE)
        w, h = label.get_width(), label.get_height()
        # Blit frame
        r = pygame.rect.Rect(1,1,MAPS_RECT.w-2,MAPS_RECT.w+2*margin+h-2)
        pygame.draw.rect(self.maps_surface, WHITE, r, 1)
        # Blit Banner for highlighting the name
        r = pygame.rect.Rect(2,2,MAPS_RECT.w-4,2*margin+h)
        pygame.draw.rect(self.maps_surface, GRAY, r)
        # Blit label
        self.maps_surface.blit(label, (margin, margin+2))
        # Blit map
        self.maps_surface.blit(port.get_image(square_side=MAPS_RECT.w-4*margin,
                  with_labels=True), (2*margin,4*margin+h))

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


