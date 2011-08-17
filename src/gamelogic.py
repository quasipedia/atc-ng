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
from pygame.locals import *
import pygame.draw
import pygame.surface
import aerospace
import aeroport
import commander
import guisprites
import yamlhandlers as yh

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
        self.airline_handler = yh.AirlinesHandler()
        self.machine_state = MS_RUN
        # Surfaces
        self.global_surface = surface
        self.radar_surface = surface.subsurface(RADAR_RECT)
        self.cli_surface = surface.subsurface(CLI_RECT)
        self.strips_surface = surface.subsurface(STRIPS_RECT)
        self.strips_bkground = self.strips_surface.copy()
        self.maps_surface = surface.subsurface(MAPS_RECT)
        x, y, w, h = RADAR_RECT
        pygame.draw.line(surface, WHITE, (x-1, y), (x-1, WINDOW_SIZE[1]))
        pygame.draw.line(surface, WHITE, (x+w, y), (x+w, WINDOW_SIZE[1]))
        pygame.draw.line(surface, WHITE, (x-1, y+h), (x+w, y+h))
        self.aerospace = aerospace.Aerospace(self.radar_surface)
        self.cli = commander.CommandLine(self.cli_surface, self.aerospace,
                                         self.game_commands_processor)
        self.ms_from_last_ping = PING_PERIOD+1  #force update on first run
        self.strips = guisprites.StripsGroup()
        self.maps = []
        self.parse_scenario()
        self.set_challenge()

    def __add_aeroport_map(self, port):
        '''
        Add an aeroport map to the map collection.
        '''
        margin = 7
        a_map = pygame.surface.Surface((MAPS_RECT.w, MAPS_RECT.h), SRCALPHA)
        # Prepare the label and get its size
        fontobj = pygame.font.Font(MAIN_FONT, margin*2)
        text = '%s ] %s' % (port.iata, port.name)
        ellipsis = ''
        while True:
            label = fontobj.render(text+ellipsis, True, WHITE)
            w, h = label.get_width(), label.get_height()
            if w < MAPS_RECT.w - 2*margin:
                break
            text = text[:-1]
            ellipsis = '...'
        # Blit frame
        r = pygame.rect.Rect(1,1,MAPS_RECT.w-2,MAPS_RECT.w+2*margin+h-2)
        pygame.draw.rect(a_map, WHITE, r, 1)
        # Blit Banner for highlighting the label
        r = pygame.rect.Rect(2,2,MAPS_RECT.w-4,2*margin+h)
        pygame.draw.rect(a_map, GRAY, r)
        # Blit label
        a_map.blit(label, (margin, margin+2))
        # Blit map
        a_map.blit(port.get_image(square_side=MAPS_RECT.w-4*margin,
                   with_labels=True), (2*margin,4*margin+h))
        a_map = a_map.subsurface(a_map.get_bounding_rect()).copy()
        self.maps.append(a_map)

    def parse_scenario(self, fname=None):
        '''
        Parse and render a scenario.
        '''
        if fname == None:
            fname = 'default'
        scene = yh.ScenarioHandler(fname)
        scene.adjust_settings()
        # AEROPORTS
        for port in scene.aeroports:
            self.aerospace.add_aeroport(port)
            self.__add_aeroport_map(port)
            port.del_cached_images()
        self.draw_maps()
        # GATES
        for gate in scene.gates:
            self.aerospace.add_gate(gate)
        # BEACONS
        for beacon in scene.beacons:
            self.aerospace.add_beacon(beacon)
        # Update the background of the aerospace
        self.aerospace.bkground = self.aerospace.surface.copy()

    def set_challenge(self):
        '''
        Start the challenge (place planes on the radar).
        '''
        d = RADAR_RANGE/9
        rfn = self.airline_handler.random_flight
        self.aerospace.add_plane(position=Vector3(RADAR_RANGE-d,RADAR_RANGE),
                                 velocity=Vector3(170,0,0),
                                 origin='ARN', destination='FRA', **rfn())
        self.aerospace.add_plane(position=Vector3(RADAR_RANGE+d,RADAR_RANGE),
                                 velocity=Vector3(-70,0,0),
                                 origin='ARN', destination='ARN', **rfn())
        self.aerospace.add_plane(position=Vector3(RADAR_RANGE,RADAR_RANGE-d),
                                 velocity=Vector3(0,370,0),
                                 origin='ARN', destination='EX1', **rfn())
        self.aerospace.add_plane(position=Vector3(RADAR_RANGE,RADAR_RANGE+d),
                                 velocity=Vector3(0,-290,0),
                                 origin='ARN', destination='EX2', **rfn())
        for plane in self.aerospace.aeroplanes:
            status = INBOUND if plane.destination in \
                     self.aerospace.aeroports.keys() else OUTBOUND
            self.strips.add(guisprites.FlightStrip(plane, status))

    def draw_maps(self):
        '''
        Draw the maps in the map collection in the map column (right side).
        '''
        x = y = 1
        for map_ in self.maps:
            self.maps_surface.blit(map_, (x, y))
            y += map_.get_height()+1

    def game_commands_processor(self, command):
        '''
        Execute a game command.
        '''
        cname, args = command
        if cname == 'quit':
            self.machine_state = MS_QUIT

    def key_pressed(self, key):
        self.cli.process_keystroke(key)

    def update(self, milliseconds):
        self.ms_from_last_ping += milliseconds
        if self.ms_from_last_ping > PING_PERIOD:
            pings = self.ms_from_last_ping / PING_PERIOD
            self.ms_from_last_ping %= PING_PERIOD
            self.aerospace.update(pings)
        self.strips.update()
        self.strips.clear(self.strips_surface, self.strips_bkground)
        self.strips.draw(self.strips_surface)

    def draw(self):
        self.aerospace.draw()
        self.cli.draw()


