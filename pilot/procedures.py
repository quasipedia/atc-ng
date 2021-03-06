#!/usr/bin/env python
# -*- coding: utf-8  -*-
'''
The procedures a pilot can perform, such take offs or landings.

A procedure in ATC-NG is defined as an order that requires the pilot to perform
different actions at different stages of it.
'''

import lib.utils as U
from engine.settings import settings as S
from lib.euclid import Vector3
from engine.logger import log
from navigator import Lander

__author__ = "Mac Ryan"
__copyright__ = "Copyright ©2011, Mac Ryan"
#__credits__ = ["Name Lastname", "Name Lastname"]
__license__ = "GPL v3"
#__version__ = "<dev>"
#__date__ = "<unknown>"
__maintainer__ = "Mac Ryan"
__email__ = "quasipedia@gmail.com"
__status__ = "Development"


class GeneralProcedure(object):

    '''
    Virtual class to serve as ancestor for the various procedures.

    The following methods must be implemented in childred classes:
    * ``_initiate`` - called at object creation
    * ``_update`` - called at any radar ping
    '''

    def __init__(self, pilot, *args):
        '''
        Standard setup operations. Calls the ``self.initiate(args)`` method,
        which should be imlemented in children classes.

        ``args`` can be different data for different procedures.
        '''
        self.pilot = pilot
        self.plane = pilot.plane
        pilot.status['procedure'] = self
        self._initiate(*args)

    def _check_expedite(self, commands):
        '''
        Return True if any of the commands have the expedite flag.
        '''
        for value in commands.values():
            if 'EXPEDITE' in value[1]:
                return True
        return False


class Avert(GeneralProcedure):
    '''
    Procedure to avert a given 3D point on the map.
    This procedure is triggered by the TCAS in response to a proximity warning
    (either by an aeroplane or by ground).
    '''

    def _initiate(self, point):
        '''
        Automatically called by ancestor class upon ``__init__``
        '''
#        assert isinstance(point, Vector3)
#        for k, v in self.pilot.navigator.get_aversion_course(point):
#            setattr(self.pilot.target_conf, k, v)
#        log.info('%s is averting point %s' % (self.plane.icao, point.xyz))

    def update(self):
        '''
        The procedure will terminate when the TCAS will be off.
        '''
#        if self.plane.tcas.state == False:
#            self.pilot.status['procedure'] = None


class Bye(GeneralProcedure):
    '''
    Procedure whose only purpose is to keep the radar target displayed as busy.
    '''

    def _initiate(self, commands):
        '''
        Automatically called by ancestor class upon ``__init__``
        '''
        self.pilot.executer.process_commands(commands)
        self.pilot.say('Good-bye tower!', S.OK_COLOUR)

    def update(self):
        '''
        The procedure will terminate only upon an ``ABORT`` command.
        '''
        pass


class Circle(GeneralProcedure):

    '''
    Procedure to hold the plane circling in the same direction.
    '''

    def _initiate(self, commands):
        '''
        Automatically called by ancestor class upon ``__init__``
        '''
        self.pilot.executer.process_commands(commands)
        st = self.pilot.status
        param = commands['CIRCLE'][0][0]
        if param in ('L', 'LEFT', 'CCW'):
            st['veer_dir'] = S.LEFT
        elif param in ('R', 'RIGHT', 'CW'):
            st['veer_dir'] = S.RIGHT
        else:
            msg = 'Unknown parameter for circle command.'
            raise BaseException(msg)
        if self._check_expedite(commands):
            st['haste'] = 'expedite'
        log.info('%s is circling %s' % (self.plane.icao, st['veer_dir']))


    def update(self):
        '''
        Does nothing, as the circling must be explicitly interrupted with an
        ABORT command
        '''
        assert self.pilot.status['veer_dir'] in (S.LEFT, S.RIGHT)
        if self.pilot.status['veer_dir'] == S.LEFT:
            target = (self.plane.heading - 179) % 360
        elif self.pilot.status['veer_dir'] == S.RIGHT:
            target = (self.plane.heading + 179) % 360
        self.pilot.target_conf.heading = target


class Clear(GeneralProcedure):

    '''
    Procedure to make the plane fly over a given point on the map.
    '''

    def _initiate(self, commands):
        '''
        Automatically called by ancestor class upon ``__init__``
        '''
        # Preliminary check: is the beacon in range?
        point = commands['CLEAR'][0][0]
        veer_type = 'expedite' if 'EXPEDITE' in commands['CLEAR'][1] else None
        if not self.pilot.navigator.check_reachable(point, veer_type) \
           and 'SPEED' not in commands \
           or ('SPEED' in commands \
               and commands['SPEED'][0][0] > self.plane.speed):
            msg = 'The target waypoint is too close for us to fly over it!'
            return self._abort_clear(msg)
        if self._check_expedite(commands):
            self.pilot.status['haste'] = 'expedite'
        # Head towards the point
        commands['HEADING'] = commands['CLEAR']
        self.pilot.executer.process_commands(commands)
        self.target = point
        log.info('%s is clearing towards %s' % (self.plane.icao, point))

    def _abort_clear(self, msg):
        '''
        Abort clear, generating all events of the case and resetting relevant
        variables.
        '''
        log.info('%s aborts: %s' % (self.plane.icao, msg))
        self.pilot.say('Aborting clear command: %s' % msg, S.ALERT_COLOUR)
        self.pilot.status['procedure'] = None
        self.pilot.set_target_conf_to_current()
        self.pilot.adjust_to_valid_FL()

    def update(self):
        '''
        Operations that must be performed when the radar pings.
        '''
        # If the plane has reached it's target...
        if self.pilot.target_conf.heading == self.plane.heading \
            and self.pilot.navigator.check_overshot(self.target):
                msg = 'We just flown over the beacon, awiting new orders!'
                self.pilot.say(msg, S.ALERT_COLOUR)
                self.pilot.status['procedure'] = None
        # If the plane is now in a configuration that doesn't allow it to
        # reach the target point...
        if not self.pilot.navigator.check_maybe_reachable(self.target):
            msg = 'We are flying too fast to veer in time!'
            self._abort_clear(msg)
        # ...otherwise do absolutely nothing!

class Land(GeneralProcedure):

    '''
    Procedure to make the plane land.
    '''

    # PHASES OF THE LANDING SEQUENCE
    ABORTED = 0
    INTERCEPTING = 1
    MERGING = 2
    MATCHING = 3
    GLIDING = 4
    TAXIING = 5

    def _initiate(self, commands):
        '''
        Automatically called by ancestor class upon ``__init__``
        '''
        pl = self.plane
        pi = self.pilot
        port_name, rnwy_name = commands['LAND'][0]
        self.lander = Lander(self.pilot, port_name, rnwy_name)
        l = self.lander
        # EARLY RETURN - Maximum incidence angle into the ILS is 60°
        ils_heading = U.v3_to_heading(l.ils)
        boundaries = [(ils_heading - S.ILS_TOLERANCE)%360,
                      (ils_heading + S.ILS_TOLERANCE)%360]
        if not U.heading_in_between(boundaries, pl.heading):
            msg = 'ILS heading must be within %s degrees ' \
                  'from current heading' % S.ILS_TOLERANCE
            return self._abort_landing(msg)
        # EARLY RETURN - No possible intersection (the RADAR_RANGE*3
        # ensures that the segments to test for intersection are long enough.
        if not l.set_intersection_point():
            msg = 'The ILS does not intersect the plane current heading'
            return self._abort_landing(msg)
        # EARLY RETURN - Although the intersection is ahead of the plane,
        # it's too late to merge into the ILS vector
        type_ = pi.status['haste']
        if l.set_merge_point(pi.navigator.get_veering_radius(type_)) < 0:
            msg = 'We are too close to the ILS to merge into it'
            return self._abort_landing(msg)
        # LANDING IS NOT EXCLUDED A PRIORI...
        log.info('%s started landing procedure, destination: %s %s' %
                                (self.plane.icao, port_name, rnwy_name))
        # SETTING PERSISTENT DATA
        if self._check_expedite(commands):
            pi.status['haste'] = 'expedite'
        self.phase = self.INTERCEPTING
        self.lander = l

    def _abort_landing(self, msg):
        '''
        Abort landing, generating all events of the case and resetting relevant
        variables.
        '''
        # TODO: Introducing abort codes would simplify testing!
        log.info('%s aborts: %s' % (self.plane.icao, msg))
        self.pilot.say('Aborting landing: %s' % msg, S.ALERT_COLOUR)
        # Marked runway as free
        if self.lander and self.lander.taxiing_data:
            self.pilot.aerospace.runways_manger.release_runway(self.plane)
        self.pilot.status['procedure'] = None
        self.pilot.set_target_conf_to_current()
        self.pilot.adjust_to_valid_FL()

    def update(self):
        '''
        Guide a plane towards the ILS descent path and then makes it land.
        Return the phase of the landing sequence.
        '''
        pl = self.plane
        pi = self.pilot
        l = self.lander
        assert self.phase in (self.ABORTED, self.INTERCEPTING, self.MERGING,
                              self.MATCHING, self.GLIDING, self.TAXIING)
        if self.phase == self.INTERCEPTING:
            #BUG: if command is given too late the plane won't manage to
            #     turn into the vector
            log.debug('%s INTERCEPTING: md=%s fd=%s' % (pl.icao, l.md, l.fd))
            if pi.navigator.check_overshot(l.mp) == True:
                pi.target_conf.heading = l.foot
                self.phase = self.MERGING
        if self.phase == self.MERGING:
            log.debug('%s MERGING: head=%s t_head= %s fd=%s' % (pl.icao,
                      pl.heading, pi.target_conf.heading, l.fd))
            if pl.heading == pi.target_conf.heading:
                self.phase = self.MATCHING
        if self.phase == self.MATCHING:
            path_alt = l.path_alt
            alt_diff = path_alt - pl.altitude  #negative -> descend!
            log.debug('%s MATCHING: alt=%s path_alt=%s delta=%s fd=%s' %
                      (pl.icao, pl.altitude, path_alt, alt_diff, l.fd))
            secs_to_foot = l.fd / pl.speed
            # Abort if the plane is too fast to descend
            if abs(secs_to_foot * pl.climb_rate_limits[0]) < l.above_foot:
                msg = 'Plane is flying too fast to lose enough altitude'
                return self._abort_landing(msg)
            # If the delta to the path is less than the climbing/descending
            # capabilities of the aeroplane, consider it on slope...
            if alt_diff < 0 and alt_diff > pl.climb_rate_limits[0] or \
               alt_diff > 0 and alt_diff < pl.climb_rate_limits[1]:
                pl.position.z = path_alt
                self.phase = self.GLIDING
                l.set_breaking_point()
                if pi.navigator.check_overshot(l.bp):
                    msg = 'Plane too fast to slow down to landing speed'
                    self._abort_landing(msg)
            # ...otherwise tell it to climb/descend!!
            else:
                pi.target_conf.altitude = path_alt
        elif self.phase == self.GLIDING:
            log.debug('%s GLIDING: footalt=%s speed=%s t_speed=%s bd=%s fd=%s'
                      % (pl.icao, l.above_foot, pl.speed,
                         pi.target_conf.speed, l.bd, l.fd))
            # Abort if the plane is too fast to slow to landing speed
            if pi.navigator.check_overshot(l.bp):
                pi.target_conf.speed = pl.landing_speed
            # Make decision if below minimum altitude
            if not l.taxiing_data and l.above_foot <= S.DECISION_ALTITUDE:
                l.make_decision()
            ticks = 1.0 * l.fd / pi.target_conf.speed / S.PING_IN_SECONDS
            z_step = 1.0 * l.above_foot / ticks
            pi.target_conf.altitude -= z_step
            if pl.position.z <= l.foot.z \
               or pi.navigator.check_overshot(l.foot):
                pl.flags.on_ground = True
                self.phase = self.TAXIING
                pi.target_conf.speed = l.taxiing_data['speed']
                if pl.destination == l.port.iata:
                    msg = 'Thank you tower, we\'ve hit home. Over and out!'
                    pi.say(msg, S.OK_COLOUR)
                else:
                    msg = 'Well, well... we just landed at the WRONG airport!'
                    pi.say(msg, S.KO_COLOUR)
        elif self.phase == self.TAXIING:
            log.debug('%s TAXIING: speed=%s fd=%s' % (pl.icao, pl.speed, l.fd))
            l.taxiing_data['timer'] -= S.PING_IN_SECONDS
            if l.taxiing_data['timer'] <= 0:
                if pl.destination == l.port.iata:
                    pl.terminate(S.PLANE_LANDS_CORRECT_PORT)
                else:
                    pl.terminate(S.PLANE_LANDS_WRONG_PORT)
        return self.phase


class TakeOff(GeneralProcedure):

    '''
    Procedure to make the plane take off.
    '''

    # PHASES OF THE TAKE OFF SEQUENCE
    ACCELERATING = 0
    CLIMBING = 1
    HEADING = 2

    def _initiate(self, commands):
        '''
        Automatically called by ancestor class upon ``__init__``
        '''
        pl = self.plane
        aspace = pl.aerospace
        r_name = commands['TAKEOFF'][0][0]
        port = aspace.airports[pl.origin]
        runway = port.runways[r_name]
        twin = port.runways[runway['twin']]
        start_point = runway['location'] + port.location
        vector = Vector3(*(-twin['ils']).normalized().xy)
        self.end_of_runway = twin['location'] + port.location
        # SAVE PROCEDURE' PERSISTENT DATA
        h = commands['HEADING'][0][0] if 'HEADING' in commands \
                                else U.v3_to_heading(vector)
        a = commands['ALTITUDE'][0][0] if 'ALTITUDE' in commands \
                                else pl.max_altitude
        self.target_heading = h
        self.target_altitude = a
        self.timer = S.RUNWAY_BUSY_TIME
        # LET'S ROLL!!
        pl.position = start_point.copy()
        aspace.runways_manager.use_runway(port, twin, pl)
        pl.flags.locked = True
        # Give 1 m/s speed and update target to set the heading/sprite icon
        pl.velocity = vector.copy()
        self.pilot.set_target_conf_to_current()
        # Set max acceleration
        self.pilot.target_conf.speed = \
            commands['SPEED'][0][0] if 'SPEED' in commands else pl.max_speed
        self.phase = self.ACCELERATING
        # LOG
        log.info('%s is taking off from %s %s' %
                                    (pl.icao, pl.origin, runway['name']))
        if self._check_expedite(commands):
            self.pilot.status['haste'] = 'expedite'

    def update(self):
        '''
        Operations that must be performed when the radar pings.
        '''
        assert self.phase in (self.ACCELERATING, self.CLIMBING, self.HEADING)
        pl = self.plane
        pi = self.pilot
        if self.phase == self.ACCELERATING:
            if pl.speed > pl.landing_speed:
                pi.target_conf.altitude = self.target_altitude
                pl.flags.on_ground = False
                self.phase = self.CLIMBING
                log.info('%s is lifting off' % pl.icao)
            else:
                if pi.navigator.check_overshot(self.end_of_runway):
                    log.info('%s crashed due to too short runway' % pl.icao)
                    pl.terminate(S.PLANE_CRASHES)
        if self.phase == self.CLIMBING:
            if pi.navigator.check_overshot(self.end_of_runway):
                pi.target_conf.heading = self.target_heading
                self.phase = self.HEADING
                log.info('%s is setting post-lift-off course' % pl.icao)
        if self.timer <= 0 and self.phase == self.HEADING:
            pl.aerospace.runways_manager.release_runway(pl)
            pl.flags.locked = False
            pi.status['procedure'] = None
            log.info('%s has terminated takeoff, runway free' % pl.icao)
        self.timer -= S.PING_IN_SECONDS
