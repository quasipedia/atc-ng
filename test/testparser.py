#!/usr/bin/env python
# -*- coding: utf-8  -*-
'''
Testing suite for commandline parser.
'''

import unittest

import entities.aeroplane as aero
import pilot.pilot as pilo
import engine.commander as comm
from lib.euclid import Vector3

__author__ = "Mac Ryan"
__copyright__ = "Copyright 2011, Mac Ryan"
__license__ = "GPL v3"
#__version__ = "<dev>"
#__date__ = "<unknown>"
__maintainer__ = "Mac Ryan"
__email__ = "quasipedia@gmail.com"
__status__ = "Development"

# Mock classes to allow creation of Aeroplanes that do not throw exceptions.
class MockBeacon(object):
    def __init__(self):
        self.location = Vector3(10, 10, 10)
class MockGameLogic(object):
    def score_event(self, *args, **kwargs):
        pass
    def say(self, *args, **kwargs):
        pass
class MockAerospace(object):
    def __init__(self):
        self.tcas_data = {}
        self.gamelogic = MockGameLogic()
        self.plane = None
        self.beacons = {'NDB1':MockBeacon()}
        self.airports = []
    def get_plane_by_icao(self, icao):
        return self.plane if icao == self.plane.icao else None
class MockProcessor(object):
    def xxx(self, *args, **kwargs):
        self.last = [args, kwargs]

class ParserTest(unittest.TestCase):

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
        mock_aerospace.plane = self.plane
        self.pilot = self.plane.pilot
        mock_processor = MockProcessor()
        self.parser = comm.Parser(mock_aerospace, mock_processor)

    def testCommandsFullAuto(self):
        '''
        Automatically test all commands, building possible forms from
        introspectively looking at the YAML definition file.
        '''
        ARGUMENTS = dict(ABORT = [],
                         ALTITUDE = ['25', '05'],
                         BYE = [],
                         CIRCLE = ['CCW', 'L', 'LEFT', 'RIGHT', 'R', 'CW'],
                         CLEAR = ['NDB1'],
                         HEADING = ['135', '000', '360', '090'],
                         LAND = ['ARN 01L', 'ARN 19L', 'ARN 08', 'ARN 26'],
                         SPEED = ['450', '525'],
                         SQUAWK = [],
                         TAKEOFF = ['01R', '01L', '08', '26'],
                         )
        icao = 'ABC1234'
        commands = comm.PLANE_COMMANDS
        # build all possible records to test
        records = []
        for command, c_values in commands.items():
            for arg in ARGUMENTS[command]:
                # Process the expected commands
                if command == 'ALTITUDE':
                    exp_arg = [int(arg) * 100]
                elif command == 'SPEED':
                    exp_arg = [int(arg) / 3.6]
                elif command == 'HEADING':
                    exp_arg = [int(arg)]
                elif command == 'LAND':
                    exp_arg = arg.split()
                elif command == 'CLEAR':
                    exp_arg = [Vector3(10, 10, 10)]
                else:
                    exp_arg  = [arg]
                for c_spell in c_values['spellings']:
                    if c_values['flags']:
                        for flag, f_values in c_values['flags'].items():
                            for f_spell in f_values:
                                line = '%s %s %s %s' % \
                                       (icao, c_spell, arg, f_spell)
                                expected = [command, exp_arg, [flag]]
                                records.append((line, expected))
                    # We always want to try commands without flags...
                    line = '%s %s %s' % (icao, c_spell, arg)
                    expected = [command, exp_arg, []]
                    records.append((line, expected))
        # process all the test records
        for line, expected in records:
            self.parser.initialise(line)
            # discard the callable, and assume only one take the first line
            # of commands [we never combine commands in this test]
            result = self.parser.parse()
            to_compare = result[1][0]
            self.assertEqual(to_compare, expected)

    def testShortHandNotation(self):
        '''
        Test the shortand notation ``HXXX SXXX AXX``.
        '''
        TO_TEST = [('ABC1234 H135', True),
                   ('ABC1234 S500', True),
                   ('ABC1234 A20', True),
                   ('ABC1234 A200', False),
                   ('ABC1234 A20 S500 H135', True),
                   ('ABC1234 S500 H135', True),
                   ('ABC1234 A20 H135', True),
                   ('ABC1234 A20 S500', True)]
        for line, expected in TO_TEST:
            self.parser.initialise(line)
            # discard the callable, and assume only one take the first line
            # of commands [we never combine commands in this test]
            result = self.parser.parse()
            to_compare = result[1][0]
            self.assertEqual(type(to_compare) == list, expected, msg=result)

    def testHeadingToBeacons(self):
        '''
        Test command ``HEADING`` works fine with beacons.
        '''
        TO_TEST = [('ABC1234 HEAD NDB1', True),
                   ('ABC1234 HEAD NDB2', False),]
        for line, expected in TO_TEST:
            self.parser.initialise(line)
            # discard the callable, and assume only one take the first line
            # of commands [we never combine commands in this test]
            result = self.parser.parse()
            to_compare = result[1][0]
            self.assertEqual(type(to_compare) == list, expected, result)

    def testRelativeHeading(self):
        '''
        Test command ``HEADING`` works fine with relatives entries.
        '''
        TO_TEST = [('ABC1234 HEAD +45', True),
                   ('ABC1234 HEAD -120', True),
                   ('ABC1234 HEAD -ABC', False),]
        for line, expected in TO_TEST:
            self.parser.initialise(line)
            # discard the callable, and assume only one take the first line
            # of commands [we never combine commands in this test]
            result = self.parser.parse()
            to_compare = result[1][0]
            self.assertEqual(type(to_compare) == list, expected, result)

    def testRebutWrongCombos(self):
        '''
        Tests that the parser refuses wrong combinations of commands.
        '''
        TO_TEST = [('ABC1234 CIRCLE CCW HEADING +45'),
                   ('ABC1234 LAND NAD 01L CIRCLE R'),
                   ('ABC1234 LAND MAC 18 CLEAR NDB1')]
        for line in TO_TEST:
            self.parser.initialise(line)
            self.assertIsInstance(self.parser.parse(), str)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()