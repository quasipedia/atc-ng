#!/usr/bin/env python
# -*- coding: utf-8  -*-
'''
Test the util heading_in_betweentions for ATC-NG game.
'''

import unittest
import entities.aeroplane as aero
from lib.utils import *
from random import randint
from lib.euclid import Vector3

__author__ = "Mac Ryan"
__copyright__ = "Copyright 2011, Mac Ryan"
#__credits__ = ["Name Lastname", "Name Lastname"]
__license__ = "GPL v3"
#__version__ = "1.0.0"
__maintainer__ = "Mac Ryan"
__email__ = "quasipedia@gmail.com"
__status__ = "Development"


class Test(unittest.TestCase):

    '''
    Test the utility heading_in_betweentions.
    '''

    def testRint(self):
        '''
        rint - round to integer and typecast to int
        '''
        self.assertEqual(rint(0.35), 0)
        self.assertEqual(rint(0.835), 1)
        self.assertIsInstance(rint(3465657.4545), int)

    def testSc(self):
        '''
        sc - transform coordinates from "world logic" to radar screen
        '''
        for i in range(100):
            x = randint(0, 2*RADAR_RANGE)
            y = randint(0, 2*RADAR_RANGE)
            x, y = sc((x,y))
            self.assertGreaterEqual(x, 0)
            self.assertLessEqual(x, RADAR_RECT.width)
            self.assertGreaterEqual(y, 0)
            self.assertLessEqual(y, RADAR_RECT.height)

    def testVector2Heading(self):
        '''
        v3_to_heading - heading of a vector
        '''
        TOTEST = [((0, 1, -27),    0),
                  ((0, -1, +0.57), 180),
                  ((1, 1, 0),      45),
                  ((-10, 10, 0),   315),
                  ]
        for vector, result in TOTEST:
            vector = Vector3(*vector)
            self.assertEqual(v3_to_heading(vector), result)

    def testHeading2Vector(self):
        '''
        heading_to_v3 - normalized vector pointint towards heading"
        '''
        TO_TEST = [(  0, ( 0,  1, 0)),
                   ( 90, ( 1,  0, 0)),
                   (180, ( 0, -1, 0)),
                   (270, (-1,  0, 0)),
                   (360, ( 0,  1, 0)),
                   ( 45, (1/2**0.5, 1/2**0.5, 0))
                   ]
        for heading, xyz in TO_TEST:
            res = heading_to_v3(heading)
            tuples = zip(res.xyz, xyz)
            for a, b in tuples:
                self.assertAlmostEqual(a,b)

    def testIntersectSegment(self):
        '''
        intersect_by_points - intersect two lines
        '''
        # Format: list of points, expected result
        POSITIVES = [([(-1,-1), (1,1), (-1,1), (1,-1)], (0,0)  ),
                     ([(-1,0),  (1,0), (0,1),  (0,-1)], (0,0)  ),
                     ([(0,0),   (2,2), (2,0),  (0,2) ], (1,1)  ),
                     ([(0,0),   (2,1), (1,0),  (1,2) ], (1,0.5))]
        NEGATIVES = [([(-1,-1), (1,1), (5,5),  (6,6) ], (None, 'separation')),
                     ([(0,0),   (7,7), (0,0),  (7,7) ], (None, 'overlapping')),
                     ([(0,0),   (0,9), (2,0),  (2,9) ], (None, 'parallelism'))]
        for points, result in POSITIVES:
            res = segment_intersection(*points)
            self.assertEqual(res[1], 'intersection')
            self.assertAlmostEqual(res[0][0], result[0], 4)
            self.assertAlmostEqual(res[0][1], result[1], 4)
        for points, result in NEGATIVES:
            res = segment_intersection(*points)
            self.assertEqual(res, result)

    def testRectangleIntersection(self):
        '''
        rectangle_intersection - intersect rectangles
        '''
        POSITIVES = [[(0,0),     (5,5),       (4,4),     (7,7)],
                     [(-1,0),    (1,5),       (0,3),     (8,8)],
                     [(-5.1,2),  (-7,-2.3),   (-6.1,12), (3,-3)],
                     [(0,0),     (7,7),       (0,0),     (-7,-7)],
                     [(0,0),     (2,1),       (1,0),     (1,2)]]
        NEGATIVES = [[(-1,-1),   (1,1),       (5,5),     (6,6)],
                     [(-8.4,-2), (-7.33,1.3), (2,0.1),   (3,9)]]
        for points in POSITIVES:
            self.assertTrue(rectangle_intersection(*points))
        for points in NEGATIVES:
            self.assertFalse(rectangle_intersection(*points))

    def testGroundDistance(self):
        '''
        ground_distance - ground distance between points
        '''
        TO_TEST = [((0,0,0), (0,0,10),   0),
                   ((0,0,0), (0,10,0),   10),
                   ((0,0,0), (10,0,0),   10),
                   ((0,0,0), (1,1,1),    2**0.5),
                   ((0,0,0), (-1,-1,-1), 2**0.5)]
        for v1, v2, r in TO_TEST:
            back = ground_distance(Vector3(*v1), Vector3(*v2))
            self.assertAlmostEqual(back, r, 5)

    def testInBetween(self):
        '''
        in_between - number comprised between two?
        '''
        # Positive range
        self.assertTrue(in_between((0, 10), 5))
        self.assertTrue(in_between((10, 0), 5))
        self.assertFalse(in_between((0, 10), 15))
        self.assertFalse(in_between((10, 0), 15))
        # Negative range
        self.assertTrue(in_between((0, -10), -5))
        self.assertTrue(in_between((-10, 0), -5))
        self.assertFalse(in_between((0, -10), -15))
        self.assertFalse(in_between((-10, 0), -15))
        # Spanning range
        self.assertTrue(in_between((10, -10), 5))
        self.assertTrue(in_between((-10, 10), 5))
        self.assertTrue(in_between((10, -10), -5))
        self.assertTrue(in_between((-10, 10), -5))
        self.assertFalse(in_between((10, -10), 15))
        self.assertFalse(in_between((-10, 10), 15))
        self.assertFalse(in_between((10, -10), -15))
        self.assertFalse(in_between((-10, 10), -15))
        # Edges
        self.assertTrue(in_between((-10, 10), 10))
        self.assertTrue(in_between((-10, 10), -10))
        # Punctiform
        self.assertTrue(in_between((10, 10), 10))

    def testHeadingInBetween(self):
        '''
        heading_in_between - heading in the shortest arc between other two
        '''
        # Normalised values
        self.assertTrue(heading_in_between((0, 90), 45))
        self.assertFalse(heading_in_between((270, 0), 45))
        # Non-normalised values
        self.assertTrue(heading_in_between((-60, 60), -1))
        self.assertTrue(heading_in_between((-60, 60), -0))
        self.assertTrue(heading_in_between((-60, 60), 1))
        self.assertTrue(heading_in_between((60, -60), -1))
        self.assertTrue(heading_in_between((60, -60), -0))
        self.assertTrue(heading_in_between((60, -60), 1))
        self.assertFalse(heading_in_between((-60, 60), -179))
        self.assertFalse(heading_in_between((-60, 60), -180))
        self.assertFalse(heading_in_between((-60, 60), 180))
        self.assertFalse(heading_in_between((-60, 60), 179))
        self.assertFalse(heading_in_between((60, -60), -179))
        self.assertFalse(heading_in_between((60, -60), -180))
        self.assertFalse(heading_in_between((60, -60), 180))
        self.assertFalse(heading_in_between((60, -60), 179))
        # Tricky cases
        self.assertTrue(heading_in_between((-90, 90), 0))
        self.assertTrue(heading_in_between((-90, 90), 180))



if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()