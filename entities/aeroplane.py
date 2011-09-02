#!/usr/bin/env python
# -*- coding: utf-8  -*-
'''
Aeroplanes modelling of the ATC simulation game.
'''

from engine.settings import *
from math import sqrt, atan2, degrees, radians, cos, sin
from lib.euclid import Vector3
from collections import deque
from random import randint
from time import time
import yaml


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


class Flags(object):

    '''
    A simple container for flags, used only to avoid using dictionaries all
    over the place.
    '''

    def __init__(self):
        self.reset()

    def reset(self):
        '''
        Set all flags to their default value
        '''
        self.expedite = False
        self.cleared_up = False        # take off clearance
        self.cleared_down = False      # landing clearance
        self.cleared_beacon = False    # clearance to reach beacon
        self.priority = False
        self.circling = False
        self.locked = False            # The plane is under computer control
        self.collision = False         # The plane is on a collision path
        self.busy = False              # The plane is executing a command


class Pilot(object):

    '''
    A class containing all the methods that alter the flying configuration of
    the aeroplane.
    '''

    LEFT = CCW = -1
    RIGHT = CW = +1

    def __init__(self, plane):
        self.plane = plane

    def __verify_feasibility(self, speed=None, altitude=None):
        '''
        Verify if given speed and altitude are within aeroplane specifications.
        Heading is a dummy variable, used to make possible to use this method
        with any of the three attributes.
        Return True or a message error.
        '''
        if speed != None and not self.min_speed < speed < self.max_speed:
            mi = rint(self.min_speed * 3.6)
            ma = rint(self.max_speed * 3.6)
            return 'Our aircraft can only cruise between %d and %d kph.' % \
                    (mi, ma)
        if altitude != None and altitude  > self.max_altitude:
            return 'The target altitude is above the maximum one for our ' +\
                   'aircraft.'
        return True

    def test_in_between(self, boundaries, value):
        '''
        Return True if value is between boundaries.
        Boundaries : any two values (tuple, list)
        Value: the value to be tested
        '''
        tmp = list(boundaries)
        tmp.append(value)
        tmp = [el for el in tmp]
        tmp.sort()
        return tmp[1] == value

    def test_heading_in_between(self, boundaries, value):
        '''
        This is a heading-specific implmentation of `test_in_between`.
        From a geometrical point of view, an angle is always between other two.
        This method return True, if the tested value is between the *smallest*
        angle between the other two.
        '''
        sort_a = lambda a,b : [a,b] if (a-b)%360 > (b-a)%360 else [b,a]
        tmp = sort_a(*boundaries)
        if tmp[0] > tmp[1]:
            tmp[0] -= 360
        return tmp[0] <= value <= tmp[1]

    def test_target_conf_reached(self):
        '''
        Return True if the current plane configuration matches the target one.
        '''
        tc = self.plane.target_conf
        return self.plane.heading == tc['heading'] and \
               self.plane.altitude == tc['altitude'] and \
               self.plane.speed == tc['speed']

    def shortest_veering_direction(self):
        '''
        Return self.LEFT or self.RIGHT according to whatever the shortest
        veering to a certain course is.
        '''
        theta = (self.plane.heading - self.plane.target_conf['heading']) % 360
        return self.LEFT if theta < 180 else self.RIGHT

    def veer(self, pings):
        '''
        Make the plane turn.

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
        # The tightness of the curve is given by the kind of situation the
        # aeroplane is in.
        max_manouvering_g = 1.15
        if self.plane.flags.expedite or self.flags.cleared_down:
            max_manouvering_g = 1.41
        if self.plane.flags.collision:
            max_manouvering_g = self.plane.max_g
        g_to_mks = lambda x : 9.807 * x
        acc_module = sqrt(g_to_mks(max_manouvering_g)**2-g_to_mks(1)**2)
        angular_speed = acc_module/self.plane.velocity.magnitude() * \
                        -self.veering_direction
        rotation_axis = Vector3(0,0,1)
        self.plane.velocity = self.plane.velocity.rotate_around(rotation_axis,
                             angular_speed*PING_IN_SECONDS*pings)

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
        tc = self.plane.target_conf
        if vector.z == 0:
            vector.z = randint(0,1)  #if two planes fly at the same level...
        tc['altitude'] = self.plane.max_altitude if vector.z > 0 else 0
        tc['speed'] = self.plane.min_speed
        tc['heading'] = (90-degrees(atan2(vector.y, vector.x)))%360
        self.veering_direction = self.shortest_veering_direction()


class Aeroplane(object):

    '''
    Obviously this class represent the aeroplanes lying in the aerospace
    controlled from within the game. They can also be seen - using the MVC
    pattern - as the controllers for the sprites/groups.

    The ICAO attribute is also used as unique ID for each airplane.

    Each aeroplane has static attributes depending from the model the plane is.
    See the class `Flag` to see what status flag a plane can have.
    '''

    KNOWN_PROPERTIES = [#STATIC / game logic
                        'icao',              # Three-letter code and flight n.
                        'callsign',          # Radio callsign
                        'model',             # Type of plane (name)
                        'origin',       # Airport/exit name
                        'destination',       # Airport/exit name
                        'entry_time',        # Time of entry in airspace
                        #STATIC / vertical modelling
                        'max_altitude',      # max altitude
                        'climb_rate_limits', # (down, up) climb rates
                        'climb_rate_accels', # (down, up) climb acceleration
                        #STATIC / horizontal modelling
                        'max_speed',         # max ground speed
                        'ground_accels',     # (decel, accel) ground accel
                        'landing_speed',     # landing/takeoff speed
                        'max_g',             # Gforce for emergency manouvers
                        #DYNAMIC
                        'target_conf',       # (heading, speed, altitude)
                        'position',          # 3D vector
                        'velocity',          # 3D vector
                        'fuel',              # remaining fuel
                        'time_last_cmd',     # time of last received command
                        'flags',             # flag object (see class `Flags`)
                        'veering_direction', # self.LEFT or self.RIGHT
                        'target_coords',     # target coordinates to reach
                                             # (e.g.: a beacon location)
                        'target_vector',     # target vector to align to
                                             # (e.g.: ILS landing path)
                       ]

    LEFT = CCW = -1
    RIGHT = CW = +1

    def __init__(self, **kwargs):
        self.pilot = Pilot(self)
        for property in self.KNOWN_PROPERTIES:
            value = kwargs[property] if kwargs.has_key(property) else None
            setattr(self, property, value)
        if self.icao == None:
            raise BaseException('An ICAO id must be always specified.')
        if self.position is None:
            self.position = Vector3(RADAR_RANGE, RADAR_RANGE)
        if self.velocity is None:
            self.velocity = Vector3(randint(30,400), 0, 0)
        if self.target_conf == None:
            self.target_conf = {}
            self.set_target_conf_to_current()
        if self.climb_rate_limits == None:
            self.climb_rate_limits = (-30, 15)
        if self.climb_rate_accels == None:
            self.climb_rate_accels = (-20, 10)
        if self.max_altitude == None:
            self.max_altitude = 10000
        if self.ground_accels == None:
            self.ground_accels = (-5, 10)
        if self.landing_speed == None:
            self.landing_speed = 100 / 3.6  #100kph
        if self.max_speed == None:
            self.max_speed = 800
        if self.max_g == None:
            self.max_g = 3
        if self.fuel == None:
            self.fuel = randint(100,200)
        self.time_last_cmd = time()
        # Derived values
        self.min_speed = self.landing_speed*1.5
        # Dummy to test varius sprites
        mag = self.velocity.magnitude()
        if mag < 150:
            self.model = 'propeller'
        elif mag < 300:
            self.model = 'jet'
        else:
            self.model = 'supersonic'
        self.flags = Flags()
        # Initialise the trail
        self.trail = deque([sc(self.position.xy)] * TRAIL_LENGTH, TRAIL_LENGTH)
        # Initialise the command queue
        self.queued_commands = []
        # Initialise the colliding planes registry
        self.colliding_planes = []

    @property
    def heading(self):
        '''Current heading [CW degrees from North]'''
        return (90-degrees(atan2(self.velocity.y, self.velocity.x)))%360

    @property
    def speed(self):
        '''
        Current ground speed [m/s].
        (That means speed as projected on the XY plane)
        '''
        return rint(sqrt(self.velocity.x**2 + self.velocity.y**2))

    @property
    def altitude(self):
        '''Current altitude [m]'''
        return self.position.z

    @property
    def variometer(self):
        '''
        Show weather the plane is currently climbing or descending.
        Note that this is controlled by instant velocity, not by weather the
        plane target altitude is above or below the present one (inertia of a
        descending plane might keep the variometer indicating 'down' for a few
        seconds even if the last command instructed to climb.
        '''
        indicator = ' '
        if self.velocity.z > 0:
            indicator = CHAR_UP
        elif self.velocity.z < 0:
            indicator = CHAR_DOWN
        return indicator

    @property
    def accelerometer(self):
        '''
        Show weather the plane is currently increasing or decreasing speed.
        '''
        t_speed = self.target_conf['speed']
        indicator = ' '
        if t_speed > self.speed:
            indicator = CHAR_UP
        elif t_speed < self.speed:
            indicator = CHAR_DOWN
        return indicator

    @property
    def sprite_index(self):
        '''
        Return a sprite index value (for selecting the correct sprite in the
        sprite sheets). Highest priority statuses override lower priority ones.
        '''
        value = CONTROLLED
        fl = self.flags
        if fl.busy or self.queued_commands or fl.circling or \
           fl.cleared_down or fl.cleared_up or fl.cleared_beacon:
            value = INSTRUCTED
        if fl.priority:
            value = PRIORITIZED
        if fl.collision:
            value = COLLISION
        if fl.locked:
            value = NON_CONTROLLED
        return value

    def queue_command(self, commands):
        '''
        Add a command to the queue buffer.
        '''
        # Only valid commands must be queued!
        for line in commands:
            command, args, flags = line
            if command == 'altitude':
                feasible = self.__verify_feasibility(altitude=args[0])
                if feasible != True:
                    return feasible
            elif command == 'speed':
                feasible = self.__verify_feasibility(speed=args[0])
                if feasible != True:
                    return feasible
        # Queuing can only be performed after commands whose implementation
        # will eventually finish...
        if self.flags.circling:
            msg = 'This makes no sense... when should we stop circling?!'
            return msg
        # And before the end of the flight!
        if self.flags.cleared_down:
            msg = 'Once landed, the flight is over!'
            return msg
        self.queued_commands.append(commands)
        return True

    def execute_command(self, commands):
        '''
        Execute commands.
        Input is a list of triplets each of them in the format:
        [command, [arg1, arg2, ...], [flag1, flag2, ...]].
        Return True or a message error.
        '''
        if self.flags.busy == True and commands[0][0] != 'abort':
            return 'Still maneuvering, please specify abort/append command'
        if self.flags.collision == True:
            return '...'
        for line in commands:
            command, args, flags = line
            if 'expedite' in flags:
                self.flags.expedite = True
            if command == 'heading':
                if type(args[0]):  #the argument is a heading
                    self.target_conf['heading'] = args[0]
                    self.veering_direction = \
                                        self.pilot.shortest_veering_direction()
                    if 'long_turn' in flags:
                        self.veering_direction *= -1  #invert direction
                else:  #the argument is a location (a beacon's one)
                    self.target_coords = args[0]
            elif command == 'altitude':
                feasible = self.__verify_feasibility(altitude=args[0])
                if feasible != True:
                    return feasible
                self.target_conf['altitude'] = args[0]
            elif command == 'speed':
                feasible = self.__verify_feasibility(speed=args[0])
                if feasible != True:
                    return feasible
                self.target_conf['speed'] = args[0]
            elif command == 'takeoff':
                pass
            elif command == 'land':
                pass
            elif command == 'circle':
                param = args[0].lower()
                if param in ('l', 'left', 'ccw'):
                    self.veering_direction = self.LEFT
                elif param in ('r', 'right', 'cw'):
                    self.veering_direction = self.RIGHT
                else:
                    msg = 'Unknown parameter for circle command.'
                    raise BaseException(msg)
                self.flags.circling = True
            elif command == 'abort':
                self._abort_command('lastonly' in flags)
                return True  #need to skip setting flag.busy to True!
            else:
                raise BaseException('Unknown command: %s' % command)
            self.flags.busy = True
        self.time_last_cmd = time()
        return True

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
        self.flags.reset()

    def set_aversion(self, other_plane):
        '''
        Instruct the plane to avoid collision with `other_plane`
        '''
        # Aversion is an emergency, and voids any other order and order queue
        self.flags.reset()
        self.queued_commands = []
        self.colliding_planes.append(other_plane)
        self.flags.collision = True

    def update(self, pings):
        '''
        Update the plane status according to the elapsed time.
        Pings = number of radar pings from last update.
        '''
        # Store initial values [for "post_update_ops"]
        self.previous_altitude = self.altitude
        self.previous_heading = self.heading
        self.previous_speed = self.speed
        # In case of imminent collision:
        if self.flags.collision:
            self.pilot.set_aversion_course()
        # If instructed to reach a coordinate
        if self.target_coords:
            pass
        # If instructed to align with a vector:
        if self.target_vector:
            pass
        # Circling action affects heading only (can be combined with changes in
        # speed and/or altitude)
        if self.flags.circling:
            if self.veering_direction == self.LEFT:
                target = (self.heading - 179) % 360
            elif self.veering_direction == self.RIGHT:
                target = (self.heading + 179) % 360
            else:
                raise BaseException('Veering direction not set for circling.')
            self.target_conf['heading'] = target
        if self.heading != self.target_conf['heading']:
            self.pilot.veer(pings)
        if self.altitude != self.target_conf['altitude']:
            # Descending or ascending?
            index = self.altitude < self.target_conf['altitude']
            z_acc = self.climb_rate_accels[index]*PING_IN_SECONDS*pings
            # Non expedite climbs are limited at 50% of maximum rate
            if not self.flags.expedite:
                z_acc *= 0.5
            # Acceleration cannot produce a climb rate over or under the limits
            min_, max_ = self.climb_rate_limits
            if min_ <= self.velocity.z + z_acc <= max_:
                self.velocity.z += z_acc
            # if out of boundaries, uses min and max
            else:
                self.velocity.z = max_ if index else min_
        if self.speed != self.target_conf['speed']:
            index = self.speed < self.target_conf['speed']
            gr_acc = self.ground_accels[index]*PING_IN_SECONDS*pings
            # Non expedite accelerations are limited at 50% of maximum accels
            if not self.flags.expedite:
                gr_acc *= 0.5
            norm_velocity = Vector3(*self.velocity.xyz).normalized()
            acc_vector = norm_velocity * gr_acc
            # Acceleration cannot produce a speed over or under the limits
            min_, max_ = self.min_speed, self.max_speed
            if min_ <= self.speed + gr_acc <= max_:
                self.velocity += acc_vector
            # if out of boundaries, uses min and max
            else:
                self.velocity = norm_velocity * (max_ if index else min_)
        # Update position
        self.position += self.velocity*PING_IN_SECONDS*pings
        # Decrease fuel consumption
        self.fuel -= 1*pings if self.fuel else 0
        self.rect = sc(self.position.xy)
        self.trail.appendleft(sc(self.position.xy))
        # Post-update ops
        self.post_update_ops()

    def post_update_ops(self):
        '''
        Peforms a series of post-update plane operations.
        '''
        # Heading dampener (act on velocity vector)
        t_head = self.target_conf['heading']
        if self.pilot.test_heading_in_between((self.previous_heading,
                                           self.heading), t_head):
            mag = self.velocity.magnitude()
            theta = radians(90-t_head)
            self.velocity.x = cos(theta)*mag
            self.velocity.y = sin(theta)*mag
        # Speed dampener (act on velocity vector)
        t_speed = self.target_conf['speed']
        if self.pilot.test_in_between((self.previous_speed, self.speed), t_speed):
            mag = t_speed
            self.velocity = self.velocity.normalized() * t_speed
        # Altitude dampener (act on position vector)
        t_alt = self.target_conf['altitude']
        if self.pilot.test_in_between((self.previous_altitude,
                                   self.altitude), t_alt):
            self.position.z = t_alt
            self.velocity.z = 0
        # Update busy flag or start execution of next command
        fl = self.flags
        if self.pilot.test_target_conf_reached() and not \
                      (fl.cleared_beacon or fl.cleared_down or fl.cleared_up):
            fl.busy = False  #execute commands will check this flag
            fl.expedite = False  #reset
            if self.queued_commands:
                self.execute_command(self.queued_commands.pop(0))

    def set_target_conf_to_current(self):
        '''
        Set the target configuration for the plane to the current heading,
        speed and altitude.
        '''
        self.target_conf['speed'] = self.speed
        self.target_conf['altitude'] = self.altitude
        self.target_conf['heading'] = self.heading

