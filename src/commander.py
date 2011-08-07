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
                      'validator': '_validate_heading',
                      'flags'    : {'expedite': ['expedite', 'x'],
                                    'long'    : ['long', 'l']}},
        'altitude' : {'spellings': ['altitude', 'a', 'alt'],
                      'arguments': 1,
                      'validator': '_validate_altitude',
                      'flags'    : {'expedite': ['expedite', 'x']}},
        'speed'    : {'spellings': ['speed', 's', 'sp'],
                      'arguments': 1,
                      'validator': '_validate_speed',
                      'flags'    : {'expedite': ['expedite', 'x']}},
        'take off' : {'spellings': ['takeoff', 'to', 'up', 'fly'],
                      'arguments': 1,
                      'validator': '_validate_altitude',
                      'flags'    : {'expedite': ['expedite', 'x']}},
        'land'     : {'spellings': ['land', 'l', 'down'],
                      'arguments': 2,
                      'validator': '_validate_land',
                      'flags'    : []},
        'circle'   : {'spellings': ['circle', 'c', 'hold'],
                      'arguments': 1,
                      'validator': '_validate_circle',
                      'flags'    : []},
        'abort'    : {'spellings': ['abort', 'purge'],
                      'arguments': 0,
                      'validator': None,
                      'flags'    : {'lastonly': ['lastonly', 'last', 'l']}}
        }

class Parser(object):

    '''
    Parse a command line (validate and execute it).
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

    # VALIDATORS These methods provide validation for the arguments of the
    # commands, they all return True/False according to whether the argument is
    # a valid one. All arguments are passed-in as strings.

    def _validate_icao(self, icao):
        '''
        Valid plane designations are in the format `XXX0000` with `X` being
        letters and `0` being digits.
        '''
        return not (None == re.match(r'^[a-zA-Z]{3}\d{4}$', icao))

    def _validate_heading(self, heading):
        '''
        Valid headings can be either a 3 digit angle between 000° and 360° or a
        beacon code.
        '''
        try:
            num_h = int(heading)
        except ValueError:
            return False
        return 0 <= num_h <= 360 and len(heading) == 3 and num_h % 10 == 0

    def _validate_altitude(self, altitude):
        '''
        Valid altitudes are given in hundreds of meters, and are multiple of
        500. They must also be in the range between min and max altitudes for
        the game.
        '''
        #TODO: Parametrise the min and max in-game altitudes
        try:
            num_a = int(altitude)
        except ValueError:
            return False
        return 0 <= num_a <= 80 and len(altitude) == 2 and num_a % 5 == 0

    def _validate_speed(self, speed):
        '''
        Valid speeds are given in hundreds of km/h.
        '''
        try:
            num_s = int(speed)
        except ValueError:
            return False
        return True

    def _validate_land(self, iata, runaway):
        '''
        Valid landings indicate the three-letters airport code and the runaway
        in the format 00X, where 0 represent a digit and X a letter (R,L or C)
        '''
        return (not (None == re.match(r'^[a-zA-Z]{3}$', iata)) and
                not (None == re.match(r'^\d{2}(L|C|R)?$', runaway)))

    def _validate_circle(self, direction):
        '''
        Parameter can only be right (r) or left (l).
        '''
        if direction.lower() not in ('r', 'right', 'l', 'left'):
            return False
        return True

    def parse(self):
        '''
        Validate/Parse the command line.
        Returns a list of parsed commands in case of success, or a string with
        an error message in case of failure.
        The parsed commands list is structured with a callable object and a
        list that should be given as input for it:
        [[callable_, [arg1, arg2...]], [callable_, [arg1, arg2]]]
        '''
        if len(self.sentence) == 0:
            return []
        self.bits = self.sentence.lower().split()
        self.bits.reverse()
        first = self.bits.pop()
        # We're issuing commands to a plane
        if self._validate_icao(first):
            return self.parse_plane_commands(first)
        # We're appending commands to a plane queue
        elif first[0] == '.':
            icao = self.bits.pop()
            if self._validate_icao(icao):
                return self.parse_plane_commands(icao, to_queue=True)
            else:
                msg = 'Invalid ICAO reference (append - %s)' % icao
                return msg
        # We're issuing a game command
        elif first == '/':
            return self.parse_game_command()
        else:
            msg = 'Invalid ICAO reference (direct - %s)' % first
            return msg

    def parse_plane_commands(self, icao, to_queue=False):
        '''
        Parse all commands on the command line, dispatching them to the plane
        whose ICAO code is given.
        '''
        parsed_commands = []
        aeroplane = self.aerospace.get_plane_by_icao(icao)
        callable_ = aeroplane.queue_command if to_queue \
                                            else aeroplane.execute_command
        while len(self.bits) != 0:
            issued = self.bits.pop()
            # Identify what command has been issued
            command_name = None
            command = None
            for k, v in PLANE_COMMANDS.items():
                if issued in v['spellings']:
                    command_name = k
                    command = v
                    break
            if not command_name or not command:
                msg = 'Unrecognised bit, expected command: %s' % issued
                return msg
            # Parse arguments
            args = []
            for i in range(command['arguments']):
                try:
                    args.append(self.bits.pop())
                except IndexError:
                    msg = 'Not enough arguments for command %s' % command_name
                    return msg
            # Verify that arguments pass validation
            if command['validator']:
                validator = getattr(self, command['validator'])
                if not validator(*args):
                    msg = 'Parameters for %s failed validation' % command_name
                    return msg
            # Check for flags and parse them if present
            flags = []
            possible_flag = command['flags']  #[] = skip
            while possible_flag:
                possible_flag = False
                if not self.bits:
                    break
                candidate = self.bits[-1]
                for k, v in command['flags'].items():
                    if candidate in v:
                        flags.append(k)
                        self.bits.pop()
                        possible_flag = True
                        break
            # Store the parsed commands
            parsed_commands.append([command_name, args, flags])
        # Verify that some command has been entered
        if len(parsed_commands) == 0:
            msg = 'No commands were issued for the plane!'
            return msg
        # Verify the compatibility of stored commands: only heading, speed and
        # altitude values can be combined in a single command.
        elif len(parsed_commands) != 1:
            command_list = [el[0] for el in parsed_commands]
            if len(command_list) != len(set(command_list)):
                msg = 'Repeated commands!'
                return msg
            for com in command_list:
                if com not in ['heading', 'altitude', 'speed']:
                    msg = 'Only heading, altitude and speed can be combined!'
                    return msg
        return (callable_, parsed_commands)

    def parse_game_command(self, validate_only=False):
        command = self.bits.pop()
        if command in GAME_COMMANDS['quit']['spellings']:
            print('quit')
        elif command in GAME_COMMANDS['help']['spellings']:
            print('help')
        else:
            msg = 'Invalid game command! (%s)' % command
            return msg
        return []

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
            chs = set([s[i] for s in strings])
            if len(chs) == 1:
                result.append(chs.pop())
            else:
                break
        return ''.join(result)

    @property
    def text(self):
        return ''.join(self.chars)

    def process_keystroke(self, event):
        if event.key == K_RETURN:
            self.parser.initialise(self.text)
            parsed = self.parser.parse()
            if type(parsed) not in (tuple, list):
                print('Validation failed with message: %s' % parsed)
            elif parsed:
                callable_, args = parsed
                callable_(args)
        elif event.key == K_BACKSPACE and self.chars:
            self.chars.pop()
        elif event.key == K_TAB:
            self.autocomplete()
        elif event.unicode in VALID_CHARS:
            self.chars.append(event.unicode.upper())

    def autocomplete(self):
        root = ''.join(self.chars).split()[-1]  #The bit after the last space
        pool = self._get_list_of_existing('planes')
        matches = [i for i in pool if i.find(root) == 0]
        if len(matches) == 1:
            match = matches[0]+' '
        elif len(matches) > 1:
            match = self._get_common_beginning(matches)
        else:
            return
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