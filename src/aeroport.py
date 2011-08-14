#!/usr/bin/env python
# -*- coding: utf-8  -*-
'''
Aeroports modelling of the ATC simulation game.
'''

from locals import *
from euclid import Vector3
from math import radians
import pygame.font
from pygame.locals import *
import pygame.surface
import pygame.transform

__author__ = "Mac Ryan"
__copyright__ = "Copyright 2011, Mac Ryan"
__license__ = "GPL v3"
#__version__ = "1.0.0"
__maintainer__ = "Mac Ryan"
__email__ = "quasipedia@gmail.com"
__status__ = "Development"


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
        self.centre_pos = Vector3(*centre_pos) #in mt from aribitrary point


class Aeroport(object):

    '''
    Modelling description of the aeroport. Note that the runaway naming happens
    here and not in the Runway class.
    '''

    def __init__(self, location, iata, name, asphalt_strips):
        self.iata = iata
        self.name = name
        self.asphalt_strips = asphalt_strips
        self.location = Vector3(*location)
        self.__define_points()
        self.__plain_image = None
        self.__labelled_image = None

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
            for rot in (strip.orientation, 180+strip.orientation):
                tmp = {}
                offset = Vector3(1,0,0)
                r_ang = radians(270-rot)
                offset = offset.rotate_around(Vector3(0,0,1), r_ang)
                tmp['ils'] = offset
                offset *= strip.length / 2
                tmp['location'] = strip.centre_pos + offset
                tmp['to_point'] = strip.centre_pos
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

    def get_image(self, square_side=None, scale=None, with_labels=False):
        '''
        Return a pygame squared surface with the map of the aeroport.
        A master image is stored internally at 1mt:1px scale, either argument
        is provided, the method will return either the bounding image scaled
        as requested, either a squared image with the side measuring
        `square_side` pixels.
        '''
        # Helper function that blits on the canvas fixing the y axis and using
        # the centre of the blitted image as reference point
        def my_blit(dest, source, pos):
            x,y = pos
            x,y = x-source.get_width()/2, y+source.get_height()/2
            y = -(y-dest.get_height())
            dest.blit(source, (x,y))
        if bool(square_side) == bool(scale):
            msg = 'Either `square_side` XOR `scale` MUST be specified'
            raise BaseException(msg)
        # The master images hasn't yet been generated...
        if not self.__plain_image or not self.__labelled_image:
            strips = self.asphalt_strips
            xes = [s.centre_pos[0] for s in strips]
            ys = [s.centre_pos[1] for s in strips]
            min_x, max_x = min(xes), max(xes)
            min_y, max_y = min(ys), max(ys)
            max_len = max([s.length for s in strips])
            width = max_x-min_x+2*max_len
            height = max_y-min_y+2*max_len
            trasl = Vector3(max_len-min_x, max_len-min_y)
            a_canvas = pygame.surface.Surface((width, height), SRCALPHA)
            for strip in strips:
                size = (strip.width, strip.length)
                image = pygame.surface.Surface(size, SRCALPHA)
                image.fill(GRAY)
                image = pygame.transform.rotate(image, -strip.orientation)
                my_blit(a_canvas, image, (strip.centre_pos+trasl).xy)
            # Store the label-less image
            self.__plain_image = a_canvas.subsurface(
                                 a_canvas.get_bounding_rect()).copy()
            # Add the the labels
            pi = self.__plain_image
            font_size = max(pi.get_width(), pi.get_height()) / 16
            fontobj = pygame.font.Font(MAIN_FONT, font_size)
            for k, v in self.runways.items():
                label = fontobj.render(k, True, WHITE)
                loc = v['location'] + trasl + \
                      v['ils'].normalized() * font_size * 1.2
                my_blit(a_canvas, label, loc.xy)
            self.__labelled_image = a_canvas.subsurface(
                                    a_canvas.get_bounding_rect()).copy()
        # THIS IS THE BIT THAT RUNS AT EACH CALL
        img = (self.__plain_image if with_labels == False
                                  else self.__labelled_image).copy()
        w, h = img.get_width(), img.get_height()
        if square_side:
            ratio = float(square_side)/max(w,h)
            tmp = pygame.transform.smoothscale(img,
                                               (rint(w*ratio), rint(h*ratio)))
            w, h = tmp.get_width(), tmp.get_height()
            pos = ((square_side-w)/2, (square_side-h)/2, )
            img = pygame.surface.Surface((square_side, square_side), SRCALPHA)
            img.blit(tmp, pos)
        if scale:
            img = pygame.transform.smoothscale(img,
                                               (rint(w*scale), rint(h*scale)))
        return img

    def del_cached_images(self):
        '''
        Cached images are BIG. It's a good idea to flush them when they are not
        to be used again.
        '''
        self.__plain_image = None
        self.__labelled_image = None