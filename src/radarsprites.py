#!/usr/bin/env python
# -*- coding: utf-8  -*-
'''
Provides the sprite classes used in the radar window.

These are: aeroplanes, trailing dots, labels.
'''

from locals import *
from pygame.locals import *
import pygame.sprite
import pygame.surfarray
import pygame.transform
import pygame.surface
import pygame.image
import pygame.font
import os
from math import sin, cos, radians
from euclid import Vector2

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

    initialised = False

    @classmethod
    def initialise(cls):
        if not cls.initialised:
            cls.initialised = True

    @classmethod
    def load_sprite_sheet(cls, fname, colorkey=False, directory='../data'):
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

    @classmethod
    def get_sprites_from_sheet(cls, sheet):
        '''
        Return the different sprites from the sheet, scaled appropriately.
        The number of sprites is derived from the amount of plane states which
        are possible in the game. The scaling is calculated based on the size
        of the radar window.
        '''
        sh_size = sheet.get_rect()
        w, h = sh_size.width/PLANE_STATES_NUM, sh_size.height
        sprites = []
        for i in range(PLANE_STATES_NUM):
            crop_area = (pygame.rect.Rect((0+i*w, 0), (w, h)))
            sprites.append(cls.crop(sheet, crop_area))
        return sprites

    @classmethod
    def crop(cls, image, area):
        '''
        Return the cropped portion of an image.
        '''
        new_surface = pygame.surface.Surface((area.width, area.height),
                                             flags=SRCALPHA)
        new_surface.blit(image, (0,0), area)
        return new_surface

    @classmethod
    def rotoscale(cls, image, angle=0, factor=1, px_limit=1):
        '''
        Return an image that has been rotated CCW of 'angle' degrees, scaled
        of a 'factor' factor. If 'factor' would imply having the y axis of the
        original non-rotated image < to 'px_limit', factor is re-calculated
        to match the limit.
        '''
        #TODO: calculating the ratio should go in the initialisation code
        x, y = image.get_rect().width, image.get_rect().height
        factor = max(factor, 1.0*px_limit/y)
        if angle:
            image = pygame.transform.rotate(image, angle)
            # The rotation can potentially enlarge the bounding rectangle of
            # the sprite, filling the extra other space with alpha=0
            image = cls.crop(image, image.get_bounding_rect())
        # Calculate the actual ratio that allows not to exceed px_limit
        x, y = [int(round(v*factor)) for v in (x,y)]
        # Finally, scaling down as last operation guarantees anti-aliasing
        return pygame.transform.smoothscale(image, (x,y))

    @property
    def position(self):
        return self.rect.center


class TagConnector(SuperSprite):

    '''
    The line connecting the Tag to the AeroplaneIcon sprites.
    '''

    def __init__(self, tag):
        super(TagConnector, self).__init__()
        tag.set_connector(self)
        self.tag = tag
        self.update()

    @property
    def icon_pos(self):
        return self.tag.plane.trail[0]

    def update(self):
        plane = Vector2(*self.icon_pos)
        angle = self.tag.angle
        r = self.tag.rect
        if 0 <= angle < 90:
            corner = Vector2(*r.bottomleft)
        elif 90<= angle < 180:
            corner = Vector2(*r.bottomright)
        elif 180 <= angle < 270:
            corner = Vector2(*r.topright)
        elif 270 <= angle < 360:
            corner = Vector2(*r.topleft)
        else:
            msg = 'Something very fishy with then angles is going on...'
            raise BaseException(msg)
        placement = Vector2(min(plane.x, corner.x), min(plane.y, corner.y))
        flip_x = True if corner.x > plane.x else False
        flip_y = True if corner.y > plane.y else False
        diff = plane-corner
        image = pygame.surface.Surface((abs(diff.x), abs(diff.y)), SRCALPHA)
        self.rect = image.get_rect()
        pygame.draw.aaline(image, WHITE, (0,0), (self.rect.width,
                                                 self.rect.height))
        if flip_x != flip_y:  #both flips == no flip
            image = pygame.transform.flip(image, flip_x, flip_y)
        self.image = image
        self.rect.move_ip(placement)


class Tag(SuperSprite):

    '''
    The airplane information displayed beside the aeroplane icon.
    '''

    @classmethod
    def initialise(cls):
        cls.fontobj = pygame.font.Font('../data/ex_modenine.ttf',
                                        HUD_INFO_FONT_SIZE)
        cls.default_angle = 45
        cls.default_radius = 50
        cls.initialised = True

    @classmethod
    def render_lines(cls, lines):
        '''
        Return the image of the rendered multiline text
        '''
        font_height = cls.fontobj.get_height()
        surfaces = [cls.fontobj.render(ln, True, WHITE) for ln in lines]
        maxwidth = max([s.get_width() for s in surfaces])
        result = pygame.surface.Surface((maxwidth, len(lines)*font_height),
                                        SRCALPHA)
        for i in range(len(lines)):
            result.blit(surfaces[i], (0,i*font_height))
        return result

    def __init__(self, data_source, radar_rect):
        super(Tag, self).__init__()
        self.plane = data_source
        self.radar_rect = radar_rect
        self.update()

    def set_connector(self, connector_sprite):
        '''
        Associate another sprite (the connecting line from the airplane to the
        tag) with this sprite. It's used to update that sprite when the tag
        placement changes.
        '''
        self.connector = connector_sprite

    def place(self):
        '''
        Place the tag in a radar position that does not overlaps any other
        tag or aeroplane icon.
        '''
        cx, cy = self.plane.trail[0]
        while True:
            rad = radians(self.angle)
            ox = rint(cos(rad) * self.radius)
            oy = -rint(sin(rad) * self.radius)  #minus because of screen coordinates
            x, y = cx + ox, cy + oy
            self.rect = get_rect_at_centered_pos(self.image, (x, y))
            if self.radar_rect.contains(self.rect):
                break
            else:
                self.angle += 5
                self.angle %= 360

    def update(self):
        pl = self.plane
        render = self.fontobj.render
        lines = []
        # LINE 1 = Airplane code
        lines.append(pl.icao.upper())
        # LINE 2 = Altitude, speed
        # Remove last digit, add variometer
        alt = str(int(round(pl.altitude/10.0)))
        alt += pl.variometer
        # Convert m/s to kph AND remove last digit, add accelerometer
        spd = str(int(round(pl.speed*0.36)))
        spd += pl.accelerometer
        lines.append('%s%s' % (alt,spd))
        self.image = self.render_lines(lines)
        self.angle = self.default_angle
        self.radius = self.default_radius
        self.place()


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
        if cls.initialised:
            return  #make sure initialisation occurs only once
        # Load the basic sprites sheet
        cls.sprite_sheet = cls.load_sprite_sheet('sprite-traildots.png')
        base_sprites = cls.get_sprites_from_sheet(cls.sprite_sheet)
        cls.sprites = []
        # Generate the fading matrix
        fade_step = int(round(-100.0 / TRAIL_LENGTH))
        for opacity_percentage in range(100, 0, fade_step):
            rtsc = cls.rotoscale
            tmp = [rtsc(img, 0, SPRITE_SCALING, 2) for img in base_sprites]
            dim = lambda x : int(round(x * opacity_percentage/100))
            for img in tmp:
                a_values = pygame.surfarray.pixels_alpha(img)
                # There's no pynum native method for in-place mapping, see:
                # http://stackoverflow.com/q/6824122/146792
                for row in range(len(a_values)):
                    for col in range(len(a_values[0])):
                        a_values[row][col] = dim(a_values[row][col])
            cls.sprites.append(tmp)
        cls.initialised = True

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
        self.update()

    def update(self, *args):
        status = self.data_source.status
        if status != self.last_status:
            self.image = self.sprites[self.time_shift][status]
        rect = self.data_source.trail[self.time_shift]
        self.rect = get_rect_at_centered_pos(self.image, rect)


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
        if cls.initialised:
            return  #make sure initialisation occurs only once
        # Load the basic sprites sheet
        sheets = {}
        sheets['jet'] = cls.load_sprite_sheet('sprite-jet.png')
        sheets['propeller'] = cls.load_sprite_sheet('sprite-propeller.png')
        sheets['supersonic'] = cls.load_sprite_sheet('sprite-supersonic.png')
        cls.sprite_sheets = sheets
        cls.initialised = True

    def __init__(self, data_source, model='jet'):
        self.data_source = data_source
        self.model = model
        assert model in ('jet', 'propeller', 'supersonic')
        super(AeroplaneIcon, self).__init__()
        self.sprites = self.get_sprites_from_sheet(self.sprite_sheets[model])
        self.last_status = None
        self.last_heading = None
        self.update()

    def update(self, *args):
        status = self.data_source.status
        heading = self.data_source.heading
        if status != self.last_status or heading != self.last_heading:
            img = self.sprites[status]
            # The following line needs a bit of explanation:
            # 1. plane heading in the simulation is defined as CW degrees from
            #    North, but on screen (and for pygame) they are CCW from East
            # 2. screen Y axis has reversed polarity from simulation one (it
            #    decreases going UP!!
            # The CCW vs CW and the polarity axis compensate for each other,
            # eliminatig the need to change sign to the heading. the North vs
            # East is compensated by subtracting 90 degrees.
            heading -= 90
            self.image = self.rotoscale(img, heading, SPRITE_SCALING, 15)
        self.rect = get_rect_at_centered_pos(self.image, self.data_source.trail[0])


# Initialisation of the sprite classes
AeroplaneIcon.initialise()
TrailingDot.initialise()
Tag.initialise()
TagConnector.initialise()