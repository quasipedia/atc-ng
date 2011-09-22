#!/usr/bin/env python
# -*- coding: utf-8  -*-
'''
The pilot that is in charge of planes in the ATC-NG game.
'''

from engine.settings import *
from engine.logger import log
from entities.aeroplane import Aeroplane
from lib.utils import *
from math import sqrt, radians, cos, sin, tan
from lib.euclid import Vector3
import checker
import random
import executer
import navigator
import procedures

__author__ = "Mac Ryan"
__copyright__ = "Copyright 2011, Mac Ryan"
__license__ = "GPL v3"
#__version__ = "<dev>"
#__date__ = "<unknown>"
__maintainer__ = "Mac Ryan"
__email__ = "quasipedia@gmail.com"
__status__ = "Development"


class TargetConfiguration():

    '''
    This is a container class with a few tweaks:

    - It allows a more coincise spelling of H, A, S, compared to a dictionary
      ``target_conf.altitude`` instead of ``target_conf['altitude']``
    - It allows to retrive the target heading through a method, which in turns
      allows for the data to be stored either as a numeric heading or as
      a point the aeroplane should head towards
    - It embed a method to check if the values stored in ``self`` match the
      configuration of a given plane.
    '''

    def __init__(self, pilot):
        self.pilot = pilot
        # These two properties are "vanilla"...
        self.speed = None
        self.altitude = None
        # ...but this isn't!
        self.__heading = None

    @property
    def heading(self):
        '''
        If ``self.__heading`` is a heading, return it. If it is a point,
        return the heading from the plane towards that point.
        '''
        if type(self.__heading) == Vector3:
            return self.pilot.navigator.get_course_towards(self.__heading)
        return self.__heading

    @heading.setter
    def heading(self, value):
        assert type(value) in (int, float, Vector3)
        self.__heading = value

    def is_reached(self):
        '''
        Return True if ``self`` matches the configuration of a given plane.
        '''
        plane = self.pilot.plane
        return plane.heading == self.heading and \
               plane.altitude == self.altitude and \
               plane.speed == self.speed


class Pilot(object):

    '''
    The Pilot class is the pivotal point of the pilot package, and most
    probably the only one that should be used from outside the package itself.

    At each ``update()`` call, the pilot follows a two-steps routine:

    #. Check the plane instruments (and take emergency actions if needed)
    #. Check the ToDo list (and perform any regular action if needed)

    The pilot communicates with the player through two methods:

    * ``do()`` - Receive a command
    * ``say()`` - Output a message on the console

    the ``do()`` method also returns a response message to the caller (so
    to the code, not to the player), which is tuple (boolean, dictionary) in
    which the tuple value True/False represent the affermative or negative
    outome of the order, while the dictionary represent other command-specific
    response codes that is up to the caller to be able to process.

    By default, the task of the pilot is to make the aeroplane to reach a given
    configuration (altitude, heading, speed) and maintain that. In order to do
    so, the pilot performs certain *manoeuvres* (veer, climb..).

    However, the pilot can also follow more complex *procedures* for multi-
    steps tasks, like landings and take-offs. Such procedures live in the
    ``pilot.procedures`` module.

    The ``pilot.status`` is a dictionary and it is used to keep track between
    game loops of the pilot configuration.
    '''

    # SHORTHANDS
    PING_IN_SECONDS = PING_PERIOD / 1000.0
    # RADIO ANSWERS
    AFFIRMATIVE_EXEC_ANSWERS = ['Roger that. Executing.',
                                'Affirmative, initiating maneuver now.',
                                'Roger, we\'re on it.',
                                'Copy that.',
                                'Okie dokie artichokie!']

    AFFIRMATIVE_QUEUE_ANSWERS = ['Roger that. Queued.',
                                 'Affirmative, command queued for execution.',
                                 'We\'ll do that as soon as possible.',
                                 'Copy that, command queued']
    # DEFAULT VALUES
    DEFAULT_STATUS = dict(veer_dir = None,
                          procedure = None,
                          haste = 'normal',
                          bye = False)

    @classmethod
    def set_aerospace(cls, aerospace):
        '''
        All in-game pilots operate in the same aerospace, so a class attribute
        is the cheapest solution.
        '''
        cls.aerospace = aerospace

    def __init__(self, plane):
        self.plane = plane
        self.target_conf = TargetConfiguration(self)
        self._reset_status()
        self._set_target_conf_to_current()
        self.checker = checker.Checker(self)
        self.navigator = navigator.Navigator(self)
        self.executer = executer.Executer(self)

    def _reset_status(self):
        '''
        Reset the ``pilot.status`` dictionary to it default values IN_PLACE.
        [this is so that other classes can keep a pointer to the dictionary]
        '''
        try:
            for k, v in self.DEFAULT_STATUS.items():
                self.status[k] = v
        except AttributeError:  #not created yet
            self.status = self.DEFAULT_STATUS.copy()

    def _set_target_conf_to_current(self):
        '''
        Set the target configuration identical to present aeroplane one.
        '''
        for k, v in self.plane.get_current_configuration():
            setattr(self.target_conf, k, v)

    def _adjust_to_valid_FL(self):
        '''
        Adjust altitude to match a valid flight level.
        '''
        min_altitude = self.navigator.get_required_minimum_altitude()
        if self.plane.position.z < min_altitude:
            self.target_conf['altitude'] = min_altitude
        else:
            extra = self.plane.position.z % 500
            extra = -extra if extra < 250 else 500-extra
            self.target_conf['altitude'] = self.plane.position.z + extra

    def _veer(self):
        '''
        Make the plane turn.
        '''
        # The tightness of the curve is given by the kind of situation the
        # aeroplane is in.
        if self.plane.tcas.state == True:
            veer_type = 'emergency'
        elif self.status['expedite'] == True:
            veer_type = 'expedite'
        else:
            veer_type = 'normal'
        # Unless already specified, set the veering_direction
        if not self.status['veer_dir']:
            self.status['veer_dir'] = \
                        self.navigator.shortest_veering_direction()




        type_ = self.status['haste']
        abs_ang_speed = self.navigator.get_veering_angular_velocity(type_)
        angular_speed = abs_ang_speed * -self.status['veer_dir']
        axis = Vector3(0,0,1)
        amount = angular_speed * self.PING_IN_SECONDS
        self.plane.velocity = self.plane.velocity.rotate_around(axis, amount)

    def _dampen(self, previous_conf):
        '''
        Prevent the aeroplane to "overshoot" its target configuration.
        '''
        pl = self.plane
        p_alt = previous_conf['altitude']
        p_head = previous_conf['heading']
        p_speed = previous_conf['speed']
        # Heading dampener (act on velocity vector)
        t_head = self.target_conf.heading
        if heading_in_between((p_head, pl.heading), t_head):
            mag = abs(Vector2(*pl.velocity.xy))
            theta = radians(90-t_head)
            pl.velocity.x = cos(theta)*mag
            pl.velocity.y = sin(theta)*mag
            self.target_conf['heading'] = pl.heading  #Fixes decimal approx.
        # Speed dampener (act on velocity vector)
        t_speed = self.target_conf.speed
        if in_between((p_speed, pl.speed), t_speed):
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
        t_alt = self.target_conf.altitude
        if in_between((p_alt, pl.altitude), t_alt):
            pl.position.z = t_alt
            pl.velocity.z = 0
        # Actions to be performed if all orders have been executed
        if self.target_conf.is_reached() \
                and not (self.status['procedure'] or self.status['bye']):
            pl.flags.reset()
            self._reset_status()

    def _manoeuvre(self):
        '''
        Manoeuvre the aircraft in order to reach the desired target
        configuration.
        '''
        pl = self.plane
        # Store initial values for self._dampen()
        initial_conf = pl.get_current_configuration()
        if pl.heading != self.target_conf['heading']:
            self.veer()
        if pl.altitude != self.target_conf['altitude']:
            # Descending or ascending?
            index = pl.altitude < self.target_conf['altitude']
            z_acc = pl.climb_rate_accels[index] * self.PING_IN_SECONDS
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
            gr_acc = pl.ground_accels[index] * self.PING_IN_SECONDS
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
        pl.position += pl.velocity * self.PING_IN_SECONDS
        self._dampen(initial_conf)

    def do(self, commands):
        '''
        Perform an order issued by the player.
        Input is a list of triplets each of them in the format:
        [command, [arg1, arg2, ...], [flag1, flag2, ...]].
        Return (boolean, message).
        '''
        # Transform the commands in a more suitable dictionary form..
        commands = dict([(a, (b, c)) for a, b, c in commands])
        # ...perform validity checks...
        check = self.checker.check(commands)
        if check != True:
            return False, check
        # ..and eventually execute the commands!
        return True, self.executer.execute(commands)

    def say(self, what, colour):
        '''
        Output a message on the console.
        '''
        self.plane.aerospace.gamelogic.say(self.plane.callsign, what, colour)

    def update(self):
        '''
        Modify aeroplane configuration according to pilot's instructions.
        '''
        # Run the TCAS subroutine, which can override any order given to the
        # pilot in case of risk of imminent collision
        self.plane.tcas.update()
        # Decide how to handle the aeroplane:
        st = self.status
        if st['procedure']:
            st['procedure'].update()
        self._manoeuvre()