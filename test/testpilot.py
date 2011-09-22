#!/usr/bin/env python
# -*- coding: utf-8  -*-
'''
Testing suite for the pilot package. Each test class corresponds (more or less
to one of the modules in the package).
'''

import unittest
import entities.aeroplane as aero
import pilot.pilot as pilo
from euclid import Vector3

__author__ = "Mac Ryan"
__copyright__ = "Copyright 2011, Mac Ryan"
__license__ = "GPL v3"
#__version__ = "<dev>"
#__date__ = "<unknown>"
__maintainer__ = "Mac Ryan"
__email__ = "quasipedia@gmail.com"
__status__ = "Development"


# MOCK CLASSES TO ALLOW CREATION OF AEROPLANES THAT DO NOT THROW EXCEPTIONS.
class MockGameLogic(object):
    def score_event(self, *args, **kwargs):
        pass
    def say(self, *args, **kwargs):
        pass
class MockAerospace(object):
    def __init__(self):
        self.tcas_data = {}
        self.gamelogic = MockGameLogic()
        self.airports = []


class PilotTest(unittest.TestCase):

    '''
    '''

    def setUp(self):
        kwargs = {'icao' : 'ABC1234',
                  'callsign' : 'CALLME PLANE',
                  'model' : 'A380',
                  'category' : 'jet',
                  'origin' : 'XXX',
                  'destination' : 'YYY',
                  'fuel_efficiency' : 1,
                  'max_altitude' : 10000,
                  'climb_rate_limits' : [-30, 15],
                  'climb_rate_accels' : [-20, 10],
                  'max_speed' : 800,
                  'ground_accels' : [-4, 6],
                  'landing_speed' : 150,
                  'max_g' : 2,
                  'position' : Vector3(),
                  'velocity' : Vector3(),
                  'fuel' : 500}
        mock_aerospace = MockAerospace()
        pilo.Pilot.set_aerospace(mock_aerospace)
        self.plane = aero.Aeroplane(mock_aerospace, **kwargs)
        self.pilot = self.plane.pilot

    def test(self):
        '''
        When pilot is talked to, it answer in it's API format.
        '''



if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()