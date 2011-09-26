#!/usr/bin/env python
# -*- coding: utf-8  -*-
'''
Testing suite for the pilot.navigator module.
'''

import unittest

import entities.aeroplane as aero
import pilot.pilot as pilo
from lib.euclid import Vector3

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


class NavigatorTest(unittest.TestCase):

    '''
    Test each function of the pilot.navigator module.
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

    def testRunwayExists(self):
        '''
        check_existing_runway
        '''
        pass

    def testOvershot(self):
        '''
        check_overshot
        '''
        pass

    def testTooClose(self):
        '''
        check_too_close
        '''
        pass

    def testPointAhead(self):
        '''
        get_point_ahead
        '''
        pass

    def testCourseTowards(self):
        '''
        get_course_towards - Is the vector to the target correct?
        '''
        def perform(x, y):  # x, y = position relative to plane position
            self.plane.position = Vector3(10000,10000)
            self.plane.velocity = Vector3(0)
            point = Vector3(10000+x, 10000+y)
            tmp = self.pilot.navigator.get_course_towards(point)
            self.pilot.target_conf.heading = tmp
        perform(10000,10000)
        self.assertEqual(self.plane.pilot.target_conf.heading, 45)
        perform(-10000,-10000)
        self.assertEqual(self.plane.pilot.target_conf.heading, 225)
        perform(0, 10000)
        self.assertEqual(self.plane.pilot.target_conf.heading, 0)
        perform(-5000*3**0.5, 5000)
        self.assertEqual(self.plane.pilot.target_conf.heading, 300)

    def testAversionCourse(self):
        '''
        get_aversion_course
        '''
        pass

    def testMinimumAltitude(self):
        '''
        get_required_minimum_altitude
        '''
        #TODO: When mimimum altitudes will be implemented!
        pass

    def testShortestVeeringDirection(self):
        '''
        get_shortest_veering_direction
        '''
        pass

    def testIntersectionPoint(self):
        '''
        get_intersection_point
        '''
        pass

    def testVeeringRadius(self):
        '''
        get_veering_radius - Is the extimate of the veering radio correct?
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
        func = self.pilot.navigator.get_veering_radius
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