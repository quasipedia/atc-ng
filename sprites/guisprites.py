#!/usr/bin/env python
# -*- coding: utf-8  -*-
'''
Provides the sprite classes used in the radar window.

These are: flight strips, airport maps,
'''

import os.path as path

import pygame.sprite
from pygame.locals import *
from pkg_resources import resource_stream  #@UnresolvedImport

import lib.utils as U
from engine.settings import settings as S

__author__ = "Mac Ryan"
__copyright__ = "Copyright 2011, Mac Ryan"
__license__ = "GPL v3"
#__version__ = "<dev>"
#__date__ = "<unknown>"
__maintainer__ = "Mac Ryan"
__email__ = "quasipedia@gmail.com"
__status__ = "Development"


class StripsGroup(pygame.sprite.RenderUpdates):

    '''
    Sprite container for Flight strips.
    '''

    def update(self, *args):
        cmp = lambda a,b : U.rint(b.plane.time_last_cmd - a.plane.time_last_cmd)
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
        self.image = pygame.surface.Surface(S.SCORE_RECT.size, SRCALPHA)
        self.rect = self.image.get_rect()
        self.score = self.gamelogic.score
        self.fontobj = pygame.font.Font(S.MAIN_FONT, U.rint(self.rect.h * 0.8))

    def update(self):
        STEP = U.rint(S.PING_PERIOD / 1000.0 + 1)  #arbitrary: ping in sec + 1
        self.image.fill(S.BLACK)
        delta = U.rint(self.gamelogic.score) - self.score
        if abs(delta) < STEP:
            colour = S.WHITE
            variation = delta
        elif delta > 0:
            colour = S.OK_COLOUR
            variation = STEP
        else:
            colour = S.KO_COLOUR
            variation = -STEP
        self.score += variation
        score = str(self.score).zfill(6)
        score_img = self.fontobj.render(score, True, colour)
        score_img.subsurface(score_img.get_bounding_rect()).copy()
        pos = U.get_rect_at_centered_pos(score_img, self.rect.center)
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
        self.image.blit(self.render_text('large', S.BLACK, plane.icao),
                        (self.offset, self.offset))
        task = '%s ] %s' % (plane.origin, plane.destination)
        self.image.blit(self.render_text('small', S.BLACK, task),
                        (S.STRIPS_RECT.w*0.60, self.offset))
        self.image.blit(self.render_text('small', S.BLACK, plane.callsign),
                        self.callsign_position)
        # Save the empty one as bkground
        self.bkground = self.image.copy()
        # Initial position
        self.rect = pygame.rect.Rect(0, 0, S.STRIPS_RECT.w, self.strip_h)

    @classmethod
    def initialise(cls):
        '''
        Initialisation method, called at import time.
        '''
        tmp = cls.__get_fontobj('large')
        l_height = tmp.render('M', True, S.WHITE).get_bounding_rect().h
        tmp = cls.__get_fontobj('small')
        s_height = tmp.render('M', True, S.WHITE).get_bounding_rect().h
        cls.strip_h = 2 * l_height + 3 * cls.offset
        for fname in ('drop-black.png', 'drop-green.png',
                      'drop-red.png', 'drop-yellow.png',
                      'master-alarm-off.png', 'master-alarm-on.png',
                      'expedite-off.png', 'expedite-on.png'):
            data = resource_stream(__name__, path.join('data', fname))
            image = pygame.image.load(data)
            if 'drop' in fname or 'alarm' in fname:
                height = float(l_height)
            else:
                height = float(s_height)
            new_size = (int(height / image.get_height() * image.get_width()),
                        int(height))
            image = pygame.transform.smoothscale(image, new_size)
            name = fname.split('.')[0].replace('-', '_')
            setattr(cls, name, image)
        cls.drop_position = (
            S.STRIPS_RECT.w * 0.55 - cls.drop_red.get_width() / 2,
            cls.offset)
        cls.expedite_position = (
            S.STRIPS_RECT.w - cls.offset - cls.expedite_on.get_width(),
            cls.offset)
        cls.fuel_data_position = (
            S.STRIPS_RECT.w * 0.60,
            cls.offset + l_height - s_height)
        cls.callsign_position = (
            cls.offset,
            cls.offset + l_height + cls.offset)
        cls.order_being_processed_position = (
            cls.offset,
            cls.strip_h - cls.offset - s_height)
        cls.master_alarm_position = (
            S.STRIPS_RECT.w - cls.offset - cls.master_alarm_on.get_width(),
            cls.offset + l_height + cls.offset)

    @classmethod
    def __get_fontobj(cls, size_str):
        '''
        Return the appropriate font object.
        '''
        if size_str not in cls.font_objects.keys():
            # set the big font
            size = 1
            while True:
                fontobj = pygame.font.Font(S.MAIN_FONT, size)
                w,h = fontobj.render('XXX0000', True, S.WHITE).get_size()
                if w > S.STRIPS_RECT.w/2 - cls.offset - cls.margin:
                    break
                last_ok = fontobj
                size += 1
            cls.font_objects['large'] = last_ok
            # set the small font
            cls.font_objects['small'] = pygame.font.Font(S.MAIN_FONT,
                                                         U.rint(size/3.0))
        return cls.font_objects[size_str]

    @classmethod
    def __get_empty(cls, type_):
        '''
        Generate an empty flight-strip.
        Return the pygame.surface object of appropriate colour and dimenstion.
        '''
        if type_ not in cls.empty_sprites.keys():
            if type_ == S.OUTBOUND:
                color = S.PALE_RED
            elif type_ == S.INBOUND:
                color = S.PALE_GREEN
            else:
                raise RuntimeError('Unknown type of empty strip.')
            s = pygame.surface.Surface(
                   (S.STRIPS_RECT.w, cls.strip_h), SRCALPHA)
            for x in (cls.offset, S.STRIPS_RECT.w - cls.offset):
                for y in (cls.offset, cls.strip_h - cls.offset):
                    pygame.draw.circle(s, color, (x,y), cls.radius)
            r = pygame.rect.Rect(cls.margin, cls.offset,
                S.STRIPS_RECT.w-2*cls.margin, cls.strip_h-2*cls.offset)
            pygame.draw.rect(s, color, r)
            r = pygame.rect.Rect(cls.offset, cls.margin,
                S.STRIPS_RECT.w-2*cls.offset, cls.strip_h-2*cls.margin)
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

    def update(self):
        self.image = self.bkground.copy()
        fuel_msg = 'FUEL: %s (%s)' % (str(U.rint(self.plane.fuel)).zfill(3),
                    str(U.rint(self.plane.fuel_delta)).zfill(3))
        color = S.DARK_GREEN if self.plane.fuel > 100 else S.KO_COLOUR
        img = self.render_text('small', color, fuel_msg)
        self.image.blit(img, self.fuel_data_position)
        self.rect.y += cmp(self.target_y, self.rect.y) * \
                       min(3, abs(self.rect.y - self.target_y))
        # Master alarm
        if self.plane.flags.collision or not self.plane.fuel:
            img = self.master_alarm_on
        else:
            img = self.master_alarm_off
        self.image.blit(img, self.master_alarm_position)
        # Expedite arrow
        if self.plane.pilot.status['haste'] in ('expedite', 'emergency'):
            img = self.expedite_on
        else:
            img = self.expedite_off
        self.image.blit(img, self.expedite_position)
        # Drop
        if self.plane.fuel_delta > 0:
            img = self.drop_green
        elif self.plane.fuel:
            img = self.drop_yellow
        else:
            img = self.drop_red
        self.image.blit(img, self.drop_position)
        # Last order
        text = self.plane.pilot.order_being_processed
        if text:
            text = self.render_text('small', S.GRAY, text)
            self.image.blit(text, self.order_being_processed_position)

# MODULE INITIALISATION
FlightStrip.initialise()