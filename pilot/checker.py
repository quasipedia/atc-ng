#!/usr/bin/env python
# -*- coding: utf-8  -*-
'''
Verify if a given order can be performed.
'''

import lib.utils as U

__author__ = "Mac Ryan"
__copyright__ = "Copyright ©2011, Mac Ryan"
#__credits__ = ["Name Lastname", "Name Lastname"]
__license__ = "GPL v3"
#__version__ = "<dev>"
#__date__ = "<unknown>"
__maintainer__ = "Mac Ryan"
__email__ = "quasipedia@gmail.com"
__status__ = "Development"


class Checker(object):

    '''
    Perform a series of logical and situational tests on a set of commands
    issued by the player. This class is a middle layer between the syntactic
    validation occurring in the ``engine.commander`` module and the command
    execution happening in the ``pilot.executer`` one.
    '''

    def __init__(self, pilot):
        self.pilot = pilot
        self.plane = pilot.plane

    def check(self, commands):
        '''
        Check if the requested commands can be performed or not. Return True or
        an error message. ``commands`` is a dictionary in the form:
        {command_name = (args, flags)}. Return True or a message error.
        '''
        pi = self.pilot
        pl = self.plane
        aspace = self.plane.aerospace
        cnames = set(commands.keys())
        # Reject orders if imminent collision
        if pl.tcas.state == True:
            return 'Mayday, mayday!!!'
        # Reject orders if busy
        assert not (pl.flags.busy and pl.flags.locked)  #only one of them on!
        if pl.flags.busy == True and cnames - set(['ABORT', 'SQUAWK']):
            return 'We are still performing the previous command.'
        # Reject orders other than SQUAWK if plane is locked
        if pl.flags.locked and cnames - set('SQUAWK'):
            return 'You can only SQUAWK this plane.'
        # Reject orders other than TAKEOFF or SQUAWK if plane is on ground
        if pl.flags.on_ground and not \
                        ('TAKEOFF' in cnames or cnames == set(['SQUAWK'])):
            return 'We should probably TAKEOFF first, uh?'
        # Reject orders if they contain an altitude beyond max_altitude
        if 'ALTITUDE' in cnames and \
                        commands['ALTITUDE'][0][0] > pl.max_altitude:
            return 'The target altitude is above the maximum one for our ' +\
                   'aircraft.'
        # Reject orders if they contain a speed out of speed limits (min/max)
        if 'SPEED' in cnames and \
                        not self.plane.min_speed <= commands['SPEED'][0][0] \
                                                 <= self.plane.max_speed:
            mi = U.rint(self.plane.min_speed * 3.6)
            ma = U.rint(self.plane.max_speed * 3.6)
            return 'Our speed must be between %d and %d kph!' % (mi, ma)
        # Reject LAND order if unexisting airport or runway
        if 'LAND' in cnames:
            check = pi.navigator.check_existing_runway(*commands['LAND'][0])
            if check != True:
                return check
        # Reject TAKEOFF if one of the various no-go conditions is true
        if 'TAKEOFF' in cnames:
            args, flags = commands['TAKEOFF']
            assert len(args) == 1 and len(flags) == 0
            if not pl.flags.on_ground:
                return 'We can\'t take off if we are already airborne!'
            port = aspace.airports[pl.origin]
            if args[0] not in port.runways.keys():
                return 'Uh? What runway did you say we should taxi to?'
            runway = port.runways[args[0]]
            twin = port.runways[runway['twin']]
            if not aspace.runways_manager.check_runway_free(port, twin):
                return 'Negative, that runway is currently in use.'
        # TODO: check for overshooting CLEAR.
        # If nothing else have stopped us...
        return True
