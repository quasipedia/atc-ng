#!/usr/bin/env python
# -*- coding: utf-8  -*-
'''
The piloting system for the ATC-NG aeroplanes.
'''

from engine.settings import *
from lib.utils import *
from math import sqrt, radians, cos, sin, tan
from lib.euclid import Vector3
from random import randint
from time import time

__author__ = "Mac Ryan"
__copyright__ = "Copyright 2011, Mac Ryan"
#__credits__ = ["Name Lastname", "Name Lastname"]
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
        port = plane.aerospace.aeroports[port_name]
        tmp = port.runways[rnw_name]
        self.foot = tmp['location'] + port.location
        self.ils = tmp['ils']
        self.phase = None

    def set_ip(self):
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

    def set_md(self, radius):
        '''
        Set self.md_from_ip, the distance of the veering point from self.ip.
        Veering point: point in which the plane must initiate veering in order
        to merge into the ILS vector.
            Return self.md!!! [the distance between the plane and such point]
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
        self.md_from_ip = radius/tan(angle)
        return self.md

    def set_bd(self):
        '''
        Set self.bd_from_ft, the distance of the braking point from self.foot.
        Braking point: distance at which the plane must activate airbrakes to
        hit the foot of the runway at landing speed.
            Return self.bd!!! [the distance between the plane and such point]
        '''
#        pl = self.plane
#        delta_speeds = 1.0 * pl.speed - pl.landing_speed
#        secs = abs(delta_speeds / pl.ground_accels[0])
#        # The integral over time for a lineraly decreasing function is the
#        # area of the triangle.
#        self.bd_from_ft = secs * (delta_speeds /2  + pl.landing_speed)
#        print "BD --> %s" % self.bd
#        return self.bd
        pl = self.plane
        dist = 0
        speed = pl.speed
        # To calculate the amount of space, simulate the breaking procedure
        # and measure it. Each loops is equivalent to one radar ping.
        while True:
            dist += speed * PING_IN_SECONDS
            if speed <= pl.landing_speed:
                self.bd_from_ft = dist
                return self.bd
            speed += pl.ground_accels[0] * PING_IN_SECONDS

    @property
    def md(self):
        '''
        Distance from the veering point for merging into the ILS.
        '''
        pl_from_ip = abs(self.ip-self.plane.position)
        return pl_from_ip - self.md_from_ip

    @property
    def fd(self):
        '''
        Distance from the foot of the runway.
        '''
        return ground_distance(self.foot, self.plane.position)

    @property
    def bd(self):
        '''
        Distance from the braking point.
        '''
        return self.fd - self.bd_from_ft

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
        #TODO:BUG - landing abortions don't always "say" what they should
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
        self.say(randelement(self.AFFIRMATIVE_QUEUE_ANSWERS), OK_COLOUR)
        return True

    def execute_command(self, commands):
        '''
        Execute commands.
        Input is a list of triplets each of them in the format:
        [command, [arg1, arg2, ...], [flag1, flag2, ...]].
        Return True on message successfully executed, false otherwise.
        '''
        self.plane.time_last_cmd = time()
        # Speedup hack
        pl_flags = self.plane.flags
        # Points event
        if commands[0][0] != 'squawk':
            self.aerospace.gamelogic.score_event(COMMAND_IS_ISSUED)
        # Reject orders if busy
        if pl_flags.busy == True and commands[0][0] != 'abort':
            msg = 'Still maneuvering, please specify abort/append command'
            self.say(msg, KO_COLOUR)
            return False
        # Reject order if imminent collision
        if pl_flags.collision == True:
            msg = '...'
            self.say(msg, KO_COLOUR)
            return False
        # Otherwise execute what requested
        for line in commands:
            command, args, cmd_flags = line
            # EXPEDITE FLAG
            if 'expedite' in cmd_flags:
                pl_flags.expedite = True
            # HEADING COMMAND
            if command == 'heading':
                if type(args[0]) == int:  #the argument is a heading
                    self.target_conf['heading'] = args[0]
                else:  #the argument is a location (a beacon's one)
                    self.set_course_towards(args[0])
                # Veering direction
                self.veering_direction = self.shortest_veering_direction()
                if 'long_turn' in cmd_flags:
                    self.veering_direction *= -1  #invert direction
            # ALTITUDE COMMAND
            elif command == 'altitude':
                feasible = self.verify_feasibility(altitude=args[0])
                if feasible != True:
                    self.say(feasible, KO_COLOUR)
                    return False
                self.target_conf['altitude'] = args[0]
            elif command == 'speed':
                feasible = self.verify_feasibility(speed=args[0])
                if feasible != True:
                    self.say(feasible, KO_COLOUR)
                    return False
                self.target_conf['speed'] = args[0]
            # TAKE OFF COMMAND
            elif command == 'takeoff':
                pass
            # LAND COMMAND
            elif command == 'land':
                feasible = self.verify_existing_runway(*args)
                if feasible != True:
                    self.say(feasible, KO_COLOUR)
                    return False
                ret = self.land(*args)
                if type(ret) != int:
                    return ret
            # CIRCLE COMMAND
            elif command == 'circle':
                param = args[0].lower()
                if param in ('l', 'left', 'ccw'):
                    self.veering_direction = self.LEFT
                elif param in ('r', 'right', 'cw'):
                    self.veering_direction = self.RIGHT
                else:
                    msg = 'Unknown parameter for circle command.'
                    raise BaseException(msg)
                pl_flags.circling = True
            # ABORT COMMAND
            elif command == 'abort':
                self._abort_command('lastonly' in cmd_flags)
                return True  #need to skip setting flag.busy to True!
            # SQUAWK COMMAND
            elif command == 'squawk':
                self.say('Currently heading %s, directed to %s' %
                          (rint(self.heading), self.destination), OK_COLOUR)
                return True  #need to skip setting flag.busy to True!
            else:
                raise BaseException('Unknown command: %s' % command)
        pl_flags.busy = True
        self.say(randelement(self.AFFIRMATIVE_EXEC_ANSWERS), OK_COLOUR)
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
        if port not in self.aerospace.aeroports:
            return 'Aeroport %s is not on the map!' % port
        if runway not in self.aerospace.aeroports[port].runways:
            return 'Aeroport %s does not have runway %s!' % (port, runway)
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

    def land(self, port_name=None, rnw_name=None):
        #TODO:BUG - Fix bug that limit turning ration to 'normal'
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
            if abs(pl.heading-ils_heading) > 60:
                msg = 'ILS heading must be within 60 degrees ' \
                      'from current heading'
                return self.__abort_landing(msg)
            # EARLY RETURN - No possible intersection (the RADAR_RANGE*3
            # ensures that the segments to test for intersection are long enough.
            if not l.set_ip():
                msg = 'The ILS does not intersect the plane current heading'
                return self.__abort_landing(msg)
            # EARLY RETURN - Although the intersection is ahead of the plane,
            # it's too late to merge into the ILS vector
            #TODO:BUG - doesn't work with 'expedite'! :(
            if l.set_md(self.get_veering_radius('normal')) < 0:
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
            if l.md <= 0:
                self.set_course_towards(l.foot.xy)
                l.phase = self.MERGING
#            print "--- INTERCEPTING ---"
#            print "from veering point : %s" % (l.md)
#            print "from ft            : %s" % l.fd
        elif l.phase == self.MERGING:
            if self.course_towards == None:
                l.phase = self.MATCHING
#            print "--- MERGING ---"
#            print "heading  : %s" % pl.heading
#            print "t head   : %s" % self.target_conf['heading']
#            print "from ft  : %s" % l.fd
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
                l.set_bd()
                if l.bd_from_ft < 0:
                    msg = 'Plane too fast to slow down to landing speed'
                    self.__abort_landing(msg)
            # ...otherwise tell it to climb/descend!!
            else:
                self.target_conf['altitude'] = path_alt
#            print "--- MATCHING ---"
#            print "alt        : %s" % pl.altitude
#            print "path alt   : %s" % path_alt
#            print "alt diff   : %s" % alt_diff
#            print "from ft    : %s" % l.fd
        elif l.phase == self.GLIDING:
            # Abort if the plane is too fast to slow to landing speed
            if l.bd <= 0:
                self.target_conf['speed'] = pl.landing_speed
            if pl.position.z < l.foot.z:
                if pl.destination == l.port_name:
                    pl.terminate(PLANE_LANDS_CORRECT_PORT)
                else:
                    pl.terminate(PLANE_LANDS_WRONG_PORT)
                return
            ticks = 1.0 * l.fd / self.target_conf['speed'] / PING_IN_SECONDS
            z_step = 1.0 * l.above_foot / ticks
            self.target_conf['altitude'] -= z_step
#            print "--- GLIDING ---"
#            print "alt on foot  : %s" % l.above_foot
#            print "speed        : %s" % pl.speed
#            print "target speed : %s" % self.target_conf['speed']
#            print "bd_from_ft   : %s" % l.bd_from_ft
#            print "from braking : %s" % l.bd
#            print "from ft      : %s" % l.fd
        return l.phase

    def veer(self):
        '''
        Make the plane turn.
        '''
        # The tightness of the curve is given by the kind of situation the
        # aeroplane is in.
        if self.plane.flags.expedite or self.plane.flags.cleared_down:
            veer_type = 'expedite'
        if self.plane.flags.collision:
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

    def check_closest_pass(self):
        '''
        Check if the plane has approached as much as possible to the target
        point (en route point).
          Return False if the plane hasn't, the minimum distance if it has.
        '''
        curr_dist = self.ground_distance(self.plane.position,
                                         Vector3(self.course_towards))
        if self.closest_pass_so_far < curr_dist:
            return self.closest_pass_so_far
        else:
            self.closest_pass_so_far = curr_dist
            return False

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
            self.closest_pass_so_far = self.ground_distance(
                                       self.plane.position, Vector3(*coords))
        delta = Vector3(*coords) - self.plane.position
        new_head = v3_to_heading(delta)
        if new_head != self.plane.heading:
            self.target_conf['heading'] = new_head
        else:
            self.course_towards = None
            self.veering_direction = None

    def set_aversion_course(self):
        '''
        Calculate the best course to avoid the colliding plane(s).
        This is done by:
        - Reducing speed to the minimum for increased manoeuvrability
        - Calculating opposite vectors to colliding planes and assigning to
          them a magnitude which is proportional to their distance.
        - Setting the course for the resulting vector.
        '''
        # Calculate the avoidance vector
        vectors = [self.plane.position - p.position
                   for p in self.plane.colliding_planes]
        vectors = [v.normalized()/abs(v) for v in vectors]
        vector = reduce(lambda x,y : x+y, vectors)
        # Set the target configuration
        self.plane.flags.expedite = True
        tc = self.target_conf
        if vector.z == 0:
            vector.z = randint(0,1)  #if two planes fly at the same level...
        tc['altitude'] = self.plane.max_altitude if vector.z > 0 else 0
        tc['speed'] = self.plane.min_speed
        tc['heading'] = (90-degrees(atan2(vector.y, vector.x)))%360
        self.veering_direction = self.shortest_veering_direction()

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
        # In case of imminent collision:
        if pl.flags.collision:
            self.set_aversion_course()
        # Circling action affects heading only (can be combined with changes in
        # speed and/or altitude)
        if pl.flags.circling:
            if self.veering_direction == self.LEFT:
                target = (self.heading - 179) % 360
            elif self.veering_direction == self.RIGHT:
                target = (self.heading + 179) % 360
            else:
                raise BaseException('Veering direction not set for circling.')
            self.target_conf['heading'] = target
        # Landing loop (affects all parameters at various landing phases)
        if pl.flags.cleared_down:
            self.land()
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
            if min_ <= pl.speed + gr_acc <= max_:
                pl.velocity += acc_vector
            # if out of boundaries, uses min and max
            else:
                pl.velocity = norm_velocity * (max_ if index else min_)
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
                self.execute_command(self.queued_commands.pop(0))
        # If the plane is en route towards a given point...
#        if self.course_towards:
#            self.test_closest_pass()