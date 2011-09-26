#!/usr/bin/env python
# -*- coding: utf-8  -*-
'''
Testing suite for the pilot.navigator module.
'''

import unittest

import entities.aeroplane as aero
import pilot.pilot as pilo
from lib.euclid import Vector3
from engine.settings import settings as S

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
class MockAirport(object):
    def __init__(self):
        self.runways = ['01', '10L', '20C', '36']
class MockAerospace(object):
    def __init__(self):
        self.tcas_data = {}
        self.gamelogic = MockGameLogic()
        self.airports = {}
        for icao in ('ABC', 'XYZ', 'NNO'):
            self.airports[icao] = MockAirport()


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
        check_existing_runway - Runway exists on map.
        '''
        n = self.pilot.navigator
        self.assertTrue(n.check_existing_runway('ABC', '36'))
        self.assertTrue(n.check_existing_runway('XYZ', '20C'))
        self.assertTrue(n.check_existing_runway('MNO', '10L'))
        self.assertNotEqual(n.check_existing_runway('ABC', '18'), True)
        self.assertNotEqual(n.check_existing_runway('EFG', '36'), True)

    def testOvershot(self):
        '''
        check_overshot - Plane has flown past a point.
        '''
        f = self.pilot.navigator.check_overshot
        TO_TEST = [((100, 0, 5), (0, 0, 0), False),  #on the point!
                   ((100, 0, 5), (50, 0, 0), False),
                   ((100, 0, 5), (200, 0, 0), False),
                   ((100, 0, 5), (110, 300, 0), False),
                   ((100, 100, 5), (0, -1, 0), True),
                   ]
        for velocity, point, result in TO_TEST:
            self.plane.velocity = Vector3(*velocity)
            self.assertEqual(f(Vector3(*point)), result)

    def testReachable(self):
        '''
        check_reachable - Plane can fly over a given point.
        '''
        # According to http://www.csgnetwork.com/aircraftturninfocalc.html,
        # 100 m/s would result in veering radii of:
        # normal, 30° --> 1 774.57608 metres
        # expedite, 45° --> 1 024.7376 metres
        # emergency, 60° -->  591.89112 metres
        f = self.pilot.navigator.check_reachable
        self.plane.velocity = Vector3(100, 0, 0)
        TO_TEST = [('normal', (1800, 1800, 0), True),
                   ('expedite', (1800, 1800, 0), True),
                   ('emergency', (1800, 1800, 0), True),
                   ('normal', (1100, 1100, 0), False),
                   ('expedite', (1100, 1100, 0), True),
                   ('emergency', (1100, 1100, 0), True),
                   ('normal', (600, 600, 0), False),
                   ('expedite', (600, 600, 0), False),
                   ('emergency', (600, 600, 0), True),
                   ('normal', (550, 550, 0), False),
                   ('expedite', (550, 550, 0), False),
                   ('emergency', (550, 550, 0), False),
                   ]
        for haste, point, result in TO_TEST:
            self.pilot.status['haste'] = haste
            self.assertEqual(f(Vector3(*point)), result)

    def testPointAhead(self):
        '''
        get_point_ahead - Returns co-ordinates of a point X metres ahead.
        '''
        f = self.pilot.navigator.get_point_ahead
        self.plane.velocity = Vector3(100, 0, 0)
        TO_TEST = [((100, 100, 0), (100, 0, 0), 100, (200, 100, 0)),
                   ((-100, 0, 0), (100, 100, 0), 100*2**0.5, (0, 100, 0)),
                   ((150, 150, 0), (0, -100, 0), 150, (150, 0, 0)),
                   ]
        for position, velocity, distance, expected in TO_TEST:
            self.plane.position = Vector3(*position)
            self.plane.velocity = Vector3(*velocity)
            self.assertAlmostEqual(f(distance), Vector3(*expected), delta=1)


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

    def testMinimumAltitude(self):
        '''
        get_required_minimum_altitude - detects no-fly zones and ground
        '''
        #TODO: When mimimum altitudes will be implemented!
        pass

    def testShortestVeeringDirection(self):
        '''
        get_shortest_veering_direction - which way to veer?
        '''
        f = self.pilot.navigator.get_shortest_veering_direction
        self.plane.velocity = Vector3(100, 0, 0)
        TO_TEST = [(0, S.LEFT),
                   (180, S.RIGHT),
                   (Vector3(-100, 1), S.LEFT),
                   (Vector3(-100, -1), S.RIGHT),
                   ]
        for heading, expected in TO_TEST:
            self.pilot.target_conf.heading = heading
            self.assertEqual(f(), expected)

    def testIntersectionPoint(self):
        '''
        get_intersection_point - where is the plane intercepting a given line?
        '''
        f = self.pilot.navigator.get_intersection_point
        self.plane.velocity = Vector3(100, 0, 0)
        TO_TEST = [((1, 1, 0), (0, -3, 0), (3, 0)),
                   ((0, 1, 0), (-5, -3, 0), (-5, 0)),
                   ]
        for vector, point, expected in TO_TEST:
            result = f(Vector3(*vector), Vector3(*point))
            expected = (expected, 'intersection')
            self.assertEqual(result, expected)

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