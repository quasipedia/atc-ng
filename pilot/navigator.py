#!/usr/bin/env python
# -*- coding: utf-8  -*-
'''
Provide support for pilot's navigation (calculate distances, radii, etc...).
'''

from lib.utils import *
from lib.euclid import Vector3

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
        self.mp = self.pilot.get_point_ahead(dist_from_plane)
        if self.pilot.navigator.ceck_overshot(self.mp) == True:
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
        self.bp = self.pilot.get_point_ahead(distance)

    def make_decision(self):
        '''
        Make a decision if trying to land or not depending on whether the
        target runway is free or not. If free, return True and mark runway
        busy, otherwise return False.
        '''
        rman = self.plane.aerospace.runways_manager
        if rman.check_runway_free(self.port, self.rnwy):
            rman.use_runway(self.port, self.rnwy, self.plane)
            full_length_speed = float(self.rnwy['length'])/RUNWAY_BUSY_TIME
            self.taxiing_data = dict(
                 speed = min(self.plane.landing_speed, full_length_speed),
                 timer = RUNWAY_BUSY_TIME)
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
        return self.fd * sin(radians(SLOPE_ANGLE)) + self.foot.z


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
        if port not in self.aerospace.airports:
            return 'airport %s is not on the map!' % port
        if runway not in self.aerospace.airports[port].runways:
            return 'airport %s does not have runway %s!' % (port, runway)
        return True

    def check_overshot(self, point):
        '''
        Return True if the plane has overshot (i.e. flown past) the ``point``.
        '''
        return is_behind(self.plane.velocity, self.plane.position, point)

    def get_point_ahead(self, distance):
        '''
        Return the coordinates of a point which is X metres ahead of current
        flown point (assumes velocity vector won't change, of course).
        '''
        pl = self.plane
        return pl.position + (pl.velocity.normalized() * distance)

    def get_course_towards(self, coords=None):
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

    def get_aversion_course(self, point):
        '''
        Calculate the best course to avoid the colliding plane(s).
        This is done by:
        - Reducing speed to the minimum for increased manoeuvrability
        - Calculating opposite vectors to colliding planes and assigning to
          them a magnitude which is proportional to their distance.
        - Setting the course for the resulting vector.
        '''
        plane = self.plane
        pilot = self.pilot
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
        max_up = min(plane.max_altitude, MAX_FLIGHT_LEVEL)
        tc['altitude'] = max_up if vector.z > 0 else MIN_FLIGHT_LEVEL
        tc['speed'] = plane.min_speed
        tc['heading'] = (90-degrees(atan2(vector.y, vector.x)))%360
        pilot.veering_direction = pilot.shortest_veering_direction()

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
        theta = (self.plane.heading - self.target_conf['heading']) % 360
        return self.LEFT if theta < 180 else self.RIGHT

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
        acc_module = (g_to_mks(max_manouvering_g)**2-g_to_mks(1)**2)**0.5
        return acc_module/speed
