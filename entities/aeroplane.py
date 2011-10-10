#!/usr/bin/env python
# -*- coding: utf-8  -*-
'''
Aeroplanes modelling of the ATC simulation game.
'''

from math import sqrt, degrees, atan2
from collections import deque
from time import time

import lib.utils as U
import pilot.pilot
from engine.settings import settings as S
from lib.euclid import Vector3
from engine.logger import log


__author__ = "Mac Ryan"
__copyright__ = "Copyright 2011, Mac Ryan"
__license__ = "GPL v3"
#__version__ = "<dev>"
#__date__ = "<unknown>"
__maintainer__ = "Mac Ryan"
__email__ = "quasipedia@gmail.com"
__status__ = "Development"


class Flags(object):

    '''
    A simple container for flags, used only to avoid using dictionaries all
    over the place. Flags are mostly used for sprite colour-control. Most of
    the static information on what the plane is doing are contained within
    ``pilot.pilot.Pilot()``.
    '''

    def __init__(self):
        self.reset()

    def reset(self):
        '''
        Set all flags to their default value.
        '''
        self.collision = False         # The plane is about to collide
        self.priority = False          # The plane needs a priority landing
        self.locked = False            # The plane is under computer control
        self.busy = False              # The plane is executing a command
        self.on_ground = False         # The plane is not flying
        try:
            self.fuel_emergency = self.fuel_emergency
        except AttributeError:
            self.fuel_emergency = False
        if self.fuel_emergency:
            self.priority = True

class Tcas(object):

    '''
    TCAS = Traffic Collision Avoidance System. This class provides the methods
    needed to avoid collisions between planes. This class relies on "server
    data" made available from the aerospace. Such server data indicates which
    planes are about to collide. This class establishes the counter-measures.
    '''

    def __init__(self, plane):
        self.plane = plane
        self.state = False  #OFF state

    def set_aversion_course(self, colliding):
        '''
        Calculate the best course to avoid the colliding plane(s).
        This is done by:
        - Reducing speed to the minimum for increased manoeuvrability
        - Calculating opposite vectors to colliding planes and assigning to
          them a magnitude which is proportional to their distance.
        - Setting the course for the resulting vector.
        '''
        plane = self.plane
        pilot = self.plane.pilot
        # CALCULATE THE AVOIDANCE VECTOR
        # Prevents unresolved cases but altering slighly the plane position if
        # two planes are stacked one on top of the other or fly at the same
        # level.
        while True:
            vectors = [plane.position - p.position for p in colliding]
            vectors = [v.normalized()/abs(v) for v in vectors]
            vector = reduce(lambda x,y : x+y, vectors)
            if vector.z == 0:
                plane.position.z += 0.01
            elif vector.x == vector.y == 0:
                plane.position.x += 0.01
            else:
                break
        # SET THE TARGET CONFIGURATION
        tc = pilot.target_conf
        max_up = min(plane.max_altitude, S.MAX_FLIGHT_LEVEL)
        tc.altitude = max_up if vector.z > 0 else S.MIN_FLIGHT_LEVEL
        tc.speed = plane.min_speed
        tc.heading = (90-degrees(atan2(vector.y, vector.x)))%360
        pilot.status['veer_dir'] = \
                pilot.navigator.get_shortest_veering_direction()

    def update(self):
        '''
        Check if there is danger of collsion. If this is the case, take
        appropriate counter-measures.
        '''
        try:
            colliding = self.plane.aerospace.tcas_data[self.plane.icao]
            self.plane.pilot.executer.abort()
            if self.state == False:
                self.plane.aerospace.gamelogic.score_event(S.EMERGENCY_TCAS)
            self.state = True
            self.set_aversion_course(colliding)
        except KeyError:
            if self.state == True:
                self.plane.pilot.set_target_conf_to_current()
                self.plane.pilot.adjust_to_valid_FL()
            self.state = False


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
                        'origin',            # airport / Gate name
                        'destination',       # airport / Gate name
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
        self.tcas = Tcas(self)
        for property in self.KNOWN_PROPERTIES:
            setattr(self, property, kwargs[property])
        # Initialisation of other properties
        self.entry_time = time()
        self.min_speed = self.landing_speed*1.5
        self.flags = Flags()
        if self.origin in aerospace.airports:
            self.flags.on_ground = True
        self.time_last_cmd = time()
        self.trail = deque(
               [U.sc(self.position.xy)] * S.TRAIL_LENGTH, S.TRAIL_LENGTH)
        self.colliding_planes = []
        self.__accelerometer = ' '
        self.__variometer = ' '
        self.pilot = pilot.pilot.Pilot(self)
        self.fuel_delta = self.fuel / 2
        self.dist_to_target = self.fuel / self.fuel_efficiency / 4

    @property
    def heading(self):
        '''Current heading [CW degrees from North]'''
        return U.v3_to_heading(self.velocity)

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

    def get_current_configuration(self):
        '''
        Return a dictionary with current heading, speed and altitude.
        '''
        return dict(speed = self.speed,
                    altitude = self.altitude,
                    heading = self.heading)

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
            indicator = S.CHAR_UP
        elif self.velocity.z < 0:
            indicator = S.CHAR_DOWN
        self.__variometer = indicator
        # SPEEDOMETER
        # TODO: Decouple from pilot and use acceleration?
        t_speed = self.pilot.target_conf.speed
        indicator = ' '
        if t_speed > self.speed:
            indicator = S.CHAR_UP
        elif t_speed < self.speed:
            indicator = S.CHAR_DOWN
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
        value = S.CONTROLLED
        fl = self.flags
        if fl.busy:
            value = S.INSTRUCTED
        if fl.priority or fl.fuel_emergency:
            value = S.PRIORITIZED
        if self.tcas.state:
            value = S.COLLISION
        if fl.locked:  #take_offs and landings
            value = S.NON_CONTROLLED
        return value

    def terminate(self, event):
        '''
        Terminate an aeroplane.
        '''
        self.aerospace.gamelogic.remove_plane(self, event)
        self.aerospace.runways_manager.release_runway(self)

    def update(self, pings):
        '''
        Update the plane status according to the elapsed time.
        Pings = number of radar pings from last update.
        '''
        burning_speed = 1 if self.pilot.status['haste'] == 'normal' else 2
        initial = self.position.copy()
        for i in range(pings):
            # Pilot's updates
            self.pilot.update()
        # Compute waiting time score if not airborne
        # FIXME: distinguish between just landed and waiting to takeoff
        if self.flags.on_ground:
            mult = pings * S.PING_IN_SECONDS
            self.aerospace.gamelogic.score_event(S.PLANE_WAITS_ONE_SECOND,
                                                 multiplier=mult)
        # Decrease fuel amount if airborne
        elif self.fuel > 0:
            dist = U.ground_distance(initial, self.position)
            burnt = burning_speed * dist * self.fuel_efficiency
            self.fuel -= burnt
            self.aerospace.gamelogic.score_event(S.PLANE_BURNS_FUEL_UNIT,
                                                 multiplier=burnt)
        # Check if a fuel emergency has to be triggered.
        # FIXME: this is goo reason to use objects intstead of IATA/NAME
        try:
            dest_point = self.aerospace.airports[self.destination].location
        except KeyError:
            tmp = self.aerospace.gates[self.destination].location
            dest_point = Vector3(tmp[0], tmp[1], self.altitude)
        dist = U.ground_distance(dest_point, self.position)
        self.fuel_delta = self.fuel - (2 * dist * self.fuel_efficiency)
        self.dist_to_target = dist
        if not self.flags.fuel_emergency and self.fuel_delta < 0:
            log.info('%s is declaring fuel emergency' % self.icao)
            msg = 'Pan-Pan, Pan-Pan, Pan-Pan... We are low on fuel, ' \
                  'requesting priority landing!'
            self.pilot.say(msg, S.KO_COLOUR)
            self.aerospace.gamelogic.score_event(S.EMERGENCY_FUEL)
            self.flags.fuel_emergency = True
        # Fuel has ran out
        if self.fuel < 0:
            msg = 'Mayday! Mayday! Mayday! All engines have flamed out, we ' \
                  'are going down!'
            self.pilot.say(msg, S.KO_COLOUR)
            log.info('%s has ran out of fuel' % self.icao)
            self.fuel = 0
            self.max_speed = self.min_speed * 2
            max_down = self.climb_rate_limits[0]
            self.climb_rate_limits = [max_down, max_down / 2.0]
        # Update sprite
        self.rect = U.sc(self.position.xy)
        self.trail.appendleft(U.sc(self.position.xy))
