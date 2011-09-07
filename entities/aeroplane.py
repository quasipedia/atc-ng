#!/usr/bin/env python
# -*- coding: utf-8  -*-
'''
Aeroplanes modelling of the ATC simulation game.
'''

import pilot
from engine.settings import *
from lib.utils import *
from math import sqrt
from lib.euclid import Vector3
from collections import deque
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


    def __init__(self, aerospace, **kwargs):
        self.aerospace = aerospace
        self.pilot = pilot.Pilot(self)
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
            self.ground_accels = (-4, 6)
        if self.landing_speed == None:
            self.landing_speed = 250 / 3.6  #first number is kph
        if self.max_speed == None:
            self.max_speed = 1600 / 3.6
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
        # Initialise instrumentation
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
        t_speed = self.target_conf['speed']
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

    def terminate(self, event):
        '''
        Terminate an aeroplane.
        '''
        self.aerospace.gamelogic.remove_plane(self, event)

    def queue_command(self, commands):
        '''
        Add a command to the queue buffer.
        '''
        # Only valid commands must be queued!
        for line in commands:
            command, args, flags = line
            if command == 'altitude':
                feasible = self.pilot.verify_feasibility(altitude=args[0])
                if feasible != True:
                    return feasible
            elif command == 'speed':
                feasible = self.pilot.verify_feasibility(speed=args[0])
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
        # Speedup
        pilot = self.pilot
        # Reject orders if busy
        if self.flags.busy == True and commands[0][0] != 'abort':
            return 'Still maneuvering, please specify abort/append command'
        # Reject order if imminent collision
        if self.flags.collision == True:
            return '...'
        # Otherwise execute what requested
        for line in commands:
            command, args, flags = line
            # EXPEDITE FLAG
            if 'expedite' in flags:
                self.flags.expedite = True
            # HEADING COMMAND
            if command == 'heading':
                if type(args[0]) == int:  #the argument is a heading
                    self.target_conf['heading'] = args[0]
                else:  #the argument is a location (a beacon's one)
                    pilot.set_course_towards(args[0])
                # Veering direction
                pilot.veering_direction = pilot.shortest_veering_direction()
                if 'long_turn' in flags:
                    pilot.veering_direction *= -1  #invert direction
            # ALTITUDE COMMAND
            elif command == 'altitude':
                feasible = pilot.verify_feasibility(altitude=args[0])
                if feasible != True:
                    return feasible
                self.target_conf['altitude'] = args[0]
            elif command == 'speed':
                feasible = pilot.verify_feasibility(speed=args[0])
                if feasible != True:
                    return feasible
                self.target_conf['speed'] = args[0]
            # TAKE OFF COMMAND
            elif command == 'takeoff':
                pass
            # LAND COMMAND
            elif command == 'land':
                feasible = pilot.verify_existing_runway(*args)
                if feasible != True:
                    return feasible
                ret = pilot.land(*args)
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
                self.flags.circling = True
            # ABORT COMMAND
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
        for i in range(pings):
            # Pilot's updates
            self.pilot.update()
            # Decrease fuel consumption
            self.fuel -= 1*pings if self.fuel else 0
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

    def set_target_conf_to_current(self):
        '''
        Set the target configuration for the current one.
        '''
        self.target_conf = self.get_current_configuration()
