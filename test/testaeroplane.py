#!/usr/bin/env python
# -*- coding: utf-8  -*-
'''
Testing suite for entities/aeroplane.
'''

import unittest
import entities.aeroplane as aero
from lib.euclid import Vector3

__author__ = "Mac Ryan"
__copyright__ = "Copyright 2011, Mac Ryan"
#__credits__ = ["Name Lastname", "Name Lastname"]
__license__ = "GPL v3"
#__version__ = "1.0.0"
__maintainer__ = "Mac Ryan"
__email__ = "quasipedia@gmail.com"
__status__ = "Development"


class AtomicTest(unittest.TestCase):

    '''
    Series of tests that can be performed on aeroplanes without having to place
    them within an aerospace/game logic/scenario.
    '''

    def setUp(self):
        self.plane = aero.Aeroplane(icao='ABC1234', max_g=2.0)
        self.pilot = self.plane.pilot

    def testInBetween(self):
        '''
        Is a number comprised between two?
        '''
        func = self.pilot.test_in_between
        # Positive range
        self.assertTrue(func((0, 10), 5))
        self.assertTrue(func((10, 0), 5))
        self.assertFalse(func((0, 10), 15))
        self.assertFalse(func((10, 0), 15))
        # Negative range
        self.assertTrue(func((0, -10), -5))
        self.assertTrue(func((-10, 0), -5))
        self.assertFalse(func((0, -10), -15))
        self.assertFalse(func((-10, 0), -15))
        # Spanning range
        self.assertTrue(func((10, -10), 5))
        self.assertTrue(func((-10, 10), 5))
        self.assertTrue(func((10, -10), -5))
        self.assertTrue(func((-10, 10), -5))
        self.assertFalse(func((10, -10), 15))
        self.assertFalse(func((-10, 10), 15))
        self.assertFalse(func((10, -10), -15))
        self.assertFalse(func((-10, 10), -15))
        # Edges
        self.assertTrue(func((-10, 10), 10))
        self.assertTrue(func((-10, 10), -10))
        # Punctiform
        self.assertTrue(func((10, 10), 10))

    def testHeadingInBetween(self):
        '''
        Is a heading comprised in the shortest arc between other two?
        '''
        func = self.pilot.test_heading_in_between
        # Normalised values
        self.assertTrue(func((0, 90), 45))
        self.assertFalse(func((270, 0), 45))
        # Non-normalised values
        self.assertTrue(func((-60, 60), -1))
        self.assertTrue(func((-60, 60), -0))
        self.assertTrue(func((-60, 60), 1))
        self.assertTrue(func((60, -60), -1))
        self.assertTrue(func((60, -60), -0))
        self.assertTrue(func((60, -60), 1))
        self.assertFalse(func((-60, 60), -179))
        self.assertFalse(func((-60, 60), -180))
        self.assertFalse(func((-60, 60), 180))
        self.assertFalse(func((-60, 60), 179))
        self.assertFalse(func((60, -60), -179))
        self.assertFalse(func((60, -60), -180))
        self.assertFalse(func((60, -60), 180))
        self.assertFalse(func((60, -60), 179))
        # Tricky cases
        self.assertTrue(func((-90, 90), 0))
        self.assertTrue(func((-90, 90), 180))

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
        self.assertEqual(self.plane.target_conf['heading'], 45)
        perform(-10000,-10000)
        self.assertEqual(self.plane.target_conf['heading'], 225)
        perform(0, 10000)
        self.assertEqual(self.plane.target_conf['heading'], 0)
        perform(-5000*3**0.5, 5000)
        self.assertEqual(self.plane.target_conf['heading'], 300)

    def testIndependentControls(self):
        '''
        Altitude, Speed and Heading change independently one from another.
        '''
        def setup():
            self.plane.position = Vector3(10000,10000,0)
            self.plane.velocity = Vector3(150, 0, 0)  #~500kpm eastbound
            self.plane.set_target_conf_to_current()
        def perform():
            changed_keys = set()
            for i in range(500):  #arbitrary but reasonable limit...
                self.plane.update(1)
                current_conf = self.plane.get_current_configuration()
                if self.plane.target_conf != current_conf:
                    for k in current_conf:
                        if current_conf[k] != self.plane.target_conf[k]:
                            changed_keys.add(k)
            return changed_keys
        # Test altitude variation
        setup()
        self.plane.target_conf['altitude'] = 5000
        self.assertEqual(perform(), set(['altitude']))
        # Test heading variation
        setup()
        self.pilot.veering_direction = self.pilot.LEFT
        self.plane.target_conf['heading'] = 265
        self.assertEqual(perform(), set(['heading']))
        # Test speed variation
        setup()
        self.plane.max_speed = 1000
        self.plane.target_conf['speed'] = 500
        self.assertEqual(perform(), set(['speed']))

    def testDoNotOscillate(self):
        '''
        Does the plane reach a stable flight configuration after manouvering?
        '''
        def setup():
            self.plane.position = Vector3(10000,10000,0)
            self.plane.velocity = Vector3(150, 0, 0)  #~500kpm eastbound
            self.plane.set_target_conf_to_current()
        def perform():
            previous = None
            for i in range(500):  #arbitrary but reasonable limit...
                self.plane.update(1)
                if self.plane.target_conf == \
                   self.plane.get_current_configuration() == previous:
                    return True
                previous = self.plane.get_current_configuration()
            return False
        # Test altitude variation
        setup()
        self.plane.target_conf['altitude'] = 5000
        self.assertTrue(perform())
        # Test heading variation (left)
        setup()
        self.pilot.veering_direction = self.pilot.LEFT
        self.plane.target_conf['heading'] = 265
        self.assertTrue(perform())
        # Test heading variation (right)
        setup()
        self.pilot.veering_direction = self.pilot.RIGHT
        self.plane.target_conf['heading'] = 87
        self.assertTrue(perform())
        # Test speed variation
        setup()
        self.plane.max_speed = 1000
        self.plane.target_conf['speed'] = 300
        self.assertTrue(perform())
        # Test combined variation
        setup()
        self.pilot.veering_direction = self.pilot.LEFT
        self.plane.max_speed = 1000
        self.plane.target_conf = dict(speed = 677, altitude=3543, heading=123)
        self.assertTrue(perform())


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()