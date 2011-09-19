#!/usr/bin/env python
# -*- coding: utf-8  -*-
'''
Provide the logic for the playing mode of ATC-NG.
'''

import entities.yamlhandlers as ymlhand
import random
from engine.settings import *
from engine.logger import log
from entities.aeroplane import Aeroplane
from lib.euclid import Vector3
from time import time
from lib.utils import *

__author__ = "Mac Ryan"
__copyright__ = "Copyright 2011, Mac Ryan"
__license__ = "GPL v3"
#__version__ = "1.0.0"
__maintainer__ = "Mac Ryan"
__email__ = "quasipedia@gmail.com"
__status__ = "Development"

class Challenge(object):
#BUG: remove RADAR_RANGE from conf e make it load here
#TODO: Space out imports according to PEP8

    '''
    Docstring.
    '''

    PLANE_NUMBER_START = 2        # begin game with X planes
    MOD_PERIOD = 60               # modify frequency every X seconds
    FREQ_START = 120              # new plane every X seconds
    FREQ_STEP = -3                # step of frequency modification
    FREQ_LIMIT = 20               # maximum rate of new planes on screen
    MAX_PORT_PLANES = 6           # maximum number of created planes that can
                                  # be on ground simultaneously

    def __init__(self, gamelogic):
        self.gamelogic = gamelogic
        self.airline_handler = ymlhand.AirlinesHandler()
        self.model_handler = ymlhand.PlaneModelHandler()
        self.__init_scenario()
        self.__init_entry_data()
        self.fuel_per_metre = 1000/(RADAR_RANGE*11.3936)  #4 times diagonal
        # PLANE ENTRY VARIABLES
        self.plane_counter = 0
        self.frequency = self.FREQ_START
        self.last_entry = time() - self.FREQ_START + 5  #Lives 5 seconds empty
        self.last_freq_increase = time()

    def __init_scenario(self):
        '''
        Load an appropriate scenario and set all the local variables
        '''
        fname = 'default'
        self.scenario = ymlhand.ScenarioHandler(fname)
        self.flightnum_generator = self.airline_handler.random_flight
        self.model_generator = self.model_handler.random_model

    def __init_entry_data(self):
        '''
        Create the data that will be used to create aeroplanes at the right
        position on the map.
        '''
        gates_data = []
        for gate in self.scenario.gates:
            position = Vector3(*gate.location)
            velocity = heading_to_v3((gate.heading + 180)%360)
            levels = range(gate.top, gate.bottom-500, -500)
            levels = [l for l in levels if l%1000 == 500]
            gates_data.append((gate.name, position, velocity, levels))
        ports_data = []
        for port in self.scenario.airports:
            position = port.location.copy()
            position.z = -1  #-1 --> not on radar
            velocity = Vector3()
            ports_data.append((port.iata, position, velocity))
        self.__entry_data = dict(gates=gates_data, airports=ports_data)

    def __check_grounded_is_ok(self):
        '''
        Return False if there are already too many planes in airports.
        '''
        short = self.gamelogic.aerospace.aeroplanes
        on_ground = len([p for p in short if p.flags.on_ground == True])
        return True if on_ground < self.MAX_PORT_PLANES else False

    def __generate_flight_plan(self):
        '''
        Return intial position and velocity 3D vectors plus the origin and
        destination identifiers (airport or gate) for a plane. It also returns
        the initial amount of onboard fuel and the fuel_efficiency values.
        '''
        #TODO: foresee port to port and gate to gate
        #TODO: foresee a configurable ratio between ports and air
        #FIXME: consider passing gate and airport objects directly as orig/dest
        # Establish type of origin
        if self.__check_grounded_is_ok():
            options = ['gates', 'airports']
            random.shuffle(options)
            type_ = options.pop()
        else:
            type_ = 'gates'
        if type_ == 'gates':
            entry_data_gates = self.__entry_data['gates'][:]
            random.shuffle(entry_data_gates)
            # Attempt to make planes enter the aerospace without making them
            # collide with each other
            while entry_data_gates:
                orig, pos, vel, levels = entry_data_gates.pop()
                levels = levels[:]
                while levels:
                    # Prevent in-place modification on __entry_data
                    pos = pos.copy()
                    pos.z = levels.pop()
                    if not self.gamelogic.aerospace.check_proximity(pos):
                        vel = vel.copy()
                        tmp = random.choice(self.scenario.airports)
                        dest = tmp.iata
                        fuel = rint(ground_distance(pos, tmp.location)*
                                    4*self.fuel_per_metre)
                        return dict(origin=orig, position=pos, velocity=vel,
                                    destination=dest, fuel=fuel,
                                    fuel_efficiency=self.fuel_per_metre)
        elif type_ == 'airports':
            random.shuffle(self.__entry_data['airports'])
            orig, pos, vel = self.__entry_data['airports'][0]
            pos = pos.copy()
            vel = vel.copy()
            tmp = random.choice(self.scenario.gates)
            dest = tmp.name
            fuel = rint(ground_distance(pos, Vector3(*tmp.location))*
                                4*self.fuel_per_metre)
            return dict(origin=orig, position=pos, velocity=vel,
                        destination=dest, fuel=fuel,
                        fuel_efficiency=self.fuel_per_metre)
        return False

    def __add_plane(self):
        '''
        Add an aeroplane to the game.
        '''
        kwargs = {}
        # Aeroplane model and specifications
        kwargs.update(self.model_generator())
        # Flight number and callsign
        kwargs.update(self.flightnum_generator())
        # Origin and destionation. If for some reason the challenge engine
        # hasn't find a viable entry point for the challenge logic, it will
        # return False, and no aeroplane will be added to the game
        result = self.__generate_flight_plan()
        if not result:
            return
        kwargs.update(result)
        # Set the module of the velocity (until here a normalized vector)
        kwargs['velocity'] *= kwargs['max_speed']
        log.debug('About to add plane: %s' % kwargs)
        self.gamelogic.add_plane(Aeroplane(self.gamelogic.aerospace, **kwargs))
        self.plane_counter += 1

    def update(self):
        '''
        Perform actions (typically making a new aeroplane to appear) based
        on the kind of challenge.
        '''
        now = time()
        if now - self.last_entry > self.frequency:
            self.last_entry = now
            if self.plane_counter == 0:
                for i in range(self.PLANE_NUMBER_START):
                    self.__add_plane()
            else:
                self.__add_plane()
        if self.frequency != self.FREQ_LIMIT and \
           now - self.last_freq_increase > self.MOD_PERIOD:
            self.last_freq_increase = now
            self.frequency += self.FREQ_STEP
        # If there have been 3 (or more) destroyed planes, terminate the match
        if self.gamelogic.fatalities > 2:
            log.info('THREE_STRIKES_OUT: Match si over after %s planes entered'
                     % self.plane_counter)
            self.gamelogic.machine_state = MS_QUIT