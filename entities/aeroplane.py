#!/usr/bin/env python
# -*- coding: utf-8  -*-
'''
Aeroplanes modelling of the ATC simulation game.
'''

import pilot
from engine.settings import *
from lib.utils import *
from math import sqrt
from collections import deque
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


class Aeroplane(object):

    '''
    Obviously this class represent the aeroplanes lying in the aerospace
    controlled from within the game. They can also be seen - using the MVC
    pattern - as the controllers for the sprites/groups.

    The ICAO attribute is also used as unique ID for each airplane.

    Each aeroplane has static attributes depending from the model the plane is.
    See the class `Flag` to see what status flag a plane can have.
    '''

    # A list of propery names that *MUST* be passed when building the plane.
    KNOWN_PROPERTIES = [#STATIC / game logic
                        'icao',              # Three-letter code and flight n.
                        'callsign',          # Radio callsign
                        'model',             # Type of plane (name)
                        'category',          # Propeller, Chopper, Jet...
                        'origin',            # Aeroport / Gate name
                        'destination',       # Aeroport / Gate name
                        'fuel_efficiency',   # Unit of fuel per meter
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
                        'position',          # 3D vector
                        'velocity',          # 3D vector
                        'fuel',              # remaining fuel
                       ]


    def __init__(self, aerospace, **kwargs):
        # Required parameters/properties
        self.aerospace = aerospace
        self.pilot = pilot.Pilot(self)
        for property in self.KNOWN_PROPERTIES:
            setattr(self, property, kwargs[property])
        # Initialisation of other properties
        self.entry_time = time()
        self.min_speed = self.landing_speed*1.5
        self.pilot.set_target_conf_to_current()
        self.flags = Flags()
        self.time_last_cmd = time()
        self.trail = deque([sc(self.position.xy)] * TRAIL_LENGTH, TRAIL_LENGTH)
        self.colliding_planes = []
        self.__accelerometer = ' '
        self.__variometer = ' '

    @property
    def heading(self):
        '''Current heading [CW degrees from North]'''
        return v3_to_heading(self.velocity)

    @property
    def speed(self):
        '''
        Current ground speed [m/s].
        (That means speed as projected on the XY plane)
        '''
        return sqrt(self.velocity.x**2 + self.velocity.y**2)

    @property
    def altitude(self):
        '''Current altitude [m]'''
        return self.position.z

    def update_instruments(self):
        '''
        Update instruments.
        '''
        # VARIOMETER - Note that this is controlled by instant velocity, not by
        # weather the plane target altitude is above or below the present one
        # (inertia of a descending plane might keep the variometer indicating
        # 'down' for a few seconds even if the last command instructed to
        # climb.
        indicator = ' '
        if self.velocity.z > 0:
            indicator = CHAR_UP
        elif self.velocity.z < 0:
            indicator = CHAR_DOWN
        self.__variometer = indicator
        # SPEEDOMETER
        # TODO: Decouple from pilot and use acceleration?
        t_speed = self.pilot.target_conf['speed']
        indicator = ' '
        if t_speed > self.speed:
            indicator = CHAR_UP
        elif t_speed < self.speed:
            indicator = CHAR_DOWN
        self.__accelerometer = indicator

    @property
    def variometer(self):
        '''
        Show weather the plane is currently climbing or descending.
        '''
        return self.__variometer

    @property
    def accelerometer(self):
        '''
        Show weather the plane is currently increasing or decreasing speed.
        '''
        return self.__accelerometer

    @property
    def sprite_index(self):
        '''
        Return a sprite index value (for selecting the correct sprite in the
        sprite sheets). Highest priority statuses override lower priority ones.
        '''
        value = CONTROLLED
        fl = self.flags
        if fl.busy or self.pilot.queued_commands or fl.circling or \
           fl.cleared_down or fl.cleared_up or fl.cleared_beacon:
            value = INSTRUCTED
        if fl.priority:
            value = PRIORITIZED
        if fl.collision:
            value = COLLISION
        if fl.locked:
            value = NON_CONTROLLED
        return value

    def terminate(self, event):
        '''
        Terminate an aeroplane.
        '''
        self.aerospace.gamelogic.remove_plane(self, event)

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
        burning_speed = 1 if self.flags.expedite == False else 2
        initial = self.position.copy()
        for i in range(pings):
            # Pilot's updates
            self.pilot.update()
        # Decrease fuel consumption
        dist = ground_distance(initial, self.position)
        burnt = burning_speed * dist * self.fuel_efficiency
        self.fuel -= burnt
        self.aerospace.gamelogic.score_event(PLANE_BURNS_FUEL_UNIT,
                                             multiplier=burnt)
        # Update sprite
        self.rect = sc(self.position.xy)
        self.trail.appendleft(sc(self.position.xy))

    def get_current_configuration(self):
        '''
        Return a dictionary with current heading, speed and altitude.
        '''
        return dict(speed = self.speed,
                    altitude = self.altitude,
                    heading = self.heading)
