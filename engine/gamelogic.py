#!/usr/bin/env python
# -*- coding: utf-8  -*-
'''
Provides the game logic for the ATC game.

Amongst others:
    - manage the appearance / disappearance of planes on the world
    - keep track of score
    - invokes AI support for planes in emergency
'''

from engine.settings import *
from engine.logger import log
from pygame.locals import *
import pygame.draw
import pygame.surface
import aerospace
import commander
import entities.yamlhandlers
import sprites.guisprites
import engine.challenge

__author__ = "Mac Ryan"
__copyright__ = "Copyright 2011, Mac Ryan"
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
        self.machine_state = MS_RUN
        # Surfaces
        self.global_surface = surface
        self.radar_surface = surface.subsurface(RADAR_RECT)
        self.cli_surface = surface.subsurface(CLI_RECT)
        self.strips_surface = surface.subsurface(STRIPS_RECT)
        self.score_surface = surface.subsurface(SCORE_RECT)
        self.strips_bkground = self.strips_surface.copy()
        self.maps_surface = surface.subsurface(MAPS_RECT)
        x, y, w, h = RADAR_RECT
        pygame.draw.line(surface, WHITE, (x-1, y), (x-1, WINDOW_SIZE[1]))
        pygame.draw.line(surface, WHITE, (x+w, y), (x+w, WINDOW_SIZE[1]))
        pygame.draw.line(surface, WHITE, (x-1, y+h), (x+w, y+h))
        pygame.draw.line(surface, WHITE, (SCORE_RECT.x, SCORE_RECT.y-1),
                             (SCORE_RECT.x + SCORE_RECT.w, SCORE_RECT.y-1))
        self.aerospace = aerospace.Aerospace(self, self.radar_surface)
        self.cli = commander.CommandLine(self.cli_surface, self.aerospace,
                                         self.game_commands_processor)
        self.ms_from_last_ping = PING_PERIOD+1  #force update on first run
        self.strips = sprites.guisprites.StripsGroup()
        self.maps = []
        # Scoring
        self.score = 0
        self.fatalities = 0
        # Game interface
        self.fixed_sprites = pygame.sprite.Group()
        self.fixed_sprites.add(sprites.guisprites.Score(self))
        self.challenge = engine.challenge.Challenge(self)
        self.parse_scenario(self.challenge.scenario)

    def __add_airport_map(self, port):
        '''
        Add an airport map to the map collection.
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

    def parse_scenario(self, scenario):
        '''
        Parse and render a scenario.
        '''
        # airportS
        for port in scenario.airports:
            self.aerospace.add_airport(port)
            self.__add_airport_map(port)
            port.del_cached_images()
        self.draw_maps()
        # GATES
        for gate in scenario.gates:
            self.aerospace.add_gate(gate)
        # BEACONS
        for beacon in scenario.beacons:
            self.aerospace.add_beacon(beacon)
        # Update the background of the aerospace
        self.aerospace.bkground = self.aerospace.surface.copy()

    def add_plane(self, plane):
        '''
        Add a plane from the game.
        '''
        planes = self.aerospace.aeroplanes
        ports = self.aerospace.airports
        self.aerospace.add_plane(plane)
        status = INBOUND if plane.destination in ports.keys() else OUTBOUND
        self.strips.add(sprites.guisprites.FlightStrip(plane, status))
        plane.pilot.say('Hello tower, we are ready to copy instructions!',
                        ALERT_COLOUR)
        # Only airborne planes impact on proficiency score
        if plane.position.z > 0:
            already_there = len([p for p in planes if p.position.z > 0]) - 1
            if already_there > 0:
                self.score_event(PLANE_ENTERS, multiplier=already_there)

    def remove_plane(self, plane, event):
        '''
        Remove a plane from the game.
        '''
        log.info('%s removed, event is %s' % (plane.icao, event))
        self.score_event(event, plane=plane)
        self.aerospace.remove_plane(plane, event)
        self.strips.remove_strip(plane)
        if event in (PLANE_CRASHES, PLANE_LEAVES_RANDOM):
            self.fatalities += 1

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

    def say(self, who, what, color):
        '''
        Output a message on the console.
        '''
        self.cli.say(who, what, color)

    def key_pressed(self, key):
        self.cli.process_keystroke(key)

    def score_event(self, event, plane=None, multiplier=None):
        '''
        Process an event that influence the score.
        Events are defined in the settings, other keyword arguments are passed
        according the the event.
        '''
        # The second element of an event is the amount of points
        score = event[1]
        # If it's a aeroplane end-of-life event, compute the fuel effect.
        if event in (PLANE_LANDS_CORRECT_PORT, PLANE_LANDS_WRONG_PORT,
                     PLANE_LEAVES_CORRECT_GATE, PLANE_LEAVES_WRONG_GATE,
                     PLANE_LEAVES_RANDOM, PLANE_CRASHES):
            assert plane
            fuel = plane.fuel * FUEL_SCORE_WEIGHT
            score += fuel if score > 0 else -fuel
        # if the event score needs a multiplier, use it
        elif event in (PLANE_ENTERS, PLANE_BURNS_FUEL_UNIT,
                       PLANE_WAITS_ONE_SECOND):
            assert multiplier != None
            score *= multiplier
        # otherwise... vanilla!
        else:
            assert event in (COMMAND_IS_ISSUED, EMERGENCY_FUEL, EMERGENCY_TCAS)
        self.score += score

    def update(self, milliseconds):
        self.ms_from_last_ping += milliseconds
        self.challenge.update()
        self.strips.update()
        self.strips.clear(self.strips_surface, self.strips_bkground)
        self.strips.draw(self.strips_surface)
        self.fixed_sprites.update()
        self.fixed_sprites.draw(self.score_surface)
        if self.ms_from_last_ping > PING_PERIOD:
            pings = self.ms_from_last_ping / PING_PERIOD
            self.ms_from_last_ping %= PING_PERIOD
            self.aerospace.update(pings)
            self.aerospace.draw()
        self.cli.draw()
