#!/usr/bin/env python
# -*- coding: utf-8  -*-
'''
Aeroplanes modelling of the ATC simulation game.
'''

from settings import *
from math import sqrt, atan
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
        for property in self.KNOWN_PROPERTIES:
            value = kwargs[property] if kwargs.has_key(property) else None
            setattr(self, property, value)
        if self.icao == None:
            self.icao = self.__random_icao()
        if self.position == None:
            self.position = Vector3(randint(0,WINDOW_SIZE[0]*SCALE_FACTOR),
        if self.velocity == None:
            self.velocity = Vector3(randint(200,300), 0, 0)
        # Initialise the trail
        self.trail_coords = deque([self.position.xy], TRAIL_LENGTH)

    def __random_icao(self):
        '''Return a random pseudo-ICAO flight number'''
        rc = lambda : chr(randint(65, 90))
        return ''.join([rc(), rc(), rc(), str(randint(1000, 9999))])

    @property
    def heading(self):
        '''Current heading'''
        return atan(1.0*self.velocity.y/self.velocity.x)

    def turn(self):
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
                                                    angular_speed*PING_PERIOD)

    def update(self):
        self.turn()
        self.position += self.velocity*PING_PERIOD
        self.rect = sc(self.position.xy)
        self.trail.appendleft(sc(self.position.xy))
        if self.velocity.magnitude() > 75:
            self.velocity.x -= 1 if self.velocity.x >0 else -1
            self.velocity.y -= 1 if self.velocity.x >0 else -1


