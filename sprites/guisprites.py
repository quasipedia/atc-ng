#!/usr/bin/env python
# -*- coding: utf-8  -*-
'''
Provides the sprite classes used in the radar window.

These are: flight strips, aeroport maps,
'''

from engine.settings import *
from lib.utils import *
from pygame.locals import *
import pygame.sprite

__author__ = "Mac Ryan"
__copyright__ = "Copyright 2011, Mac Ryan"
__license__ = "GPL v3"
#__version__ = "1.0.0"
__maintainer__ = "Mac Ryan"
__email__ = "quasipedia@gmail.com"
__status__ = "Development"


class StripsGroup(pygame.sprite.RenderUpdates):

    '''
    Sprite container for Flight strips.
    '''

    def update(self, *args):
        cmp = lambda a,b : rint(b.plane.time_last_cmd - a.plane.time_last_cmd)
        ordered = sorted(self.sprites(), cmp)
        for i, sprite in enumerate(ordered):
            sprite.target_y = i*FlightStrip.strip_h
            sprite.update()

    def remove_strip(self, plane):
        '''
        Remove a strip from the sprite group based on its plane object.
        '''
        for sprite in self.sprites():
            if sprite.plane == plane:
                sprite.kill()
                return


class Score(pygame.sprite.Sprite):

    '''
    Score value displayed on screen.
    '''

    def __init__(self, gamelogic):
        super(Score, self).__init__()
        self.gamelogic = gamelogic
        self.image = pygame.surface.Surface(SCORE_RECT.size, SRCALPHA)
        self.rect = self.image.get_rect()
        self.score = self.gamelogic.score
        self.fontobj = pygame.font.Font(MAIN_FONT, rint(self.rect.h * 0.8))
        font_height = self.fontobj.get_height()

    def update(self):
        self.image.fill(BLACK)
        if self.gamelogic.score == self.score:
            colour = WHITE
        elif self.gamelogic.score < self.score:
            colour = RED
            self.score -= 1
        else:
            colour = GREEN
            self.score += 1
        score = str(self.score).zfill(6)
        score_img = self.fontobj.render(score, True, colour)
        score_img.subsurface(score_img.get_bounding_rect()).copy()
        pos = get_rect_at_centered_pos(score_img, self.rect.center)
        self.image.blit(score_img, pos)


class FlightStrip(pygame.sprite.Sprite):

    '''
    Flight progress strips appears to the left of the GUI.
    '''

    empty_sprites = {}
    font_objects = {}
    radius = 7
    margin = 2
    offset = margin+radius

    def __init__(self, plane, status):
        super(FlightStrip, self).__init__()
        self.plane = plane
        # Draw fixed part of the strip
        self.image = self.__get_empty(status)
        self.image.blit(self.render_text('large', BLACK, plane.icao),
                        (self.offset, self.offset))
        task = '%s ] %s' % (plane.origin, plane.destination)
        self.image.blit(self.render_text('small', BLACK, task),
                        (STRIPS_RECT.w*0.60, self.offset))
        # Save the empty one as bkground
        self.bkground = self.image.copy()
        # Initial position
        self.rect = pygame.rect.Rect(0, 0, STRIPS_RECT.w, self.strip_h)

    @classmethod
    def __get_fontobj(cls, size_str):
        '''
        Return the appropriate font object.
        '''
        if size_str not in cls.font_objects.keys():
            # set the big font
            size = 1
            while True:
                fontobj = pygame.font.Font(MAIN_FONT, size)
                w,h = fontobj.render('XXX0000', True, WHITE).get_size()
                if w > STRIPS_RECT.w/2 - cls.offset - cls.margin:
                    break
                last_ok = fontobj
                size += 1
            cls.font_objects['large'] = last_ok
            # set the small font
            cls.font_objects['small'] = pygame.font.Font(MAIN_FONT,
                                                         rint(size/3.0))
        return cls.font_objects[size_str]

    @classmethod
    def __get_empty(cls, type_):
        '''
        Generate an empty flight-strip.
        Return the pygame.surface object of appropriate colour and dimenstion.
        '''
        tmp = cls.render_text('large', WHITE, 'XXX0000')
        cls.strip_h = tmp.get_height() + 2*cls.offset
        if type_ not in cls.empty_sprites.keys():
            if type_ == OUTBOUND:
                color = PALE_RED
            elif type_ == INBOUND:
                color = PALE_GREEN
            else:
                raise BaseException('Unknown type of empty strip.')
            s = pygame.surface.Surface((STRIPS_RECT.w, cls.strip_h), SRCALPHA)
            for x in (cls.offset, STRIPS_RECT.w-cls.offset):
                for y in (cls.offset, cls.strip_h-cls.offset):
                    pygame.draw.circle(s, color, (x,y), cls.radius)
            r = pygame.rect.Rect(cls.margin, cls.offset,
                STRIPS_RECT.w-2*cls.margin, cls.strip_h-2*cls.offset)
            pygame.draw.rect(s, color, r)
            r = pygame.rect.Rect(cls.offset, cls.margin,
                STRIPS_RECT.w-2*cls.offset, cls.strip_h-2*cls.margin)
            pygame.draw.rect(s, color, r)
            cls.empty_sprites[type_] = s
        return cls.empty_sprites[type_].copy()

    @classmethod
    def render_text(cls, size, color, text):
        '''
        Return a cropped rendered text.
        '''
        fo = cls.__get_fontobj(size)
        img = fo.render(text, True, color)
        return img.subsurface(img.get_bounding_rect()).copy()

    def update(self, *args):
        #TODO: sliding animation
        #TODO: alarm signaller
        self.image = self.bkground.copy()
        fuel_msg = 'FUEL: %s' % str(self.plane.fuel).zfill(4)
        color = DARK_GREEN if self.plane.fuel > 100 else RED
        img = self.render_text('small', color, fuel_msg)
        self.image.blit(img, (STRIPS_RECT.w*0.60,
                              self.strip_h-self.offset-img.get_height()))
        self.rect.y += cmp(self.target_y, self.rect.y) * \
                       min(3, abs(self.rect.y - self.target_y))
