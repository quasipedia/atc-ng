#!/usr/bin/env python
# -*- coding: utf-8  -*-
'''
The classes needed to process orders.
'''

from time import time

import lib.utils as U
import procedures
from engine.settings import settings as S
from engine.logger import log

__author__ = "Mac Ryan"
__copyright__ = "Copyright ©2011, Mac Ryan"
#__credits__ = ["Name Lastname", "Name Lastname"]
__license__ = "GPL v3"
#__version__ = "<dev>"
#__date__ = "<unknown>"
__maintainer__ = "Mac Ryan"
__email__ = "quasipedia@gmail.com"
__status__ = "Development"


class Executer(object):

    '''
    Docstring.
    '''

    PROCEDURES = dict(CIRCLE = procedures.Circle,
                      CLEAR = procedures.Clear,
                      LAND = procedures.Land,
                      TAKEOFF = procedures.TakeOff)

    def __init__(self, pilot):
        self.pilot = pilot
        self.plane = pilot.plane

    def abort(self):
        '''
        Abort execution of a command / procedure.
        '''
        self.pilot._reset_status()
        self.pilot._set_target_conf_to_current()
        self.plane.flags.reset()
        self.pilot._adjust_to_valid_FL()

    def process_commands(self, commands):
        '''
        Process commands.

        This is a "subroutine" of ``execute`` which is also called by some of
        the procedures. This is such that is possible to process commands
        without triggering score events and setting flags (as it happens with
        ``execute()``).

        This method will silently pass if the command name has not been
        recognised. This is to allow the method to process set of commands that
        also contains *procedures* (such LAND, TAKEOFF, etc...).
        '''
        pi = self.pilot
        pl = self.plane
        for cname, (args, flags) in commands.items():
            log.info('%s executes: %s' %
                     (pl.icao, ' '.join((cname, repr(args), repr(flags)))))
            # PROCESS COMMANDS
            # Since flags are "universal" across commands (they all do the same
            # thing if they are called the same), it is possible to process
            # them separately.
            if cname == 'HEADING':
                assert len(args) == 1
                pi.target_conf.heading = args[0]
                pi.status['veer_dir'] = \
                                pi.navigator.get_shortest_veering_direction()
            elif cname == 'ALTITUDE':
                pi.target_conf.altitude = args[0]
            elif cname == 'SPEED':
                pi.target_conf.speed = args[0]
            elif cname == 'ABORT':
                self.abort()
            elif cname == 'SQUAWK':
                if pl.flags.on_ground:
                    pi.say('Currently at airport %s, our destination is %s' %
                              (pl.origin, pl.destination), S.OK_COLOUR)
                else:
                    pi.say('Currently heading %s, our destination is %s' %
                          (U.rint(pl.heading), pl.destination), S.OK_COLOUR)
            elif cname == 'BYE':
                pi.status['bye'] = True
                pi.say('Good-bye tower!')
            else:
                log.debug('process_commands() ignored: %s' % cname)
            # PROCESS FLAGS
            # Flags with the same name have the same meaning and therefore
            # can be processed independently from the command they are
            # associated with. Since they can modify the value set by their
            # command, they must follow the command processing
            if 'EXPEDITE' in flags:
                pi.status['haste'] = 'expedite'
            if 'LONG' in flags:
                pi.status['veer_dir'] *= -1  #invert direction

    def execute(self, commands):
        '''
        Execute commands.
        Input is a dictionary in the form: {command_name = (args, flags)}
        NOTE that this method assumes the feasibility of the order has been
        already verified by ``pilot.checker.Checker()``. For this reason, no
        value is returned.
        '''
        pl = self.plane
        pi = self.pilot
        # Update last order time and score event
        pl.time_last_cmd = time()
        cnames = set(commands.keys())
        if 'SQUAWK' not in cnames:
            pi.aerospace.gamelogic.score_event(S.COMMAND_IS_ISSUED)
        # PROCEDURES
        proc_name = cnames & set(self.PROCEDURES.keys())
        if proc_name:
            assert len(proc_name) == 1  #only one procedure at a time!
            self.PROCEDURES[proc_name.pop()](pi, commands)
        # COMMANDS
        else:
            self.process_commands(commands)
        pl.flags.busy = True
