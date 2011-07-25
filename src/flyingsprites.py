#!/usr/bin/env python
# -*- coding: utf-8  -*-
'''
Aeroplanes of the ATC simulation game.
'''

from settings import *
from pygame.locals import *
import pygame.sprite
import pygame.surfarray
from random import randint
from euclid import Vector3
from math import sqrt
from collections import deque
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
        Loads the specified sprite sheet.
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
        self.sprite_sheet = sheet

    def get_sprites_from_sheet(self):
        '''
        Clip the different sprites from the sheet and resize them.
        The number of sprites is derived from the amount of plane states which
        are possible in the game. The scaling is calculated based on the size
        of the radar window.
        '''
        sh = self.sprite_sheet
        sh_size = sh.get_rect()
        w, h = sh_size.get_height, sh_size.get_width/PLANE_STATES_NUM
        sprites = []
        for i in range(PLANE_STATES_NUM):
            sh.set_clip((0+i*w, 0), (w, h))
            #TODO: resize
            sprites.append(sh.get_clip())
        return sprites

class TrailDot(pygame.sprite.Sprite):

    @classmethod
    def init(cls):
        '''
        Build the entire set of images needed for the traildots.
        That means a two-dimensional array in which each column represents one
        of the possible aeroplane statuses and each row one of the possible
        "ages" of the dot (alpha channel fading out for older radar signals).
        '''
        # Load the basic sprites sheet
        cls.load_sprite_sheet('sprite-traildots.png')
        base_sprites = cls.get_sprites_from_sheet()
        cls.sprites = []
        # Generate the fading matrix
        fade_step = -100.0 / TRAIL_LENGTH
        for opacity_percentage in range(100, 0, fade_step):
            tmp = base_sprites[:]
            for img in tmp:
                a_values = pygame.surfarray.pixels_alpha(img)
                a_values = int(a_values * opacity_percentage/100)
            cls.images.append(tmp)
        cls.image = cls.sprites[0][0]
        cls.rect = cls.image.get_rect()

class Aeroplane(pygame.sprite.Sprite):

    '''
    Aeorplane modelling.

    Each aeroplane has static attributes depending from the model the plane is.
    The flag property contains a list of empty possible flags:
        Expedite   - Expedite climb or acceleration
        Cleared    - Cleared for takeoff or landing
        Emergency  - High priority flight
        Circling_L - Circling left
        Circling_R - Circling right
        Locked     - The plane is under computer control
        Collision  - The plane is on a collision path
    '''

    KNOWN_PROPERTIES = [#STATIC
                        'icao',            # Three-letter code and flight num.
                        'model',           # Type of plane (name)
                        'destination',     # Airport name
                        'entry_time',      # Time of entry in airspace
                        'speed_limits',    # (min, max) XY projected speed
                        'accel_limits',    # (decel, accel) XY projected accel
                        'max_altitude',    # max altitude
                        'climb_limits',    # (down, up) max climb rates
                        'takeoff_speed',   # takeoff speed at liftoff
                        'landing_speed',   # landing speed at touchdown
                        'max_g',           # maximum Gforce
                        #DYNAMIC
                        'target_conf',     # (heading, speed, altitude)
                        'position',        # 3D vector
                        'velocity',        # 3D vector
                        'fuel',            # seconds before crash
                        'time_last_cmd',   # time of last received command
                        'flags',           # list of flags
                       ]

    @classmethod
    def init(cls, fname):
        '''
        Build and set the default image for the plane sprite on the radar.
        - fname: name of the spritesheet file.
        '''
        # Load the basic sprites sheet
        cls.load_sprite_sheet(fname='sprite-jet.png')
        cls.sprites = cls.get_sprites_from_sheet()
        cls.image = cls.sprites[0]
        cls.rect = cls.image.get_rect()

    def __random_icao(self):
        '''Return a random pseudo-ICAO flight number'''
        rc = lambda : chr(randint(65, 90))
        return ''.join([rc(), rc(), rc(), str(randint(1000, 9999))])

    def __init__(self, **kwargs):
        # Call parent __init__
        super(Aeroplane, self).__init__()

        for property in self.KNOWN_PROPERTIES:
            value = kwargs[property] if kwargs.has_key(property) else None
            setattr(self, property, value)
        if self.icao == None:
            self.icao = self.__random_icao()
        if self.position == None:
            self.position = Vector3(randint(0,WINDOW_SIZE[0]*SCALE_FACTOR),
                                    randint(0,WINDOW_SIZE[1]*SCALE_FACTOR), 0)
        if self.velocity == None:
            self.velocity = Vector3(randint(200,300), 0, 0)

        # Initialise the trail
        self.trail_coords = deque([self.position.xy], TRAIL_LENGTH)

