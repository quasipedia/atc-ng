#!/usr/bin/env python
# -*- coding: utf-8  -*-
'''
Provide support for pilot's navigation (calculate distances, radii, etc...).
'''

from math import sin, tan, radians

import lib.utils as U
from engine.settings import settings as S
from engine.logger import log
from lib.euclid import Vector3, Vector2

__author__ = "Mac Ryan"
__copyright__ = "Copyright ©2011, Mac Ryan"
#__credits__ = ["Name Lastname", "Name Lastname"]
__license__ = "GPL v3"
#__version__ = "<dev>"
#__date__ = "<unknown>"
__maintainer__ = "Mac Ryan"
__email__ = "quasipedia@gmail.com"
__status__ = "Development"



class Lander(object):

    '''
    Container class for holding data and functions useful during the landing
    phase.
    '''

    def __init__(self, pilot, port_name, rnwy_name):
        self.pilot = pilot
        self.plane = pilot.plane
        self.port = self.plane.aerospace.airports[port_name]
        self.rnwy = self.port.runways[rnwy_name]
        self.foot = self.rnwy['location'] + self.port.location
        self.ils = self.rnwy['ils']
        self.taxiing_data = None

    def set_intersection_point(self):
        '''
        Set and return self.ip, the 2D intersection point between current
        plane heading and the ILS glide path.
        '''
        pl = self.plane
        p1 = pl.position.xy
        p2 = (pl.position + pl.velocity.normalized()*S.RADAR_RANGE*3).xy
        p3 = self.foot.xy
        p4 = (Vector3(*self.foot) + -self.ils.normalized()*S.RADAR_RANGE*3).xy
        self.ip, comment = U.segment_intersection(p1, p2, p3, p4)
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
        h2 = U.v3_to_heading(self.ils)
        a1 = abs((h1-h2)%360)
        a2 = abs((h2-h1)%360)
        angle = min(a1, a2)
        angle = radians((180 - angle) / 2.0)
        dist_from_ip = radius/tan(angle)
        dist_from_plane = abs(self.ip-self.plane.position)-dist_from_ip
        self.mp = self.pilot.navigator.get_point_ahead(dist_from_plane)
        if self.pilot.navigator.check_overshot(self.mp) == True:
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
            dist += speed * S.PING_IN_SECONDS
            if speed <= pl.landing_speed:
                break
            speed += pl.ground_accels[0] * S.PING_IN_SECONDS
        distance = abs(self.foot - self.plane.position) - dist
        self.bp = self.pilot.navigator.get_point_ahead(distance)

    def make_decision(self):
        '''
        Make a decision if trying to land or not depending on whether the
        target runway is free or not. If free, return True and mark runway
        busy, otherwise return False.
        '''
        rman = self.plane.aerospace.runways_manager
        if rman.check_runway_free(self.port, self.rnwy):
            rman.use_runway(self.port, self.rnwy, self.plane)
            full_length_speed = float(self.rnwy['length'])/S.RUNWAY_BUSY_TIME
            self.taxiing_data = dict(
                 speed = min(self.plane.landing_speed, full_length_speed),
                 timer = S.RUNWAY_BUSY_TIME)
            log.debug('%s *positive* landing decision on %s %s' %
                      (self.plane.icao, self.port.iata, self.rnwy['name']))
            self.plane.flags.locked = True
            return True
        log.debug('%s *negative* landing decision on %s %s' %
                  (self.plane.icao, self.port.iata, self.rnwy['name']))
        msg = 'Somebody is using our landing runway!!!'
        self.plane.pilot._abort_landing(msg)
        return False

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
        return self.fd * sin(radians(S.SLOPE_ANGLE)) + self.foot.z


class Navigator(object):

    '''
    Provide support for pilot's navigation.

    This class only contains ``get`` or ``check``. The first return data in a
    suitable format. The latter return boolean True in case the check resolves
    positively, and another value (might be False or an error message or...)
    otherwise. It is therefore imperative that comparison with checks happens
    with the explicit boolean comparison:

      if check_<whatever>(args) == True:
        <do something>
    '''

    def __init__(self, pilot):
        self.pilot = pilot
        self.plane = pilot.plane

    def check_existing_runway(self, port, runway):
        '''
        Verify that a given port/runway combo actually exist in the aerospace.
        '''
        aspace = self.plane.aerospace
        if port not in aspace.airports:
            return 'airport %s is not on the map!' % port
        if runway not in aspace.airports[port].runways:
            return 'airport %s does not have runway %s!' % (port, runway)
        return True

    def check_overshot(self, point):
        '''
        Return True if the plane has overshot (i.e. flown past) the ``point``.
        '''
        return U.is_behind(self.plane.velocity, self.plane.position, point)

    def check_reachable(self, point, veer_type=None):
        '''
        Return True if the plane can adjust his heading in time to fly over
        point ``point``. Assumes the speed will keep constant during the
        veering.

        If ``veer_type`` is not given, it will default to pilot's haste.
        '''
        # If we connect the plane to the destination point by a veering tangent
        # to the plane velocity (i.e. if we draw the longest possible veering
        # to reach the point, we will discover that the distance between the
        # plane an the target point is D = 2*r*sin(alpha), where r is the
        # veering radius and alpha is the angle between the present velocity
        # vector and the vector to ``point``. This means that for any shorter
        # radius it will be possible to reach the point. So the formula
        # translates in: r < distance / (2*sin(alpha))
        distance = float(abs(point - self.plane.position))
        velocity = Vector2(*self.plane.velocity.xy)
        to_target = Vector2(*(point - self.plane.position).xy)
        alpha = velocity.angle(to_target)
        # Eary retrun in case of the plane is already aligned
        if alpha == 0:
            return True
        min_radius = distance / (sin(alpha) * 2)
        if veer_type is None:
            veer_type = self.pilot.status['haste']
        actual_radius = self.get_veering_radius(veer_type, self.plane.speed)
        return actual_radius <= min_radius

    def check_maybe_reachable(self, point):
        '''
        This is a super-method of ``check_reachable``. It will return True if
        the point is reachable or if speed is decreasing (and therefore it
        might become reachable at a later stage).
        '''
        if self.check_reachable(point) or \
           self.pilot.target_conf.speed < self.plane.speed:
            return True
        return False

    def get_point_ahead(self, distance):
        '''
        Return the coordinates of a point which is X metres ahead of current
        flown point (assumes velocity vector won't change, of course).
        '''
        pl = self.plane
        return pl.position + (pl.velocity.normalized() * distance)

    def get_course_towards(self, point):
        '''
        Get the heading of a direct vector towards a given point.
        '''
        assert isinstance(point, Vector3)
        delta = point - self.plane.position
        return U.v3_to_heading(delta)

    def get_required_minimum_altitude(self):
        '''
        Return the minimum altitude a plane is required to fly at on a given
        ground point.
        '''
        # This method is for the future, when scenarios with minimum flight
        # altitudes will be implemented.
        return 500

    def get_shortest_veering_direction(self):
        '''
        Return self.LEFT or self.RIGHT according to whatever the shortest
        veering to a certain course is.
        '''
        theta = (self.plane.heading - self.pilot.target_conf.heading) % 360
        return S.LEFT if theta < 180 else S.RIGHT

    def get_intersection_point(self, vector, point):
        '''
        Return the intersection point between the projected plane trajectory
        and the line defined by `vector` applied to `point`.
        '''
        if type(point) in (tuple, list):
            point = Vector3(*point)
        p1 = self.plane.position.xy
        p2 = (self.plane.position + self.plane.velocity).xy
        p3 = point.xy
        p4 = (point + vector).xy
        return U.line_intersection(p1, p2, p3, p4)

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
            max_manouvering_g = 1.1547
        elif veer_type == 'expedite':
            max_manouvering_g = 1.4142
        elif veer_type == 'emergency':
            max_manouvering_g = self.plane.max_g
        else:
            raise BaseException('Unknown veer type')
        g_to_mks = lambda x : S.G_GRAVITY * x
        acc_module = (g_to_mks(max_manouvering_g)**2-g_to_mks(1)**2)**0.5
        return acc_module/speed
