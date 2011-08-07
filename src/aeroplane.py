#!/usr/bin/env python
# -*- coding: utf-8  -*-
'''
Aeroplanes modelling of the ATC simulation game.
'''

from locals import *
from math import sqrt, atan2, degrees
from euclid import Vector3
from collections import deque
from random import randint

__author__ = "Mac Ryan"
__copyright__ = "Copyright 2011, Mac Ryan"
#__credits__ = ["Name Lastname", "Name Lastname"]
__license__ = "GPL v3"
#__version__ = "1.0.0"
__maintainer__ = "Mac Ryan"
__email__ = "quasipedia@gmail.com"
__status__ = "Development"


class Aeroplane(object):

    '''
    Obviously this class represent the aeroplanes lying in the aerospace
    controlled from within the game. They can also be seen - using the MVC
    pattern - as the controllers for the sprites/groups.

    The ICAO attribute is also used as unique ID for each airplane.

    Each aeroplane has static attributes depending from the model the plane is.
    The flag property contains a list of empty possible flags:
        Expedite   - Expedite climb or acceleration
        Cleared    - Cleared for takeoff or landing
        Emergency  - High priority flight
        Circling_L - Circling left
        Circling_R - Circling right
        Locked     - The plane is under computer control
        Collision  - The plane is on a collision path
    '''

    KNOWN_PROPERTIES = [#STATIC
                        'icao',            # Three-letter code and flight num.
                        'model',           # Type of plane (name)
                        'destination',     # Airport name
                        'entry_time',      # Time of entry in airspace
                        'speed_limits',    # (min, max) XY projected speed
                        'accel_limits',    # (decel, accel) XY projected accel
                        'max_altitude',    # max altitude
                        'climb_limits',    # (down, up) max climb rates
                        'takeoff_speed',   # takeoff speed at liftoff
                        'landing_speed',   # landing speed at touchdown
                        'max_g',           # maximum Gforce
                        #DYNAMIC
                        'target_conf',     # (heading, speed, altitude)
                        'position',        # 3D vector
                        'velocity',        # 3D vector
                        'fuel',            # seconds before crash
                        'time_last_cmd',   # time of last received command
                        'flags',           # list of flags
                       ]

    def __init__(self, **kwargs):
        self.ping_in_seconds = PING_PERIOD / 1000.0
        for property in self.KNOWN_PROPERTIES:
            value = kwargs[property] if kwargs.has_key(property) else None
            setattr(self, property, value)
        if self.icao == None:
            self.icao = self.__random_icao()
        if self.position == None:
            self.position = Vector3(randint(0, RADAR_RANGE*2),
                                    randint(0, RADAR_RANGE*2))
        if self.velocity == None:
            self.velocity = Vector3(randint(30,400), 0, 0)
        if self.target_conf == None:
            self.target_conf = {}
            self.target_conf['heading'] = self.heading + randint(-90,90)
            self.target_conf['speed'] = self.speed + randint(-100, 100)
            self.target_conf['altitude'] = self.altitude + randint(-3000, 3000)
        # Dummy to test varius sprites
        mag = self.velocity.magnitude()
        if mag < 150:
            self.model = 'propeller'
        elif mag < 300:
            self.model = 'jet'
        else:
            self.model = 'supersonic'
        self.status = [CONTROLLED, INSTRUCTED, NON_CONTROLLED, PRIORITIZED,
                       COLLISION][randint(0,4)]
        # Initialise the trail
        self.trail = deque([sc(self.position.xy)] * TRAIL_LENGTH, TRAIL_LENGTH)

    def __random_icao(self):
        '''Return a random pseudo-ICAO flight number'''
        rc = lambda : chr(randint(65, 90))
        return ''.join([rc(), rc(), rc(), str(randint(1000, 9999))])

    @property
    def heading(self):
        '''Current heading [CW degrees from North]'''
        return degrees(atan2(self.velocity.y, self.velocity.x))

    @property
    def speed(self):
        '''
        Current ground speed [m/s].
        (That means speed as projected on the XY plane)
        '''
        return int(round(sqrt(self.velocity.x**2 + self.velocity.y**2)))


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
        tspeed = self.target_conf['speed']
        indicator = ' '
        if tspeed > self.speed:
            indicator = CHAR_UP
        elif self.velocity.z < self.speed:
            indicator = CHAR_DOWN
        return indicator

    def execute_command(self, input):
        '''
        Execute commands.
        Input is a list of triplets each of them in the format:
        [command, arguments (list), flags (list)]
        '''
        for line in input:
            command, args, flags = line
            print(command, args, flags)

    def turn(self, pings):
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
        g_to_mks = lambda x : 9.807 * x
        acc_module = sqrt(g_to_mks(1.15)**2-g_to_mks(1)**2)
        angular_speed = acc_module/self.velocity.magnitude()
        rotation_axis = Vector3(0,0,1)
        self.velocity = self.velocity.rotate_around(rotation_axis,
                             angular_speed*self.ping_in_seconds*pings)

    def update(self, pings):
        self.turn(pings)
        self.position += self.velocity*self.ping_in_seconds*pings
        self.rect = sc(self.position.xy)
        # TODO: trail entries could happen only 1 in X times, to make dots
        # more spaced out
        self.trail.appendleft(sc(self.position.xy))
