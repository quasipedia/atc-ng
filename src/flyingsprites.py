#!/usr/bin/env python
# -*- coding: utf-8  -*-
'''
Provides the sprite classes used in the radar window.

These are: aeroplanes, trailing dots, labels.
'''

from settings import *
from pygame.locals import *
import pygame.sprite
import pygame.surfarray
import pygame.transform
import os

__author__ = "Mac Ryan"
__copyright__ = "Copyright 2011, Mac Ryan"
#__credits__ = ["Name Lastname", "Name Lastname"]
__license__ = "GPL v3"
#__version__ = "1.0.0"
__maintainer__ = "Mac Ryan"
__email__ = "quasipedia@gmail.com"
__status__ = "Development"


class SuperSprite(pygame.sprite.Sprite):

    '''
    Base class to derive the in-game sprites in ATC.
    Add spritesheet manipulation capability.
    '''

    def load_sprite_sheet(self, fname, colorkey=False, directory='../data'):
        '''
        Return the specified sprite sheet as loaded surface.
        '''
        fname = os.path.join(directory, fname)
        sheet = pygame.image.load(fname)
        if colorkey:
            if colorkey == -1:
            # If the colour key is -1, set it to colour of upper left corner
                colorkey = sheet.get_at((0, 0))
            sheet.set_colorkey(colorkey)
            sheet = sheet.convert()
        else: # If there is no colorkey, preserve the image's alpha per pixel.
            _image = sheet.convert_alpha()
        return sheet

    def get_sprites_from_sheet(self, sheet):
        '''
        Return the different sprites from the sheet, scaled appropriately.
        The number of sprites is derived from the amount of plane states which
        are possible in the game. The scaling is calculated based on the size
        of the radar window.
        '''
        sh_size = sheet.get_rect()
        w, h = sh_size.get_height, sh_size.get_width/PLANE_STATES_NUM
        sprites = []
        for i in range(PLANE_STATES_NUM):
            sheet.set_clip((0+i*w, 0), (w, h))
            #TODO: resize
            sprites.append(sheet.get_clip())
        return sprites


class TrailingDot(SuperSprite):

    '''
    The dots or "ghost signals" on the radar, corresponding to past positions
    in time of the aeroplane.
    '''

    @classmethod
    def initialise(cls):
        '''
        Build the entire set of images needed for the traildots.
        That means a two-dimensional array in which each column represents one
        of the possible aeroplane statuses and each row one of the possible
        "ages" of the dot (alpha channel fading out for older radar signals).
        '''
        # Load the basic sprites sheet
        cls.sprite_sheet = cls.load_sprite_sheet('sprite-traildots.png')
        base_sprites = cls.get_sprites_from_sheet(cls.sprite_sheet)
        cls.sprites = []
        # Generate the fading matrix
        fade_step = -100.0 / TRAIL_LENGTH
        for opacity_percentage in range(100, 0, fade_step):
            tmp = base_sprites[:]
            for img in tmp:
                a_values = pygame.surfarray.pixels_alpha(img)
                a_values = int(a_values * opacity_percentage/100)
            cls.images.append(tmp)

    def __init__(self, data_source, time_shift):
        '''
        - data_source: Aeroplane() instantiation from which the sprite will
          derive it's position on the radar.
        - time_shift: which of the ghost signals in the data_source this
          sprite represents
        '''
        super(TrailingDot, self).__init__()
        self.data_source = data_source
        self.time_shift = time_shift
        self.last_status = None

    def update(self, *args):
        status = self.data_source.status
        if status != self.last_status:
            self.image = self.sprites[status][self.time_shift]
        self.rect = self.data_source.trail[self.time_shift]


class AeroplaneIcon(SuperSprite):

    '''
    The sprite located at the current position of the aeroplane
    '''

    @classmethod
    def initialise(cls):
        '''
        Build and set the default image for the plane sprite on the radar.
        - fname: name of the spritesheet file.
        '''
        # Load the basic sprites sheet
        sheets = {}
        sheets['jet'] = cls.load_sprite_sheet('sprite-jet.png')
        sheets['propeller'] = cls.load_sprite_sheet('sprite-propeller.png')
        sheets['supersonic'] = cls.load_sprite_sheet('sprite-supersonic.png')
        cls.sprite_sheets = sheets

    def __init__(self, data_source, model='jet'):
        assert model in ('jet', 'propeller', 'supersonic')
        super(AeroplaneIcon, self).__init__()
        self.sprites = self.get_sprites_from_sheet(self.sprite_sheets[model])
        self.last_status = None
        self.last_heading = None

    def update(self, *args):
        self.image = self.sprites[0]
        self.rect = self.image.get_rect()
        status = self.data_source.status
        heading = self.data_source.heading
        if status != self.last_status or heading != self.last_heading:
            img = self.sprites[status]
            self.image = pygame.transform.rotate(img, heading)
        self.rect = self.data_source.trail[self.time_shift]


# Initialisation of the sprite classes
AeroplaneIcon.initialise()
TrailingDot.initialise()
