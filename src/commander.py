#!/usr/bin/env python
# -*- coding: utf-8  -*-
'''
Provide functionality for entering commands and processing them.
'''

from locals import *
from pygame.locals import *
import pygame.font

__author__ = "Mac Ryan"
__copyright__ = "Copyright 2011, Mac Ryan"
__license__ = "GPL v3"
#__version__ = "1.0.0"
__maintainer__ = "Mac Ryan"
__email__ = "quasipedia@gmail.com"
__status__ = "Development"


# VALIDATORS
# These functions provide validation for the arguments of the commands, they
# all return True/False according to whether the argument is a valid one.

def validate_heading(heading):
    '''
    Valid headings can be either a 3 digit angle between 000° and 360° or a
    beacon code.
    '''
    num_h = int(heading)
    return 0 <= num_h <= 360 and len(heading) == 3 and num_h % 10 == 0

def validate_altitude(altitude):
    num_a = int(altitude)
    return 0 <= num_a <= 80 and len(altitude) == 2 and num_a % 5 == 0

def validate_land(world, port, runaway):
    ports = world.ports
    if port not in ports:
        return False
    if runaway not in port.runaways:
        return False
    return True

COMMANDS = {'heading'  : {'spellings': ['heading', 'h', 'head'],
                          'arguments': 1,
                          'validator': validate_heading,
                          'flags'    : ['expedite|x', 'left|l', 'right|r']},
            'altitude' : {'spellings': ['altitude', 'a', 'alt'],
                          'arguments': 1,
                          'validator': validate_altitude,
                          'flags'    : ['expedite|x']},
            'take off' : {'spellings': ['take off', 't', 'to', 'up'],
                          'arguments': 1,
                          'validator': validate_altitude,
                          'flags'    : ['expedite|x']},
            'land'     : {'spellings': ['land', 'l', 'down'],
                          'arguments': 2,
                          'validator': validate_land,
                          'flags'    : []},
            'abort'    : {'spellings': ['abort', 'a'],
                          'arguments': 0,
                          'validator': None,
                          'flags'    : ['last|l']},
            }

class CommandLine(object):

    '''
    This class manage the command string composition, validation, etc...
    '''

    def __init__(self, surface):
        self.chars = list('Hello world!')
        self.surface = surface
        if not pygame.font.get_init():
            pygame.font.init()
        self.textbox = pygame.font.Font(None, FONT_HEIGHT)

    @property
    def text(self):
        return ''.join(self.chars)

    def process_keystroke(self, event):
        if event.key == K_RETURN:
            print('quit')
        elif event.key == K_BACKSPACE and self.chars:
            self.chars.pop()
        elif event.key == K_TAB:
            self.autocomplete()
        elif event.unicode in VALID_CHARS:
            self.chars.append(event.unicode)

    def autocomplete(self):
        self.chars.extend(list('-auto-'))

    def validate(self):
        return True

    def update(self):
        pass

    def draw(self):
        image = self.textbox.render(self.text, True, WHITE, BLACK)
        iw, ih = image.get_size()
        sw, sh = self.surface.get_size()
        x = (sw - iw)/2
        y = (sh - ih)/2
        self.surface.fill(BLACK)
        self.surface.blit(image, (x,y))