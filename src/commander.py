#!/usr/bin/env python
# -*- coding: utf-8  -*-
'''
Provide functionality for entering commands and processing them.
'''

from locals import *
from pygame.locals import *
import pygame.font
import re

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

def validate_icao(icao):
    '''
    Valid plane designations are in the format `XXX0000` with `X` being letters
    and `0` being digits.
    '''
    return not None == re.match(r'^[a-z]{3}\d{4}$', icao)

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

def validate_speed(altitude):
    #TODO:Implement this
    raise BaseException('Not yet implemented')

def validate_land(world, port, runaway):
    ports = world.ports
    if port not in ports:
        return False
    if runaway not in port.runaways:
        return False
    return True

GAME_COMMANDS = {'quit' : {'spellings': ['quit', 'q'],
                           'arguments': 0,
                           'validator': None,
                           'flags'    : []
                           },
                 'help' : {'spellings': ['help', 'h', 'man'],
                           'arguments': 0,
                           'validator': None,
                           'flags'    : []
                           }
                 }

PLANE_COMMANDS = {
        'heading'  : {'spellings': ['heading', 'h', 'head'],
                      'arguments': 1,
                      'validator': validate_heading,
                      'flags'    : ['expedite|x', 'left|l', 'right|r']},
        'altitude' : {'spellings': ['altitude', 'a', 'alt'],
                      'arguments': 1,
                      'validator': validate_altitude,
                      'flags'    : ['expedite|x']},
        'speed'    : {'spellings': ['speed', 's', 'sp'],
                      'arguments': 1,
                      'validator': validate_speed,
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

class Parser(object):

    '''
    Parse a command line (execute it)
    '''

    def __init__(self, aerospace):
        self.aerospace = aerospace
        self.initialise()

    def initialise(self, sentence=''):
        '''
        The parser object is reusable. This method resets the parser internal
        status and set the text to a given value.
        '''
        # If present, separate control character from command with a space
        if len(sentence) > 1 and sentence[0] in './' and sentence[1] != ' ':
            sentence = sentence[0] + ' ' + sentence[1:]
        self.sentence = sentence
        self.validated = False
        self.bits = []                   #the sentence, reversed and split
        self.target = None               #plane that should receive order

    def validate(self):
        '''Validate current text. Return True/False.'''
        #TODO: validation goes here!
        return True

    def parse(self):
        '''Execute current text.'''
        if len(self.sentence) == 0:
            return
        if self.validated or self.validate():
            self.bits = self.sentence.split()
            self.bits.reverse()
            first = self.bits.pop()
            # We're issuing commands to a plane
            if validate_icao(first):
                self.parse_plane_command()
                self.target = first
            # We're appending commands to a plane queue
            elif first[0] == '.':
                plane = self.bits.pop()
                if validate_icao(plane):
                    self.append_command(plane)
                else:
                    msg = 'Invalid ICAO reference (append - %s)' % plane
                    raise BaseException(msg)
            # We're issuing a game command
            elif first == '/':
                self.parse_game_command()
            else:
                msg = 'Invalid ICAO reference (direct - %s)' % first
                raise BaseException(msg)

    def parse_plane_command(self):
        pass

    def append_command(self, plane):
        pass

    def parse_game_command(self):
        command = self.bits.pop().lower()
        if command in GAME_COMMANDS['quit']['spellings']:
            print('quit')
        elif command in GAME_COMMANDS['help']['spellings']:
            print('help')
        else:
            raise BaseException('Invalid game command! (%s)' % command)

class CommandLine(object):

    '''
    This class manage the command string composition, validation, etc...
    '''

    def __init__(self, surface, aerospace):
        self.chars = list('')
        self.surface = surface
        self.aerospace = aerospace
        if not pygame.font.get_init():
            pygame.font.init()
        self.textbox = pygame.font.Font(None, FONT_HEIGHT)
        self.parser = Parser(aerospace)

    def _get_list_of_existing(self, what, context=None):
        '''
        Return a list of existing (=valid) strings representing `what`
        ('planes', 'aeroports', 'runaways' or 'beacons'). The `contex` value
        is used for those `what` which are not global to the aerospace (e.g.:
        runaways can be given for a given aeroport, not aerospace).
        '''
        if what == 'planes':
            return [p.icao for p in self.aerospace.aeroplanes]
        elif what == 'aeroports':
            return [a.iata for a in self.aerospace.aeroports]
        elif what == 'runaways':
            assert context != None  #Context must be the name of the aeroport
            for ap in self.aerospace.aeroports:
                if ap.iata == context:
                    return [r.id for r in ap.runaways]
        elif what == 'beacons':
            return [b.code for b in self.aerospace.beacons]
        else:
            raise BaseException('Unknown type of items!')

    def _get_common_beginning(self, strings):
        '''
        Return the strings that is common to the beginning of each string in
        the strings list.
        '''
        result = []
        limit = min([len(s) for s in strings])
        for i in range(limit):
            if reduce(lambda s1,s2 : True and s1[i] == s2[i], strings) == True:
                result.append(object)
            else:
                break
        return ''.join(result)

    @property
    def text(self):
        return ''.join(self.chars)

    def process_keystroke(self, event):
        if event.key == K_RETURN:
            self.parser.initialise(self.text)
            self.parser.parse()
        elif event.key == K_BACKSPACE and self.chars:
            self.chars.pop()
        elif event.key == K_TAB:
            self.autocomplete()
        elif event.unicode in VALID_CHARS:
            self.chars.append(event.unicode.upper())

    def autocomplete(self):
        pool = self._get_list_of_existing('planes')
        root = ''.join(self.chars).split()[-1]  #The bit after the last space
        matches = [i for i in pool if i.find(root) == 0]
        if len(matches) == 1:
            match = matches[0]
        else:
            match = self._get_common_beginning(matches)
        self.chars.extend(list(match[len(root):]))

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