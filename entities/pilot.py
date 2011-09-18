#!/usr/bin/env python
# -*- coding: utf-8  -*-
'''
The piloting system for the ATC-NG aeroplanes.
'''

import random
from engine.settings import *
from engine.logger import log
from lib.utils import *
from math import sqrt, radians, cos, sin, tan
from lib.euclid import Vector3
from random import randint
from time import time

__author__ = "Mac Ryan"
__copyright__ = "Copyright 2011, Mac Ryan"
__license__ = "GPL v3"
#__version__ = "1.0.0"
__maintainer__ = "Mac Ryan"
__email__ = "quasipedia@gmail.com"
__status__ = "Development"


# Module variables
PING_IN_SECONDS = PING_PERIOD / 1000.0

class Lander(object):

    '''
    Container class for holding data and functions useful during the landing
    phase.
    '''

    def __init__(self, plane, port_name, rnw_name):
        self.plane = plane
        self.port_name = port_name
        self.rnw_name = rnw_name
        port = plane.aerospace.airports[port_name]
        tmp = port.runways[rnw_name]
        self.foot = tmp['location'] + port.location
        self.ils = tmp['ils']
        self.phase = None

    def __get_point_ahead(self, distance):
        '''
        Return the coordinates of a point which is X metres ahead of current
        flown point (assumes velocity vector won't change, of course).
        '''
        pl = self.plane
        return pl.position + (pl.velocity.normalized() * distance)

    def overshot(self, what):
        '''
        Return True if the plane has overshot (i.e. flown past) the ``what``
        point.
        '''
        return is_behind(self.plane.velocity, self.plane.position, what)

    def set_intersection_point(self):
        '''
        Set and return self.ip, the 2D intersection point between current
        plane heading and the ILS glide path.
        '''
        pl = self.plane
        p1 = pl.position.xy
        p2 = (pl.position + pl.velocity.normalized()*RADAR_RANGE*3).xy
        p3 = self.foot.xy
        p4 = (Vector3(*self.foot) + -self.ils.normalized()*RADAR_RANGE*3).xy
        self.ip, comment = segment_intersection(p1, p2, p3, p4)
        # If no point is due to overlapping, set the point as present position
        # of the plane.
        if comment == 'overlapping':
            self.ip = self.plane.position.xy
        # If there is a point, convert it to vector
        if self.ip:
            self.ip = Vector3(*self.ip)
        return self.ip

    def set_merge_point(self, radius):
        '''
        Set and return self.mp, the 2D point where the plane should begin
        merging into the ILS vector.
        '''
        # From the geometrical construction it is possible to observe that the
        # correct distance from the intersection point with a course for
        # merging into it is the cathetus of a triangle whose other cathetus is
        # the veering radius and whose adiacent angle is (180°-head_diff)/2, in
        # which head_diff is the difference between the current heading and the
        # target one. Since tan(angle) = opposite/adjacent the we solve for
        # adjacent with = adjacent = opposite/tan(angle)
        h1 = self.plane.heading
        h2 = v3_to_heading(self.ils)
        a1 = abs((h1-h2)%360)
        a2 = abs((h2-h1)%360)
        angle = min(a1, a2)
        angle = radians((180 - angle) / 2.0)
        dist_from_ip = radius/tan(angle)
        dist_from_plane = abs(self.ip-self.plane.position)-dist_from_ip
        self.mp = self.__get_point_ahead(dist_from_plane)
        if self.overshot(self.mp):
            self.mp = None
        return self.mp

    def set_breaking_point(self):
        '''
        Set and return self.mp, the 2D point where the plane should begin
        breaking in order to touch down at its landing_speed
        '''
        pl = self.plane
        dist = 0
        speed = pl.speed
        # To calculate the amount of space, simulate the breaking procedure
        # and measure it. Each loop is equivalent to one radar ping.
        while True:
            dist += speed * PING_IN_SECONDS
            if speed <= pl.landing_speed:
                break
            speed += pl.ground_accels[0] * PING_IN_SECONDS
        distance = abs(self.foot - self.plane.position) - dist
        self.bp = self.__get_point_ahead(distance)

    @property
    def id(self):
        '''
        Distance from the intersection point with the ILS vector.
        '''
        return abs(self.ip-self.plane.position)

    @property
    def md(self):
        '''
        Distance from the veering point for merging into the ILS.
        '''
        return abs(self.mp-self.plane.position)

    @property
    def fd(self):
        '''
        Distance from the foot of the runway.
        '''
        return abs(self.foot-self.plane.position)

    @property
    def bd(self):
        '''
        Distance from the braking point.
        '''
        return abs(self.bp-self.plane.position)

    @property
    def above_foot(self):
        '''
        Metres above the runway foot.
        '''
        return self.plane.altitude - self.foot.z

    @property
    def path_alt(self):
        '''
        Altitude of glading path at current distance from runway foot.
        '''
        return self.fd * sin(radians(SLOPE_ANGLE)) + self.foot.z


class Pilot(object):

    '''
    A class containing all the methods that alter the flying configuration of
    the aeroplane.
    '''

    # Spatial
    LEFT = CCW = -1
    RIGHT = CW = +1
    # Phases of the landing sequence
    ABORTED = 0
    INTERCEPTING = 1
    MERGING = 2
    MATCHING = 3
    GLIDING = 4
    # Radio answers
    AFFIRMATIVE_EXEC_ANSWERS = ['Roger that. Executing.',
                                'Affirmative, initiating maneuver now.',
                                'Roger, we\'re on it.',
                                'Copy that.',
                                'Okie dokie artichokie!']

    AFFIRMATIVE_QUEUE_ANSWERS = ['Roger that. Queued.',
                                 'Affirmative, command queued for execution.',
                                 'We\'ll do that as soon as possible.',
                                 'Copy that, command queued']

    @classmethod
    def set_aerospace(cls, aerospace):
        '''
        All in-game pilots operate in the same aerospace, so a class attribute
        is the cheapest solution.
        '''
        cls.aerospace = aerospace

    def __init__(self, plane):
        self.plane = plane
        self.queued_commands = []
        self.veering_direction = None
        self.target_coords = None
        self.course_towards = None
        self.lander = None

    def __abort_landing(self, msg):
        '''
        Abort landing, generating all events of the case and resetting relevant
        variables.
        '''
        # TODO:Introducing abort codes would simplify testing!
        log.info('%s aborts: %s' % (self.plane.icao, msg))
        self.say('Aborting landing: %s' % msg, ALERT_COLOUR)
        self.plane.flags.cleared_down = False
        self.lander = None

    def _abort_command(self, last_only=False):
        '''
        Abort execution of a command (or the entire command buffer).
        '''
        if last_only == True and self.queued_commands:
            self.queued_commands.pop()
            return
        self.set_target_conf_to_current()
        self.queued_commands = []
        self.veering_direction = None
        self.plane.flags.reset()

    def say(self, what, colour):
        '''
        Output a message on the console.
        '''
        self.plane.aerospace.gamelogic.say(self.plane.callsign, what, colour)

    def queue_command(self, commands):
        '''
        Add a command to the queue buffer.
        Return True on message successfully queued, false otherwise.
        '''
        # Only valid commands must be queued!
        for line in commands:
            command, args, flags = line
            if command == 'altitude':
                feasible = self.verify_feasibility(altitude=args[0])
                if feasible != True:
                    return feasible
            elif command == 'speed':
                feasible = self.verify_feasibility(speed=args[0])
                if feasible != True:
                    return feasible
        # Queuing can only be performed after commands whose implementation
        # will eventually finish...
        if self.plane.flags.circling:
            msg = 'This makes no sense... when should we stop circling?!'
            return msg
        # And before the end of the flight!
        if self.plane.flags.cleared_down:
            msg = 'Once landed, the flight is over!'
            return msg
        self.queued_commands.append(commands)
        self.say(random.choice(self.AFFIRMATIVE_QUEUE_ANSWERS), OK_COLOUR)
        return True

    def execute_command(self, commands, from_queue=False):
        '''
        Execute commands.
        Input is a list of triplets each of them in the format:
        [command, [arg1, arg2, ...], [flag1, flag2, ...]].
        Return True on message successfully executed, false otherwise.
        '''
        #FIXME: This should really be simplified and devided up, and given
        #       a proper test suite...
        self.plane.time_last_cmd = time()
        pl_flags = self.plane.flags
        if commands[0][0] != 'SQUAWK':
            self.aerospace.gamelogic.score_event(COMMAND_IS_ISSUED)
        if from_queue:
            self.say('Performing queued %s command now' %
                     commands[0][0].upper(), ALERT_COLOUR)
        # Reject orders if busy
        if pl_flags.busy == True and commands[0][0] not in ['ABORT', 'SQUAWK']:
            msg = 'Still maneuvering, please specify abort/append command'
            self.say(msg, KO_COLOUR)
            return False
        # Reject order if imminent collision
        if self.plane.tcas.state == True:
            msg = '...'
            self.say(msg, KO_COLOUR)
            return False
        # Reject order other than TAKEOFF or SQUAWK if plane is on ground
        if self.plane.position.z < 0 and commands[0][0] not \
                                in ('TAKEOFF', 'SQUAWK'):
            msg = 'We can\'t do that: we are still on the ground!'
            self.say(mas, KO_COLOUR)
            return False
        # Otherwise execute what requested
        for line in commands:
            log.info('%s executes: %s' %(self.plane.icao, line))
            command, args, cmd_flags = line
            # H, S, A data might need to be stored for takeoff...
            target = self.target_conf if not self.plane.flags.cleared_up \
                                      else self.lift_data['target_conf']
            # EXPEDITE FLAG
            if 'EXPEDITE' in cmd_flags:
                pl_flags.expedite = True
            # HEADING COMMAND
            if command == 'HEADING':
                if type(args[0]) == int:  #the argument is a heading
                    target['heading'] = args[0]
                    pass
                else:  #the argument is a location (a beacon's one)
                    self.set_course_towards(args[0])
                # Veering direction
                self.veering_direction = self.shortest_veering_direction()
                if 'LONG' in cmd_flags:
                    self.veering_direction *= -1  #invert direction
            # ALTITUDE COMMAND
            elif command == 'ALTITUDE':
                feasible = self.verify_feasibility(altitude=args[0])
                if feasible != True:
                    self.say(feasible, KO_COLOUR)
                    return False
                target['altitude'] = args[0]
            elif command == 'SPEED':
                feasible = self.verify_feasibility(speed=args[0])
                if feasible != True:
                    self.say(feasible, KO_COLOUR)
                    return False
                target['speed'] = args[0]
            # TAKE OFF COMMAND
            elif command == 'TAKEOFF':
                if self.plane.position.z >=0:
                #TODO:add also rule that excludes z<0 from tcas
                    msg = "We can't take off if we are already airborne!"
                    self.say(msg, KO_COLOUR)
                    return False
                port = self.aerospace.airports[self.plane.origin]
                if args[0].upper() not in port.runways.keys():
                    msg = "Uh? What runway did you say we should taxi to?"
                    self.say(msg, KO_COLOUR)
                    return False
                runway = port.runways[args[0]]
                twin = port.runways[runway['twin']]
                self.lift_data = dict(name = twin['name'],
                                      point = twin['location'] + port.location,
                                      velocity = -twin['ils'].normalized(),
                                      target_conf = dict(altitude = None,
                                                         speed = None,
                                                         heading = None))
                self.plane.flags.cleared_up = RUNWAY_BUSY_TIME
                self.takeoff()
            # LAND COMMAND
            elif command == 'LAND':
                feasible = self.verify_existing_runway(*args)
                if feasible != True:
                    self.say(feasible, KO_COLOUR)
                    return False
                ret = self.land(*args)
                if type(ret) != int:
                    return ret
            # CIRCLE COMMAND
            elif command == 'CIRCLE':
                param = args[0].lower()
                if param in ('L', 'LEFT', 'CCW'):
                    self.veering_direction = self.LEFT
                elif param in ('R', 'RIGHT', 'CW'):
                    self.veering_direction = self.RIGHT
                else:
                    msg = 'Unknown parameter for circle command.'
                    raise BaseException(msg)
                pl_flags.circling = True
            # ABORT COMMAND
            elif command == 'ABORT':
                self._abort_command('LASTONLY' in cmd_flags)
                return True  #need to skip setting flag.busy to True!
            # SQUAWK COMMAND
            elif command == 'SQUAWK':
                self.say('Currently heading %s, our destination is %s' %
                          (rint(self.plane.heading),
                           self.plane.destination), OK_COLOUR)
                return True  #need to skip setting flag.busy to True!
            else:
                raise BaseException('Unknown command: %s' % command)
        pl_flags.busy = True
        if not from_queue:
            self.say(random.choice(self.AFFIRMATIVE_EXEC_ANSWERS), OK_COLOUR)
        return True

    def verify_feasibility(self, speed=None, altitude=None):
        '''
        Verify if given speed and altitude are within aeroplane specifications.
        Heading is a dummy variable, used to make possible to use this method
        with any of the three attributes.
        Return True or a message error.
        '''
        r = lambda f : round(f, 4)
        #rounding is necessary for precisely matching the limits (float approx)
        if speed != None and not r(self.plane.min_speed) <= r(speed) <= \
                                 r(self.plane.max_speed):
            mi = rint(self.plane.min_speed * 3.6)
            ma = rint(self.plane.max_speed * 3.6)
            return 'Our aircraft can only cruise between %d and %d kph.' % \
                    (mi, ma)
        if altitude != None and altitude  >= self.plane.max_altitude:
            return 'The target altitude is above the maximum one for our ' +\
                   'aircraft.'
        return True

    def verify_existing_runway(self, port, runway):
        '''
        Verify that a given port/runway combo actually exist in the aerospace.
        '''
        if port not in self.aerospace.airports:
            return 'airport %s is not on the map!' % port
        if runway not in self.aerospace.airports[port].runways:
            return 'airport %s does not have runway %s!' % (port, runway)
        return True

    def set_target_conf_to_current(self):
        '''
        Set the target configuration for the current one.
        '''
        self.target_conf = self.plane.get_current_configuration()

    def test_target_conf_reached(self):
        '''
        Return True if the current plane configuration matches the target one.
        '''
        tc = self.target_conf
        return self.plane.heading == tc['heading'] and \
               self.plane.altitude == tc['altitude'] and \
               self.plane.speed == tc['speed']

    def shortest_veering_direction(self):
        '''
        Return self.LEFT or self.RIGHT according to whatever the shortest
        veering to a certain course is.
        '''
        theta = (self.plane.heading - self.target_conf['heading']) % 360
        return self.LEFT if theta < 180 else self.RIGHT

    def get_intersection_point(self, vector, point):
        '''
        Return the intersection point between the projected plane trajectory
        and the line defined by `vector` applied to `point`.
        '''
        if type(point) in (tuple, list):
            point = Vector2(*point)
        p1 = self.plane.position.xy
        p2 = (self.plane.position + self.plane.velocity).xy
        p3 = point.xy
        p4 = (point + vector).xy
        return line_intersection(p1, p2, p3, p4)

    def get_veering_radius(self, veer_type, speed=None):
        '''
        Return the veering radius at given speed.
        `speed` defaults to current plane speed.
        `type` can be: normal, expedite, emergency.
        '''
        if speed == None:
            speed = self.plane.speed
        # Given that V = ω * r...
        return speed / self.get_veering_angular_velocity(veer_type, speed)

    def get_veering_angular_velocity(self, veer_type, speed=None):
        '''
        Return the veering angular velocity at given linear speed.
        `speed` defaults to current plane speed.
        `type` can be: normal, expedite, emergency.

        The turn radius is calculated according to maximum g's exerted on the
        passengers. These are:
            - Normal flight: 1.15g (30° bank angle)
            - Quick turn:    1.41g (45° bank angle)
            - Emergency:     2.00g (60° bank angle)
        Given that there is always a vertical component of 1g (gravity), the
        above figures must be the resulting of centrifugal (C) and gravity (G)
        accelerations combined.
            Given total acceleration (T), Pitagora says T²=G²+C². This
        transalates in C²=T²-G² → C=sqrt(T²-G²).
            But C=ω²r and ω=V/r so C=V²/(V/ω) → C=Vω → ω=C/V
        '''
        if speed == None:
            speed = self.plane.speed
        if veer_type == 'normal':
            max_manouvering_g = 1.15
        elif veer_type == 'expedite':
            max_manouvering_g = 1.41
        elif veer_type == 'emergency':
            max_manouvering_g = self.plane.max_g
        else:
            raise BaseException('Unknown veer type')
        g_to_mks = lambda x : G_GRAVITY * x
        acc_module = sqrt(g_to_mks(max_manouvering_g)**2-g_to_mks(1)**2)
        return acc_module/speed

    def takeoff(self, runway=None):
        '''
        Manage the take off procedure
        '''
        if self.plane.flags.cleared_up <= 0:
            log.info('%s is taking off from %s %s' % (self.plane.icao,
                                  self.plane.origin, self.lift_data['name']))
            self.plane.position = self.lift_data['point']
            self.plane.velocity = self.lift_data['velocity'] * \
                                  self.plane.landing_speed
            target = self.target_conf
            data = self.lift_data['target_conf']
            target['altitude'] = data['altitude'] if data['altitude'] \
                                                  else self.plane.max_altitude
            target['speed'] = data['speed'] if data['speed'] \
                                               else self.plane.max_speed
            target['heading'] = data['heading'] if data['heading'] \
                                               else self.plane.heading
            del self.lift_data
            self.plane.flags.cleared_up = False
            self.plane.flags.busy = True
        else:
            self.plane.flags.cleared_up -= PING_IN_SECONDS

    def land(self, port_name=None, rnw_name=None):
        '''
        Guide a plane towards the ILS descent path and then makes it land.
        Return the phase of the landing sequence.
        '''
        assert not (port_name == rnw_name == None and not self.lander)
        pl = self.plane
        # The first time the land() method is called, generates a Lander()
        # object. This is a also a good place for early returns if we
        # already know it's impossible to land from current plane position
        if not self.lander:
            l = Lander(pl, port_name, rnw_name)
            # EARLY RETURN - Maximum incidence angle into the ILS is 60°
            ils_heading = v3_to_heading(l.ils)
            ils_heading = v3_to_heading(l.ils)
            boundaries = [(ils_heading-60)%360, (ils_heading+60)%360]
            if not heading_in_between(boundaries, pl.heading):
                msg = 'ILS heading must be within 60 degrees ' \
                      'from current heading'
                return self.__abort_landing(msg)
            # EARLY RETURN - No possible intersection (the RADAR_RANGE*3
            # ensures that the segments to test for intersection are long enough.
            if not l.set_intersection_point():
                msg = 'The ILS does not intersect the plane current heading'
                return self.__abort_landing(msg)
            # EARLY RETURN - Although the intersection is ahead of the plane,
            # it's too late to merge into the ILS vector
            #TODO:BUG - doesn't work with 'expedite'! :(
            if l.set_merge_point(self.get_veering_radius('normal')) < 0:
                msg = 'We are too close to the ILS to merge into it'
                return self.__abort_landing(msg)
            # LANDING IS NOT EXCLUDED A PRIORI...
            l.phase = self.INTERCEPTING
            self.lander = l
            pl.flags.cleared_down = True
            pl.flags.busy = True
        else:
            l = self.lander
        if l.phase == self.INTERCEPTING:
            if l.overshot(l.mp):
                self.set_course_towards(l.foot.xy)
                l.phase = self.MERGING
            log.debug('%s INTERCEPTING: md=%s fd=%s' % (pl.icao, l.md, l.fd))
        elif l.phase == self.MERGING:
            if self.course_towards == None:
                l.phase = self.MATCHING
            log.debug('%s MERGING: head=%s t_head= %s fd=%s' % (pl.icao,
                      pl.heading, self.target_conf['heading'], l.fd))
        elif l.phase == self.MATCHING:
            secs_to_foot = l.fd / pl.speed
            # Abort if the plane is too fast to descend
            if abs(secs_to_foot * pl.climb_rate_limits[0]) < l.above_foot:
                msg = 'Plane is flying too fast to lose enough altitude'
                return self.__abort_landing(msg)
            # If the delta to the path is less than the climbing/descending
            # capabilities of the aeroplane, consider it on slope...
            path_alt = l.path_alt
            alt_diff = path_alt - pl.altitude  #negative -> descend!
            if alt_diff < 0 and alt_diff > pl.climb_rate_limits[0] or \
               alt_diff > 0 and alt_diff < pl.climb_rate_limits[1]:
                pl.position.z = path_alt
                l.phase = self.GLIDING
                l.set_breaking_point()
                if l.overshot(l.bp):
                    msg = 'Plane too fast to slow down to landing speed'
                    self.__abort_landing(msg)
            # ...otherwise tell it to climb/descend!!
            else:
                self.target_conf['altitude'] = path_alt
            log.debug('%s MATCHING: alt=%s path_alt=%s delta=%s fd=%s' %
                      (pl.icao, pl.altitude, path_alt, alt_diff, l.fd))
        elif l.phase == self.GLIDING:
            # Abort if the plane is too fast to slow to landing speed
            if l.overshot(l.bp):
                self.target_conf['speed'] = pl.landing_speed
            if pl.position.z <= l.foot.z:
                if pl.destination == l.port_name:
                    msg = 'Thank you tower, we\'ve hit home. Over and out!'
                    self.say(msg, OK_COLOUR)
                    pl.terminate(PLANE_LANDS_CORRECT_PORT)
                else:
                    msg = 'Well, well... we just landed at the WRONG airport!'
                    self.say(msg, KO_COLOUR)
                    pl.terminate(PLANE_LANDS_WRONG_PORT)
                return
            ticks = 1.0 * l.fd / self.target_conf['speed'] / PING_IN_SECONDS
            z_step = 1.0 * l.above_foot / ticks
            self.target_conf['altitude'] -= z_step
            log.debug('%s GLIDING: footalt=%s speed=%s t_speed=%s bd=%s fd=%s'
                      % (pl.icao, l.above_foot, pl.speed,
                         self.target_conf['speed'], l.bd, l.fd))
        return l.phase

    def veer(self):
        '''
        Make the plane turn.
        '''
        # The tightness of the curve is given by the kind of situation the
        # aeroplane is in.
        if self.plane.flags.expedite or self.plane.flags.cleared_down:
            veer_type = 'expedite'
        if self.plane.tcas.state == True:
            veer_type = 'emergency'
        else:
            veer_type = 'normal'
        # Unless already specified, set the veering_direction
        if not self.veering_direction:
            self.veering_direction = self.shortest_veering_direction()
        abs_ang_speed = self.get_veering_angular_velocity(veer_type)
        angular_speed = abs_ang_speed * -self.veering_direction
        rotation_axis = Vector3(0,0,1)
        self.plane.velocity = self.plane.velocity.rotate_around(rotation_axis,
                             angular_speed*PING_IN_SECONDS)

    def ground_distance(self, a, b):
        '''
        Return the ground distance between two 3D vectors.
        '''
        a_pos = Vector2(*a.xy)
        b_pos = Vector2(*b.xy)
        return abs(a_pos - b_pos)

    def set_course_towards(self, coords=None):
        '''
        Set the target heading to a direct intercept towards the given
        coordinates.
           There is no guarantee the plane will be capable to
        navigate towards that point (if the turn radius is too tight it will
        overshoot the target).
           The function can be called without arguments if the plane has
        already been instructed to reach a given point.
        '''
        # No coords only if coords have been passed before!
        assert not (coords == None and not self.course_towards)
        if not coords:
            coords = self.course_towards
        else:
            self.course_towards = coords
        delta = Vector3(*coords) - self.plane.position
        new_head = v3_to_heading(delta)
        if new_head != self.plane.heading:
            self.target_conf['heading'] = new_head
        else:
            self.course_towards = None
            self.veering_direction = None

    def update(self):
        '''
        Modify aeroplane configuration according to pilot's instructions.
        '''
        # Speed-up by caching property call
        pl = self.plane
        # Store initial values [for "post_update_ops"]
        previous_altitude = pl.altitude
        previous_heading = pl.heading
        previous_speed = pl.speed
        # Run the TCAS subroutine, which can override any order given to the
        # pilot in case of risk of imminent collision
        pl.tcas.update()
        # Circling action affects heading only (can be combined with changes in
        # speed and/or altitude)
        if pl.flags.circling:
            if self.veering_direction == self.LEFT:
                target = (pl.heading - 179) % 360
            elif self.veering_direction == self.RIGHT:
                target = (pl.heading + 179) % 360
            else:
                raise BaseException('Veering direction not set for circling.')
            self.target_conf['heading'] = target
        # Landing loop (affects all parameters at various landing phases)
        if pl.flags.cleared_down:
            self.land()
        # Take off (affects all parameters at various landing phases)
        if type(pl.flags.cleared_up) != bool:  #can be 0 seconds!!!
            self.takeoff()
        # Course towards action affects heading only, can be set by landing
        if self.course_towards:
            self.set_course_towards()
        if pl.heading != self.target_conf['heading']:
            self.veer()
        if pl.altitude != self.target_conf['altitude']:
            # Descending or ascending?
            index = pl.altitude < self.target_conf['altitude']
            z_acc = pl.climb_rate_accels[index]*PING_IN_SECONDS
            # Non expedite climbs / takeoffs / landings are limited at 50% of
            # maximum rate.
            if not (pl.flags.expedite or \
                    pl.flags.cleared_down or pl.flags.cleared_up):
                z_acc *= 0.5
            # Acceleration cannot produce a climb rate over or under the limits
            min_, max_ = pl.climb_rate_limits
            if min_ <= pl.velocity.z + z_acc <= max_:
                pl.velocity.z += z_acc
            # if out of boundaries, uses min and max
            else:
                pl.velocity.z = max_ if index else min_
        if pl.speed != self.target_conf['speed']:
            index = pl.speed < self.target_conf['speed']
            gr_acc = pl.ground_accels[index]*PING_IN_SECONDS
            # Non expedite accelerations are limited at 50% of maximum accels
            if not (pl.flags.expedite or \
                   pl.flags.cleared_down or pl.flags.cleared_up):
                gr_acc *= 0.5
            norm_velocity = Vector3(*pl.velocity.xy).normalized()
            acc_vector = norm_velocity * gr_acc
            # Acceleration cannot produce a speed over or under the limits
            if pl.flags.cleared_down:
                min_, max_ = pl.landing_speed, pl.max_speed
            else:
                min_, max_ = pl.min_speed, pl.max_speed
            maybe = pl.speed + gr_acc
            # Testing for the sign of gr_acc allows to have a taking off plane
            # at takeoff speed that is below its minimum flight speed, but
            # prevent a slowing plane to go pass it's minimum speed.
            if (maybe <= min_ and gr_acc < 0):
                pl.velocity = norm_velocity * min_
            elif (maybe >= max_ and gr_acc > 0):
                pl.velocity = norm_velocity * max_
            else:
                pl.velocity += acc_vector
        pl.position += pl.velocity*PING_IN_SECONDS
        ###################
        # POST-UPDATE OPS #
        ###################
        # Heading dampener (act on velocity vector)
        t_head = self.target_conf['heading']
        if heading_in_between((previous_heading, pl.heading), t_head):
            mag = abs(Vector2(*pl.velocity.xy))
            theta = radians(90-t_head)
            pl.velocity.x = cos(theta)*mag
            pl.velocity.y = sin(theta)*mag
            self.target_conf['heading'] = pl.heading  #Fixes decimal approx.
            self.course_towards = None  #Make sure new heading is re-caculated
            self.veering_direction = None
        # Speed dampener (act on velocity vector)
        t_speed = self.target_conf['speed']
        if in_between((previous_speed, pl.speed), t_speed):
            mag = t_speed
            # this is ground speed, so we want to normalise that without
            # affecting the z component...
            saved_z = pl.velocity.z
            pl.velocity = Vector3(*pl.velocity.xy).normalized() * t_speed
            pl.velocity.z = saved_z
            self.target_conf['speed'] = pl.speed  #Fixes decimal approx.
        # Update onboard instruments, as the following dampener will modify
        # the data they would access
        pl.update_instruments()
        # Altitude dampener (act on position vector)
        t_alt = self.target_conf['altitude']
        if in_between((previous_altitude, pl.altitude), t_alt):
            pl.position.z = t_alt
            pl.velocity.z = 0
        # Update busy flag or start execution of next command
        fl = pl.flags
        if self.test_target_conf_reached() and not \
                      (fl.cleared_beacon or fl.cleared_down or fl.cleared_up):
            fl.busy = False  #execute commands will check this flag
            fl.expedite = False  #reset
            if self.queued_commands:
                self.execute_command(self.queued_commands.pop(0), True)
