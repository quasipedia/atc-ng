#!/usr/bin/env python
# -*- coding: utf-8  -*-
'''
Testing suite for entities/aeroplane.
'''

import unittest
import entities.aeroplane as aero


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

    plane = aero.Aeroplane(icao='ABC1234', max_g=2.0)
    pilot = plane.pilot

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


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()