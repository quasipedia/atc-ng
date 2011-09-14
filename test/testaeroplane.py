#!/usr/bin/env python
# -*- coding: utf-8  -*-
'''
Testing suite for entities/aeroplane.
'''

import unittest
import entities.aeroplane as aero
import entities.pilot as pilo
import engine.commander
from lib.euclid import Vector3
from lib.utils import *

__author__ = "Mac Ryan"
__copyright__ = "Copyright 2011, Mac Ryan"
__license__ = "GPL v3"
#__version__ = "1.0.0"
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

class AtomicTest(unittest.TestCase):

    '''
    Series of tests that can be performed on aeroplanes without having to place
    them within an aerospace/game logic/scenario.
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
        for n in range (MIN, MAX, 10):
            # UPPER ALTITUDE LIMIT
            self.plane.max_altitude = n
            self.assertEqual(True,
                             (self.pilot.verify_feasibility(altitude=n/3.6)))
            self.assertEqual(True,
                             (self.pilot.verify_feasibility(altitude=n-1)))
            self.assertNotEqual(True,
                                self.pilot.verify_feasibility(altitude=n+1))
            # UPPER SPEED LIMIT
            self.plane.min_speed = (MIN-10) / 3.6  #convert kph to m/s
            self.plane.max_speed = n / 3.6  #convert kph to m/s
            self.assertEqual(True,
                             (self.pilot.verify_feasibility(speed=n/3.6)))
            self.assertEqual(True,
                             (self.pilot.verify_feasibility(speed=(n-1)/3.6)))
            self.assertNotEqual(True,
                                self.pilot.verify_feasibility(speed=(n+1)/3.6))
            # LOWER SPEED LIMIT
            self.plane.min_speed = n / 3.6  #convert kph to m/s
            self.plane.max_speed = (MAX+10) / 3.6  #convert kph to m/s
            self.assertEqual(True,
                             (self.pilot.verify_feasibility(speed=n/3.6)))
            self.assertEqual(True,
                             (self.pilot.verify_feasibility(speed=(n+1)/3.6)))
            self.assertNotEqual(True,
                                self.pilot.verify_feasibility(speed=(n-1)/3.6))

    def testVeeringRadius(self):
        '''
        Is the extimate of the veering radio correct?
        This implicitly also tests: get_veering_angular_velocity()
        Known values have been extracted from:
        http://www.csgnetwork.com/aircraftturninfocalc.html
        '''
        # All tuples are in the format (speed_knots, radius_feet)
        KNOWN_30 = [(100, 1540.8),
                    (200, 6163.3),
                    (500, 38520.9),
                    (750, 86672.0),
                    (1000, 154083.6)]
        KNOWN_45 = [(100, 889.8),
                    (200, 3559.1),
                    (500, 22244.1),
                    (750, 50049.3),
                    (1000, 88976.5)]
        KNOWN_60 = [(100, 513.9),
                    (200, 2055.7),
                    (500, 12848.2),
                    (750, 28908.4),
                    (1000, 51392.7)]
        knots_to_ms = lambda n : n * 0.514444444
        feet_to_m = lambda n : n * 0.3048
        func = self.pilot.get_veering_radius
        # Max tolerance for the test is 2%
        for kts, feet in KNOWN_30:
            radius = func('normal', knots_to_ms(kts))
            self.assertAlmostEqual(feet_to_m(feet), radius, delta=radius*0.02)
        for kts, feet in KNOWN_45:
            radius = func('expedite', knots_to_ms(kts))
            self.assertAlmostEqual(feet_to_m(feet), radius, delta=radius*0.02)
        for kts, feet in KNOWN_60:
            radius = func('emergency', knots_to_ms(kts))
            self.assertAlmostEqual(feet_to_m(feet), radius, delta=radius*0.02)

    def testHeadTowardsPoint(self):
        '''
        Is the vector to the target correct?
        '''
        def perform(x, y):  # x, y = position relative to plane position
            self.plane.position = Vector3(10000,10000)
            self.plane.velocity = Vector3(0)
            self.pilot.set_course_towards((10000+x, 10000+y))
        perform(10000,10000)
        self.assertEqual(self.plane.pilot.target_conf['heading'], 45)
        perform(-10000,-10000)
        self.assertEqual(self.plane.pilot.target_conf['heading'], 225)
        perform(0, 10000)
        self.assertEqual(self.plane.pilot.target_conf['heading'], 0)
        perform(-5000*3**0.5, 5000)
        self.assertEqual(self.plane.pilot.target_conf['heading'], 300)

    def testIndependentControls(self):
        '''
        Altitude, Speed and Heading change independently one from another.
        '''
        def setup():
            self.plane.position = Vector3(10000,10000,0)
            self.plane.velocity = Vector3(150, 0, 0)  #~500kpm eastbound
            self.plane.pilot.set_target_conf_to_current()
        def perform():
            changed_keys = set()
            for i in range(500):  #arbitrary but reasonable limit...
                self.plane.update(1)
                current_conf = self.plane.get_current_configuration()
                if self.plane.pilot.target_conf != current_conf:
                    for k in current_conf:
                        if current_conf[k] != self.plane.pilot.target_conf[k]:
                            changed_keys.add(k)
            return changed_keys
        # Test speed variation
        setup()
        self.plane.max_speed = 1000 / 3.6  #1000 kph
        self.plane.pilot.target_conf['speed'] = 900
        self.assertEqual(perform(), set(['speed']))
        # Test altitude variation
        setup()
        self.plane.pilot.target_conf['altitude'] = 5000
        self.assertEqual(perform(), set(['altitude']))
        # Test heading variation
        setup()
        self.pilot.veering_direction = self.pilot.LEFT
        self.plane.pilot.target_conf['heading'] = 265
        self.assertEqual(perform(), set(['heading']))

    def testDoNotOscillate(self):
        '''
        Does the plane reach a stable flight configuration after manouvering?
        '''
        def setup():
            self.plane.position = Vector3(10000,10000,0)
            self.plane.velocity = Vector3(150, 0, 0)  #~500kpm eastbound
            self.plane.pilot.set_target_conf_to_current()
        def perform():
            previous = None
            for i in range(500):  #arbitrary but reasonable limit...
                self.plane.update(1)
                if self.plane.pilot.target_conf == \
                   self.plane.get_current_configuration() == previous:
                    return True
                previous = self.plane.get_current_configuration()
            return False
        # Test altitude variation
        setup()
        self.plane.pilot.target_conf['altitude'] = 5000
        self.assertTrue(perform())
        # Test heading variation (left)
        setup()
        self.pilot.veering_direction = self.pilot.LEFT
        self.plane.pilot.target_conf['heading'] = 265
        self.assertTrue(perform())
        # Test heading variation (right)
        setup()
        self.pilot.veering_direction = self.pilot.RIGHT
        self.plane.pilot.target_conf['heading'] = 87
        self.assertTrue(perform())
        # Test speed variation
        setup()
        self.plane.max_speed = 1000
        self.plane.pilot.target_conf['speed'] = 300
        self.assertTrue(perform())
        # Test combined variation
        setup()
        self.pilot.veering_direction = self.pilot.LEFT
        self.plane.max_speed = 1000
        self.plane.pilot.target_conf = dict(speed = 677, altitude=3543,
                                            heading=123)
        self.assertTrue(perform())

    def testCommandsDoNotRaise(self):
        '''
        Test that the commands do not raise exceptions (complete returning
        True or False).
        '''
        TO_TEST = [('circle', ['ccw'], []),
                   ('squawk', [], []),
                   ('land', ['abc', '36'], []),
                   ('altitude', [5], ['expedite']),
                   ('abort', [], ['lastonly']),
                   ('takeoff', [1000], []),
                   ('speed', [500], []),
                   ('heading', [270], ['long'])]
        # This tests if this test is complete, by verifying there is at least
        # a test command for each existing command
        self.assertEqual(set(engine.commander.PLANE_COMMANDS.keys()),
                         set([a for a,b,c in TO_TEST]))
        for command in TO_TEST:
            self.assertIsInstance(self.pilot.execute_command([command]),
                                  bool)

    def testHeadingLongFlag(self):
        '''
        Test that the plane execute veering in the right direction.
        '''
        self.plane.velocity = heading_to_v3(90).normalized() * 300 / 3.6
        self.pilot.execute_command([('heading', [180], ['long'])])
        self.plane.update(5)
        self.assertFalse(heading_in_between([90,180], self.plane.heading))

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()