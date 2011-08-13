#!/usr/bin/env python
# -*- coding: utf-8  -*-
'''
Aeroports modelling of the ATC simulation game.
'''

from euclid import Vector3
from math import radians

__author__ = "Mac Ryan"
__copyright__ = "Copyright 2011, Mac Ryan"
__license__ = "GPL v3"
#__version__ = "1.0.0"
__maintainer__ = "Mac Ryan"
__email__ = "quasipedia@gmail.com"
__status__ = "Development"


class Aeroport(object):

    '''
    Modelling description of the aeroport. Note that the runaway naming happens
    here and not in the Runway class.
    '''

    def __init__(self, centre_pos, iata, asphalt_strips):
        self.iata = iata
        self.asphalt_strips = asphalt_strips
        self.centre_pos = Vector3(*centre_pos)
        self.__define_points()

    def __sort_left_to_right(self, keys, runways):
        '''
        Sort in place `keys` according to left-to-right order from a landing
        pilot's perspective:
        - runways : dictionary of runways
        - keys : list of keys (from runway)
        See my question here: http://gamedev.stackexchange.com/q/15920/8275
        '''
        determinant = lambda v1, v2 : v1.x*v2.y - v1.y*v2.x
        centre_vector = lambda p1, p2 : Vector3(p2.x-p1.x, p2.y-p1.y)
        ils = lambda x : runways[x]['ils']
        centre = lambda x : runways[x]['to_point']
        compare = lambda x,y : cmp(determinant(ils(x),
                                   centre_vector(centre(x),centre(y))), 0)
        keys.sort(cmp=compare, reverse=True)

    def __define_points(self):
        '''
        A touch down represent the place where a landing plane (or a departing
        one) will touch down (or take off). Programmatically is a dictionary
        structured as follow:
        { runway_name : { location  : (x,y,z)    # location on map
                          ils       : Vector3()  # vector to intercept for land
                          to_point  : (z,y,z)    # take off point
        '''
        runways = {}
        # First create all runaways with temp names in the form `XX_n`...
        for n, strip in enumerate(self.asphalt_strips):
            abs_centre = self.centre_pos + strip.centre_pos
            for rot in (strip.orientation, 180+strip.orientation):
                tmp = {}
                offset = Vector3(1,0,0)
                r_ang = radians(270-rot)
                offset = offset.rotate_around(Vector3(0,0,1), r_ang)
                tmp['ils'] = offset
                offset *= strip.length / 2
                tmp['location'] = (abs_centre + offset).xyz
                tmp['to_point'] = abs_centre
                runways['%s_%d' % (str(rot/10).zfill(2), n)] = tmp
        # ...then change the names to the permanent one in the form XXL|C|R
        self.runways = {}
        for angle in range(0, 360):
            match = str(angle/10).zfill(2)
            old_keys = [key for key in runways.keys() if key.find(match) == 0]
            l = len(old_keys)
            if l == 0:
                continue
            elif len(old_keys) == 1:
                new_keys = [match]
            elif 1 < l < 4:
                self.__sort_left_to_right(old_keys, runways)
                letters = 'LR' if l == 2 else 'LCR'
                numeric = match if match != '00' else '36'
                new_keys = ['%s%s' % (numeric, letter) for letter in letters]
            else:
                raise BaseException('Max 3 runways with the same orientation!')
            # Set the property of the Aeroport object
            for n, old_key in enumerate(old_keys):
                new_key = new_keys[n]
                self.runways[new_key] = runways[old_key]


class AsphaltStrip(object):

    '''
    Base class used as a building element for aeroports. Each AsphaltStrip()
    object will generate two landing runways (the two direction one can land on
    it). Example: if the orientation is 90° the landing runaways will be 09 and
    27.
    '''

    def __init__(self, orientation, length=1000, centre_pos=(0, 0), width=30):
        if orientation % 10 != 0:
            raise BaseException('Runways must be at multiples of 10°.')
        orientation %= 180  #standardise orientation to 0-180 degrees
        self.orientation = orientation         #in degrees
        self.length = length                   #in metres
        self.width = width                     #in metres
        self.centre_pos = Vector3(*centre_pos) #mt. relative to the port centre