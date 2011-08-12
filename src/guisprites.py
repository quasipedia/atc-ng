#!/usr/bin/env python
# -*- coding: utf-8  -*-
'''
Provides the sprite classes used in the radar window.

These are: flight strips, aeroport maps,
'''

from locals import *
import pygame.sprite

__author__ = "Mac Ryan"
__copyright__ = "Copyright 2011, Mac Ryan"
__license__ = "GPL v3"
#__version__ = "1.0.0"
__maintainer__ = "Mac Ryan"
__email__ = "quasipedia@gmail.com"
__status__ = "Development"


class StripsGroup(pygame.sprite.RenderUpdates):

    def draw(self, surface):
        cmp = lambda a,b : rint(b.plane.time_last_cmd - a.plane.time_last_cmd)
        ordered = sorted(self.sprites(), cmp)
        y = 0
        for sprite in ordered:
            print y
            sprite.rect.y = y
            y += sprite.rect.h
        super(StripsGroup, self).draw(surface)

class FlightStrip(pygame.sprite.Sprite):

    '''
    Flight progress strips appears to the left of the GUI.
    '''

    def __init__(self, plane):
        super(FlightStrip, self).__init__()
        self.plane = plane
        self.__set_font_object()
        # Draw fixed part of the strip
        self.image = pygame.surface.Surface((STRIPS_RECT.w, 50))
        w, h = self.image.get_size()
        self.image.fill(BLACK)
        border_rect = pygame.rect.Rect(1, 1, w-2, h-2)
        pygame.draw.rect(self.image, WHITE, border_rect, 1)
        self.image.blit(self.fontobj.render(plane.icao, True, WHITE), (3,3))
        self.rect = pygame.rect.Rect(0, 0, w, h)

    @classmethod
    def __set_font_object(cls):
        '''
        Automatically set the font to the appropriate size.
        '''
        size = 1
        while True:
            fontobj = pygame.font.Font('../data/ex_modenine.ttf', size)
            w,h = fontobj.render('XXX0000', True, WHITE).get_size()
            if w > STRIPS_RECT.w/2 - 10:
                break
            last_ok = fontobj
            size += 1
        cls.fontobj = last_ok

    def draw(self):
        pass
