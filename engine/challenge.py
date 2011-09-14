#!/usr/bin/env python
# -*- coding: utf-8  -*-
'''
Provide the logic for the playing mode of ATC-NG.
'''

import entities.yamlhandlers as ymlhand
import random
from engine.settings import *
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

    '''
    Docstring.
    '''

    INTERVAL = 120

    def __init__(self, gamelogic):
        self.gamelogic = gamelogic
        self.airline_handler = ymlhand.AirlinesHandler()
        self.model_handler = ymlhand.PlaneModelHandler()
        self.__init_scenario()
        self.__init_entry_data()
        self.ref_time = time() - self.INTERVAL + 5  #Lives 5 seconds empty sky
        self.simultaneous_planes = 0
        self.fuel_per_metre = 1000/(RADAR_RANGE*11.3936)  #4 times diagonal

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

    def __generate_flight_plan(self):
        '''
        Return intial position and velocity 3D vectors plus the origin and
        destination identifiers (airport or gate) for a plane. It also returns
        the initial amount of onboard fuel and the fuel_efficiency values.
        '''
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
                    found_ok = True
                    tmp = random.choice(self.scenario.airports)
                    dest = tmp.iata
                    fuel = rint(ground_distance(pos, tmp.location)*
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
        self.gamelogic.add_plane(Aeroplane(self.gamelogic.aerospace, **kwargs))

    def update(self):
        '''
        Perform actions (typically making a new aeroplane to appear) based
        on the kind of challenge.
        '''
        # Every minute increase of one unit the amount of desired planes that
        # should be on radar at any time
        if time() - self.ref_time > self.INTERVAL:
            self.simultaneous_planes += 1
            self.ref_time = time()
        # Adjust the amount of actual planes to the desired one
        if len(self.gamelogic.aerospace.aeroplanes) < self.simultaneous_planes:
            self.__add_plane()
        # If there have been 3 (or more) destroyed planes, terminate the match
        if self.gamelogic.fatalities > 2:
            print ("Match is over!")
            self.gamelogic.machine_state = MS_QUIT