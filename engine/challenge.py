#!/usr/bin/env python
# -*- coding: utf-8  -*-
'''
Provide the logic for the playing mode of ATC-NG.
'''

#TODO: Convert to plugin-based challenges (time based, one against other, etc)

from engine.settings import *
from entities.aeroplane import Aeroplane
from lib.euclid import Vector3
from time import time
import entities.yamlhandlers as ymlhand
from lib.utils import *

__author__ = "Mac Ryan"
__copyright__ = "Copyright 2011, Mac Ryan"
#__credits__ = ["Name Lastname", "Name Lastname"]
__license__ = "GPL v3"
#__version__ = "1.0.0"
__maintainer__ = "Mac Ryan"
__email__ = "quasipedia@gmail.com"
__status__ = "Development"

class Challenge(object):

    '''
    Docstring.
    '''

    def __init__(self, gamelogic):
        self.gamelogic = gamelogic
        self.airline_handler = ymlhand.AirlinesHandler()
        self.model_handler = ymlhand.PlaneModelHandler()
        self.__init_scenario()
        self.__init_entry_data()
        self.ref_time = time() - 57  #Lives 3 seconds before first plane
        self.simultaneous_planes = 0
        self.max_fuel_in_metres = RADAR_RANGE*11.3936  #4 times diagonal

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
            position = Vector3(*gate.location, z=5000)  #5000 mt asl
            velocity = heading_to_v3((gate.heading + 180)%360)
            gates_data.append((gate.name, position, velocity))
        ports_data = []
        for port in self.scenario.aeroports:
            position = port.location.copy()
            position.z = -1  #-1 --> not on radar
            velocity = Vector3()
            ports_data.append((port.iata, position, velocity))
        self.__entry_data = dict(gates=gates_data, aeroports=ports_data)

    def __generate_flight_plan(self):
        '''
        Return intial position and velocity 3D vectors plus the origin and
        destination identifiers (aeroport or gate) for a plane. It also returns
        the initial amount of onboard fuel.
        '''
        orig, pos, vel = randelement(self.__entry_data['gates'])
        vel *= 500 / 3.6  #TODO: must match plane parameters!!!
        tmp = randelement(self.scenario.aeroports)
        dest = tmp.iata
        fuel = rint(ground_distance(pos, tmp.location)/self.max_fuel_in_metres)
        return dict(origin=orig, position=pos, velocity=vel, 
                    destination=dest, fuel=fuel)

    def __add_plane(self):
        '''
        Add an aeroplane to the game.
        '''
        kwargs = {}
        # Aeroplane model and specifications
        kwargs.update(self.model_generator())
        # Flight number and callsign
        kwargs.update(self.flightnum_generator())
        # Origin and destionation
        kwargs.update(self.__generate_flight_plan())
        self.gamelogic.add_plane(Aeroplane(self.gamelogic.aerospace, **kwargs))

    def update(self):
        '''
        Perform actions (typically making a new aeroplane to appear) based
        on the kind of challenge.
        '''
        # Every minute increase of one unit the amount of desired planes that
        # should be on radar at any time
        if time() - self.ref_time > 60:
            self.simultaneous_planes += 1
            self.ref_time = time()
        # Adjust the amount of actual planes to the desired one
        if len(self.gamelogic.aerospace.aeroplanes) < self.simultaneous_planes:
            self.__add_plane()
        # If there have been 3 (or more) destroyed planes, terminate the match
        if self.gamelogic.fatalities > 2:
            print ("Match is over!")