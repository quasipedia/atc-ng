#!/usr/bin/env python
# -*- coding: utf-8  -*-
'''
Code for the ATC-NG waypoints (entry/exit gates and beacons)
'''

from locals import *
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

    def __init__(self, name, radial, alignment, width):
        self.name = name
        self.radial = radial % 360
        self.aligment = alignment % 180
        self.width = width

    def draw(self, radar_surface):
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
        gate_width_px = rint(self.width/METRES_PER_PIXELS)
        gate_length_px = RADAR_RECT.h/4
        aaf = 5  #anti-alias factor
        g_img = pygame.surface.Surface((gate_width_px*aaf,
                                        gate_length_px*aaf), SRCALPHA)
        pygame.draw.line(g_img, GRAY, (aaf, 0),
                                  (aaf, gate_length_px*aaf), aaf)
        pygame.draw.line(g_img, GRAY, (gate_width_px*aaf-aaf, 0),
                                  (gate_width_px*aaf-aaf, gate_length_px*aaf), aaf)
        g_img = pygame.transform.rotate(g_img, -self.aligment)
        g_img = g_img.subsurface(g_img.get_bounding_rect()).copy()
        r = g_img.get_rect()
        g_img = pygame.transform.smoothscale(g_img, (rint(r.w*1.0/aaf),
                                                     rint(r.h*1.0/aaf)))
        g_rect = g_img.get_rect()
        radar_surface.blit(g_img, (x-g_rect.centerx, y-g_rect.centery))
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
        radar_surface.blit(label, (x,y))
