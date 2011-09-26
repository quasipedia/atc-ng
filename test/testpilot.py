#!/usr/bin/env python
# -*- coding: utf-8  -*-
'''
Testing suite for various miscellaneous stuff in the pilot package.
'''

import unittest
import entities.aeroplane as aero
import pilot.pilot as pilo
import engine.commander
from lib.euclid import Vector3
from lib.utils import *

__author__ = "Mac Ryan"
__copyright__ = "Copyright 2011, Mac Ryan"
__license__ = "GPL v3"
#__version__ = "<dev>"
#__date__ = "<unknown>"
__maintainer__ = "Mac Ryan"
__email__ = "quasipedia@gmail.com"
__status__ = "Development"

# Mock classes to allow creation of Aeroplanes that do not throw exceptions.
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


class CheckerTest(unittest.TestCase):

    '''
    Test the ``checker`` module of the ``pilot`` package.
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

    def testPlaneLimits(self):
        '''
        Test that orders fails if exceed plane altitude and speed
        specifications.
        '''
        # In the following tests, since the returned value is either True or
        # a string, the assertTrue statement can't be used as it would evaluate
        # a string too as boolean True.
        MIN = 100
        MAX = 1000
        a_chk = lambda a : self.pilot.checker.check(dict(ALTITUDE=[[a],[]]))
        s_chk = lambda s : self.pilot.checker.check(dict(SPEED=[[s],[]]))
        for n in range (MIN, MAX, 10):
            # UPPER ALTITUDE LIMIT
            self.plane.max_altitude = n
            self.assertEqual(True, a_chk(n))
            self.assertEqual(True, a_chk(n-1))
            self.assertNotEqual(True, a_chk(n+1))
            # UPPER SPEED LIMIT
            self.plane.min_speed = (MIN-10) / 3.6  #convert kph to m/s
            self.plane.max_speed = n / 3.6  #convert kph to m/s
            self.assertEqual(True, s_chk(n/3.6))
            self.assertEqual(True, s_chk((n-1)/3.6))
            self.assertNotEqual(True, s_chk((n+1)/3.6))
            # LOWER SPEED LIMIT
            self.plane.max_speed = (MAX+10) / 3.6  #convert kph to m/s
            self.plane.min_speed = n / 3.6  #convert kph to m/s
            self.assertEqual(True, s_chk(n/3.6))
            self.assertNotEqual(True, s_chk((n-1)/3.6))
            self.assertEqual(True, s_chk((n+1)/3.6))


class MiscellaneousTest(unittest.TestCase):

    '''
    Miscellaneous test for stuff in the pilot package.
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

    def testIndependentControls(self):
        '''
        Altitude, Speed and Heading change independently one from another.
        '''
        def setup():
            self.plane.position = Vector3(10000,10000,0)
            self.plane.velocity = Vector3(150, 0, 0)  #~500kpm eastbound
            self.plane.pilot._set_target_conf_to_current()
        def perform():
            pi = self.plane.pilot
            pl = self.plane
            changed_keys = set()
            for i in range(500):  #arbitrary but reasonable limit...
                pl.update(1)
                current_conf = pl.get_current_configuration()
                if not pi.target_conf.is_reached():
                    for k in current_conf:
                        if current_conf[k] != getattr(pi.target_conf, k):
                            changed_keys.add(k)
            return changed_keys
        # Test speed variation
        setup()
        self.plane.max_speed = 1000 / 3.6  #1000 kph
        self.plane.pilot.target_conf.speed = 900 / 3.6
        self.assertEqual(perform(), set(['speed']))
        # Test altitude variation
        setup()
        self.plane.pilot.target_conf.altitude = 5000
        self.assertEqual(perform(), set(['altitude']))
        # Test heading variation
        setup()
        self.pilot.veering_direction = LEFT
        self.plane.pilot.target_conf.heading = 265
        self.assertEqual(perform(), set(['heading']))

    def testDoNotOscillate(self):
        '''
        Does the plane reach a stable flight configuration after manouvering?
        '''
        def setup():
            self.plane.position = Vector3(10000,10000,0)
            self.plane.velocity = Vector3(150, 0, 0)  #~500kpm eastbound
            self.plane.pilot._set_target_conf_to_current()
        def perform():
            previous = None
            for i in range(500):  #arbitrary but reasonable limit...
                self.plane.update(1)
                if self.pilot.target_conf.is_reached() and \
                   (self.plane.get_current_configuration() == previous):
                    return True
                previous = self.plane.get_current_configuration()
            return False
        # Test altitude variation
        setup()
        self.plane.pilot.target_conf.altitude = 5000
        self.assertTrue(perform())
        # Test heading variation (left)
        setup()
        self.pilot.veering_direction = LEFT
        self.plane.pilot.target_conf.heading = 265
        self.assertTrue(perform())
        # Test heading variation (right)
        setup()
        self.pilot.veering_direction = RIGHT
        self.plane.pilot.target_conf.heading = 87
        self.assertTrue(perform())
        # Test speed variation
        setup()
        self.plane.max_speed = 1000
        self.plane.pilot.target_conf.speed = 300
        self.assertTrue(perform())
        # Test combined variation
        setup()
        self.pilot.veering_direction = LEFT
        self.plane.max_speed = 1000
        self.plane.pilot.target_conf.heading = 123
        self.plane.pilot.target_conf.altitude = 3543
        self.plane.pilot.target_conf.speed = 677
        self.assertTrue(perform())

    def testCommandsDoNotRaise(self):
        '''
        Test that the commands do not raise exceptions (complete returning
        True or False).
        '''
        TO_TEST = [('ABORT', [], ['LASTONLY']),
                   ('ALTITUDE', [5], ['EXPEDITE']),
                   ('BYE', [], []),
                   ('CIRCLE', ['CCW'], []),
                   ('CLEAR', [Vector3()], []),
                   ('HEADING', [270], ['LONG']),
                   ('HEADING', [Vector3()], ['LONG']),
                   ('LAND', ['ABC', '36'], []),
                   ('SPEED', [500], []),
                   ('SQUAWK', [], []),
                   ('TAKEOFF', [1000], []),
                   ]
        # This tests if this test is complete, by verifying there is at least
        # a test command for each existing command
        self.assertEqual(set(engine.commander.PLANE_COMMANDS.keys()),
                         set([a for a,b,c in TO_TEST]))
        for command in TO_TEST:
            self.assertIsInstance(self.pilot.do([command]), bool)

    def testHeadingLongFlag(self):
        '''
        Test that the plane execute veering in the right direction.
        '''
        self.plane.velocity = heading_to_v3(90).normalized() * 300 / 3.6
        self.pilot.do([('HEADING', [180], ['LONG'])])
        self.plane.update(5)
        self.assertFalse(heading_in_between([90,180], self.plane.heading))

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()