#!/usr/bin/env python
# -*- coding: utf-8  -*-
'''
Testing suite for the Lander class.
'''

import pygame
pygame.init()
pygame.display.set_mode((64,48))

import unittest
import entities.aeroplane
import entities.pilot
import entities.airport
import engine.aerospace
import engine.commander
from lib.euclid import Vector3
from lib.utils import *

__author__ = "Mac Ryan"
__copyright__ = "Copyright 2011, Mac Ryan"
#__credits__ = ["Name Lastname", "Name Lastname"]
__license__ = "GPL v3"
#__version__ = "1.0.0"
__maintainer__ = "Mac Ryan"
__email__ = "quasipedia@gmail.com"
__status__ = "Development"

# Mock classes to allow creation of Aeroplanes that do not throw exceptions.
class MockGameLogic(object):
    def __init__(self):
        self.last_said = ''
    def score_event(self, *args, **kwargs):
        pass
    def remove_plane(self, *args, **kwargs):
        pass
    def say(self, *args, **kwargs):
        if args[0].lower().find('abort'):
            self.last_said = args[1].lower()

class LanderTest(unittest.TestCase):

    '''
    Series of tests to verify the proper working of the Lander() class, an
    helper class for the landing phase of the aeroplanes.
    '''

    def setUp(self):
        plane_kwargs = {'icao' : 'ABC1234',
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
        strip_kwargs = {'orientation' : 0,
                        'length'      : 4000,
                        'width'       : 60,
                        'centre_pos'  : [0,0]}
        port_kwargs = {'location' : (20000, 20000),
                       'iata' : 'ABC',
                       'name' : 'Test airport',
                       'geolocation' : ['',''],
                       'elevation' : 0}
        surface = pygame.surface.Surface((64, 48))
        gamelogic = MockGameLogic()
        aerospace = engine.aerospace.Aerospace(gamelogic, surface)
        strip = entities.airport.AsphaltStrip(**strip_kwargs)
        a_port = entities.airport.airport(strips=[strip], **port_kwargs)
        aerospace.add_airport(a_port)
        entities.pilot.Pilot.set_aerospace(aerospace)
        self.plane = entities.aeroplane.Aeroplane(aerospace, **plane_kwargs)
        self.pilot = self.plane.pilot
        self.gamelogic = gamelogic

    def testEarlyAbortParallel(self):
        '''
        Test an early abortion if the ILS is parallel to plane direction.
        '''
        self.plane.position = Vector3(19000, 0, 0)
        self.plane.velocity = Vector3(0, 500 / 3.6, 0)
        self.pilot.set_target_conf_to_current()
        self.pilot.land('ABC', '36')
        msg = self.gamelogic.last_said
        self.assertGreater(msg.find('abort'), -1)
        print 'PARALLEL: %s' % self.gamelogic.last_said

    def testEarlyAbortOverSixty(self):
        '''
        Test an early abortion if the ILS is over 60° from plane course.
        '''
        self.plane.position = Vector3(10000, 10000, 0)
        self.plane.velocity = Vector3(500 / 3.6, 0, 0)
        self.pilot.set_target_conf_to_current()
        self.pilot.land('ABC', '36')
        msg = self.gamelogic.last_said
        self.assertGreater(msg.find('abort'), -1)
        print 'OVER 60°: %s' % self.gamelogic.last_said

    def testEarlyAbortNoCrossing(self):
        '''
        Test an early abortion if the ILS does not cross flight path.
        '''
        self.plane.position = Vector3(21000, 10000, 0)
        self.plane.velocity = Vector3(200/3.6, 200/3.6, 0)
        self.pilot.set_target_conf_to_current()
        self.pilot.land('ABC', '36')
        msg = self.gamelogic.last_said
        self.assertGreater(msg.find('abort'), -1)
        print 'NO CROSSING: %s' % self.gamelogic.last_said

    def testEarlyAbortTooClose(self):
        '''
        Test an early abortion if the ILS is too close to merge into it.
        '''
        self.plane.position = Vector3(18000, 10000, 0)
        self.plane.velocity = Vector3(800/3.6, 800/3.6, 0)
        self.pilot.set_target_conf_to_current()
        self.pilot.land('ABC', '36')
        msg = self.gamelogic.last_said
        self.assertGreater(msg.find('abort'), -1)
        print 'TOO CLOSE: %s' % self.gamelogic.last_said

    def testNoAbortOverlapping(self):
        '''
        An overlapping ILS must not trigger an abortion.
        '''
        self.plane.position = Vector3(20000, 0, 0)
        self.plane.velocity = Vector3(0, 500 / 3.6, 0)
        self.pilot.set_target_conf_to_current()
        self.pilot.land('ABC', '36')
        self.assertFalse(self.gamelogic.last_said)

    def testLateAbortTooHigh(self):
        '''
        Test abortion if the plane is flying too high to lose altitude quick
        enough to intercept the ILS.
        '''
        self.plane.position = Vector3(18000, 16000, 10000)
        self.plane.velocity = Vector3(200/3.6, 200/3.6, 0)
        self.pilot.set_target_conf_to_current()
        self.pilot.land('ABC', '36')
        for i in range(500):
            self.pilot.update()
        msg = self.gamelogic.last_said
        self.assertGreater(msg.find('abort'), -1)
        print 'TOO HIGH: %s' % self.gamelogic.last_said

    def testLateAbortTooFast(self):
        '''
        Test abortion if the plane is flying too fast to slow down to landing
        speed.
        '''
        self.plane.position = Vector3(16000, 14000, 100)
        self.plane.velocity = Vector3(600/3.6, 600/3.6, 0)
        self.pilot.set_target_conf_to_current()
        self.pilot.land('ABC', '36')
        for i in range(500):
            self.pilot.update()
        msg = self.gamelogic.last_said
        self.assertGreater(msg.find('abort'), -1)
        print 'TOO FAST: %s' % self.gamelogic.last_said


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()