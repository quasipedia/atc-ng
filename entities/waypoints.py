#!/usr/bin/env python
# -*- coding: utf-8  -*-
'''
Code for the ATC-NG waypoints (entry/exit gates and beacons)
'''

from engine.settings import *
from math import sin, cos, radians
from pygame.locals import *
import pygame.draw
import pygame.transform

__author__ = "Mac Ryan"
__copyright__ = "Copyright 2011, Mac Ryan"
#__credits__ = ["Name Lastname", "Name Lastname"]
__license__ = "GPL v3"
#__version__ = "1.0.0"
__maintainer__ = "Mac Ryan"
__email__ = "quasipedia@gmail.com"
__status__ = "Development"


class Gate(object):

    '''
    A gate represents an valid opening of the monitored airspace.
    Basically all entering and exiting planes should do so from a gate.
    '''

    def __init__(self, name, radial, heading, width):
        self.name = name
        self.radial = radial % 360
        self.heading = heading
        self.width = width

    def draw(self, surface):
        '''
        Blit self on radar surface.
        '''
        # Convert "radial": from "CW deg from North" to "CCW rad from East"
        convert_angle = lambda ang : radians(90-ang)
        radial = convert_angle(self.radial)
        # Find the pixel coordinates of the centre of the gate
        s, c = sin(radial), cos(radial)
        ss, cs = cmp(s, 0), cmp(c, 0)
        sa, ca = abs(s), abs(c)
        side = cmp(sa, ca)  #-1 for sides, 0 for corner, 1 or top or bottom
        rr = RADAR_RANGE
        x = cs * (rr if side <= 0 else rr/sa * ca) + rr
        y = ss * (rr if side >= 0 else rr/ca * sa) + rr
        x, y = sc((x, y))
        # GATE
        # In order to facilitate blitting information on the orientation of the
        # gate, we create the image already rotated 90° clockwise by swapping
        # width and height...
        gate_width_px = rint(self.width/METRES_PER_PIXELS)
        gate_length_px = RADAR_RECT.h/4
        aaf = 5  #anti-alias factor
        g_img = pygame.surface.Surface((gate_length_px*aaf,
                                        gate_width_px*aaf), SRCALPHA)
        # boundaries of the gate
        pygame.draw.line(g_img, GRAY, (0, aaf),
                              (gate_length_px*aaf, aaf), aaf)
        pygame.draw.line(g_img, GRAY, (0, gate_width_px*aaf-aaf),
                              (gate_length_px*aaf, gate_width_px*aaf-aaf), aaf)
        # info on orientation
        fontobj = pygame.font.Font(MAIN_FONT, HUD_INFO_FONT_SIZE*aaf)
        label = fontobj.render(str(self.heading).zfill(3), True, GRAY)
        label = label.subsurface(label.get_bounding_rect())
        w, h = label.get_size()
        ypsilon = rint(gate_width_px*aaf/2.0-h/2)
        g_img.blit(label, (0, ypsilon))
        g_img.blit(label, (gate_length_px*aaf-w, ypsilon))
        # tranformation and blitting
        rotang = 90 if 0<= self.heading < 180 else 270
        g_img = pygame.transform.rotate(g_img, rotang-self.heading)
        g_img = g_img.subsurface(g_img.get_bounding_rect()).copy()
        r = g_img.get_rect()
        g_img = pygame.transform.smoothscale(g_img, (rint(r.w*1.0/aaf),
                                                     rint(r.h*1.0/aaf)))
        g_rect = g_img.get_rect()
        surface.blit(g_img, (x-g_rect.centerx, y-g_rect.centery))
        # LABEL
        fontobj = pygame.font.Font(MAIN_FONT, HUD_INFO_FONT_SIZE)
        label = fontobj.render(self.name, True, RED)
        w, h = label.get_size()
        signed_offset = lambda n : cmp(1,n)*w
        # For gates near 45° we want labe treated as "corner", a delta of 0.12
        # make this work 40°-50° (0.25, 0.37, 0.48) for following 5° increments
        if abs(sa-ca) < 0.12:
            side = 0
        x += (signed_offset(x) if side <=0 else 0) - w/2
        y += (signed_offset(y) if side >=0 else 0) - h/2
        surface.blit(label, (x,y))


class Beacon(object):

    '''
    A beacon is a point on the ground that is known to aeroplanes and can be
    used to set heading for. [AZA0019 HEADING NDB4]
    '''

    def __init__(self, id, location):
        self.id = id
        self.location = location

    def draw(self, surface):
        pos = sc(self.location)
        pygame.draw.circle(surface, GRAY, pos, 2)
        pygame.draw.circle(surface, GRAY, pos, 6, 1)
        fontobj = pygame.font.Font(MAIN_FONT, HUD_INFO_FONT_SIZE)
        label = fontobj.render(self.id, True, BLUE)
        label = label.subsurface(label.get_bounding_rect()).copy()
        w, h = label.get_size()
        x, y = pos
        # In order to keep the crammed central space free, beacons labels are
        # always placed towards the edges of the radar screen, if possible.
        offsets = [rint(6+w/3), -rint(6+w/3)-w]
        index = x < RADAR_RECT.w/2
        if not (0 < x+offsets[index] and x+offsets[index]+w < RADAR_RECT.w):
            index = not index
        surface.blit(label, (x+offsets[index], y-h/2))
