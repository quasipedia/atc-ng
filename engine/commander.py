#!/usr/bin/env python
# -*- coding: utf-8  -*-
'''
Provide functionality for entering commands and processing them.
'''

import re
import time
import textwrap
import os.path as path
from collections import deque
from copy import copy

import yaml
import pygame.font
from pygame.locals import *
from pkg_resources import resource_stream  #@UnresolvedImport

import lib.utils as U
from engine.settings import settings as S
from engine.logger import log
from lib.euclid import Vector3

__author__ = "Mac Ryan"
__copyright__ = "Copyright 2011, Mac Ryan"
__license__ = "GPL v3"
#__version__ = "<dev>"
#__date__ = "<unknown>"
__maintainer__ = "Mac Ryan"
__email__ = "quasipedia@gmail.com"
__status__ = "Development"


# +------------------+
# | HELPER FUNCTIONS |
# +------------------+

def __command_files_sanity_check():
    '''
    Verify the command files make sense.
    '''
    sets = []
    for file in (GAME_COMMANDS, PLANE_COMMANDS):
        # No two spellings are the same
        spells = []
        for comm in file.values():
            spells.extend(comm['spellings'])
        set_ = set(spells)
        assert len(spells) == len(set_)
        sets.append(set_)
    # There are no game and plane commands with the same name
    assert len(sets[0]|sets[1]) == len(sets[0]) + len(sets[1])
    # Game commands only have maximum one parameter
    assert max([c['arguments'] for c in GAME_COMMANDS.values()]) == 1

def __attach_combo_info():
    '''
    Attach the information on combatible commands to the PLANE_COMMANDS dict.
    '''
    dict_ = {}
    # Create initial dictionary
    for combo in VALID_PLANE_COMMANDS_COMBOS:
        for command in combo:
            try:
                dict_[command].extend(combo)
            except KeyError:
                dict_[command] = combo[:]
    # Eliminates redoundancies and self and attach on target dictionary
    for k, v in dict_.items():
        PLANE_COMMANDS[k]['combos'] = list(set(v) - set([k]))

# +-----------------------+
# | MODULE INITIALISATION |
# +-----------------------+

# LOAD COMMAND DESCRIPTIONS
__data = resource_stream(__name__, path.join('data', 'gcommands.yml'))
GAME_COMMANDS = yaml.load(__data)
__data = resource_stream(__name__, path.join('data', 'pcommands.yml'))
PLANE_COMMANDS = yaml.load(__data)
__data = resource_stream(__name__, path.join('data', 'pcombos.yml'))
VALID_PLANE_COMMANDS_COMBOS = yaml.load(__data)
__command_files_sanity_check()
__attach_combo_info()

# STRIPPING REGEX TO CONVERT FROM reStructuredText TO plain text
__rst_to_strip = re.compile(
        r'(`)|'                           # literals and interpreted arguments
        r'(:[a-z-]+:)|'                   # interpreted markers
        r'(\*+)|'                         # emphasis
            r'((\+{1}[-=\+]+\+{1}){1}'    # table upper delimiter
            r'(.|\n)+'                    # anything
            r'(\+{1}[-=\+]+\+{1}){1})|'   # tables lower delimiter
        r'(_)|'                           # hyperlinks
        r'(\<.+\>)'                       # target literals
        )

# +------------------+
# | MODULE FUNCTIONS |
# +------------------+

def get_command_description(cname):
    '''
    Return the available information on the command ``cname``.
    '''
    if cname in PLANE_COMMANDS.keys():
        command = PLANE_COMMANDS[cname]
    elif cname in GAME_COMMANDS.keys():
        command = GAME_COMMANDS[cname]
    res = command.copy()
    # Strips reStructuredText markup
    res['description'] = __rst_to_strip.sub('', res['description'])
    res['description'] = res['description'].replace('  ', ' ')
    return res

# +----------------+
# | MODULE CLASSES |
# +----------------+

class Parser(object):

    '''
    Parse a command line.

    This class does mainly three things:
    * Parse the command line (= the line must respect the ATC-NG "grammar"
    * Arguments standardisation (=set defaults, convert aliases, etc...)
    * Invoke execution
    '''

    def __init__(self, aerospace, game_commands_processor):
        self.aerospace = aerospace
        self.game_commands_processor = game_commands_processor
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

    def __from_alias_to_command(self, alias):
        '''
        Return the "real" command name instead of its alias. For example, passing
        in the command name ``MAN`` will return ``HELP``, ``H`` will reaturn
        ``HEADING`` and so on.
        Return None if the given alias does not match any command.
        '''
        for pool in (GAME_COMMANDS, PLANE_COMMANDS):
            for cname in pool:
                if alias in pool[cname]['spellings']:
                    return cname
        return None

    # VALIDATORS These methods provide validation for the arguments of the
    # commands. All arguments are passed-in as strings and are converted to a
    # suitable format during the validation process. The methods return False
    # if the argument fails validation, or a list containing the converted ones
    # if passes.

    def _validate_icao(self, icao):
        '''
        Valid plane designations are in the format `XXX0000` with `X` being
        letters and `0` being digits.
        '''
        if None == re.match(r'^[A-Z]{3}\d{4}$', icao):
            return False
        return [icao]

    def _validate_heading(self, arg):
        '''
        Valid headings can be either:

        - a 3 digit angle between 000° and 360° (absolute heading)
        - a signed integer like -15 or +180 (heading delta)
        - a beacon name (target point)

        The first will convert in validation to a numeric heading, the latter
        in a ``euclid.Vector3()`` instance, while the second one will be
        returned as a string (as validation knows nothing about current plane
        heading, and calculations need to be performed by a Pilot() instance.
        '''
        if re.match(r'(\+|-)\d+$', arg):
            return [arg.strip()]
        try:  #argument is a numerical heading
            num_h = int(arg)
            if not (0 <= num_h <= 360 and len(arg) == 3):
                return False
            return [num_h]
        except ValueError:  #argument is a beacon id
            return self._validate_clear(arg)

    def _validate_altitude(self, alt):
        '''
        Valid altitudes are given in hundreds of meters, and are multiple of
        500. They must also be in the range between min and max altitudes for
        the game.
        '''
        try:
            num_a = int(alt)
        except ValueError:
            return False
        min_ = S.MIN_FLIGHT_LEVEL/100
        max_ = S.MAX_FLIGHT_LEVEL/100
        if not (min_<= num_a <= max_ and len(alt) == 2 and num_a % 5 == 0):
            return False
        return [num_a * 100]  #return in metres

    def _validate_speed(self, speed):
        '''
        Valid speeds are given in kph.
        '''
        try:
            num_s = int(speed)
        except ValueError:
            return False
        return [num_s / 3.6]  #return in metres/second

    def _validate_land(self, iata, runway):
        '''
        Valid landings indicate the three-letters airport code and the runaway
        in the format 00X, where 0 represent a digit and X a letter (R,L or C)
        '''
        if (not (None == re.match(r'^[A-Z]{3}$', iata)) and
                not (None == re.match(r'^\d{2}(L|C|R)?$', runway))):
            return [iata, runway]
        return False

    def _validate_circle(self, direction):
        '''
        Parameter can only be right (R) or left (L).
        '''
        if direction not in ('R', 'RIGHT', 'CW', 'L', 'LEFT', 'CCW'):
            return False
        return [direction]

    def _validate_clear(self, beacon):
        '''
        Marker must be an existing beacon, if given.
        '''
        if not beacon in self.aerospace.beacons:
            return False
        else:
            return [Vector3(*self.aerospace.beacons[beacon].location)]


    def _validate_takeoff(self, runway):
        '''
        Parameter must be formatted as runway.
        '''
        if not re.match(r'[0-3][0-9][LCR]?$', runway):
            return False
        return [runway]

    def _validate_help(self, cname=None):
        '''
        ``cname`` must be a valid alias of an existing command. Set default if
        needed.
        '''
        if not cname:
            cname = GAME_COMMANDS['HELP']['default']
            # one could return here, but just as consistency check, we let
            # the check run even on the default one.
        cname = self.__from_alias_to_command(cname)
        return [cname] if cname else False

    def _validate_sort(self, filter=None):
        '''
        ``filter`` must be a valid filter for sorting the strips. A default is
        set if no argument is passed.
        '''
        if not filter:
            filter = GAME_COMMANDS['SORT']['default']
            # one could return here, but just as consistency check, we let
            # the check run even on the default one.
        valid = ['ALTITUDE', 'CALLSIGN', 'FUEL', 'ICAO', 'DISTANCE', 'SPEED',
                 'STATUS', 'TIME']
        return [filter] if filter in valid else False

    def parse(self):
        '''
        Validate/Parse the command line. Returns a list of parsed commands in
        case of success, or a string with an error message in case of failure.
        The parsed commands list is structured with a callable object and a
        list that should be given as input for it:
        [command, [arg1, arg2, ...], [flag1, flag2, ...]]
        '''
        if len(self.sentence) == 0:
            return []
        self.bits = self.sentence.split()
        self.bits.reverse()
        first = self.bits.pop()
        # We're issuing commands to a plane
        if self._validate_icao(first):
            return self.parse_plane_commands(first)
        # We're issuing a game command
        elif first == '/':
            return self.parse_game_command()
        else:
            msg = '"%s" is not a valid ICAO reference.' % first
            return msg

    def parse_plane_commands(self, icao):
        '''
        Parse the command line as aeroplane commands. Return a callable and a
        list of arguments structured as a list of triplets each of them in the
        format: [command, [arg1, arg2, ...], [flag1, flag2, ...]].
        '''
        parsed_commands = []
        try:
            pilot = self.aerospace.get_plane_by_icao(icao).pilot
        except KeyError:
            return 'Flight %s is not on the radar.' % icao
        while len(self.bits) != 0:
            # The first bit of a command sequence is either the command or
            # the condensed form for heading, altitude and speed (see below)
            issued = self.bits.pop()
            # Special condensed syntax is allowed for H, A, S in the form
            # letter+digits without spaces
            decomposed = re.match(r'^(H|S|A)(\d{2,})$', issued)
            if decomposed:
                c = decomposed.group(1)
                a = decomposed.group(2)
                if c == 'H' and self._validate_heading(a) or \
                   c == 'A' and self._validate_altitude(a) or \
                   c == 'S' and self._validate_speed(a):
                    issued = c
                    self.bits.append(a)
            # Identify the issued command
            command_name = None
            command = None
            for k, v in PLANE_COMMANDS.items():
                if issued in v['spellings']:
                    command_name = k
                    command = v
                    break
            if not command_name or not command:
                msg = '"%s" is neither a command nor a flag.' % issued
                return msg
            # Parse arguments
            args = []
            for i in range(command['arguments']):
                try:
                    args.append(self.bits.pop())
                except IndexError:
                    msg = 'Not enough arguments for command "%s".' % \
                            command_name
                    return msg
            # Verify that arguments pass validation
            if command['validator']:
                validator = getattr(self, command['validator'])
                args = validator(*args)
                if not args:
                    msg = 'Parameters for "%s" command failed validation.' % \
                            command_name
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
            msg = 'No commands were issued to the plane.'
            return msg
        # FINAL SEMANTIC CHECKS
        command_list = [el[0] for el in parsed_commands]
        command_set = set(command_list)
        # If several commands are issued at once, verify they are compatible
        if len(parsed_commands) != 1:
            # No duplicates!
            if len(command_list) != len(command_set):
                msg = 'You can\'t repeat commands in the same radio message.'
                return msg
            # Can be logically mixed
            valid_combo = False
            for combo in VALID_PLANE_COMMANDS_COMBOS:
                if command_set <= set(combo):
                    valid_combo = True
            if not valid_combo:
                msg = 'These commands cannot be performed at the same time.'
                return msg
        return pilot.do, parsed_commands

    def parse_game_command(self):
        try:
            issued = self.bits.pop()
        except IndexError:  # Empty bits --> No command issued
            msg = 'What is the command?'
            return msg
        cname = None
        command = None
        for k, v in GAME_COMMANDS.items():
            if issued in v['spellings']:
                cname = k
                command = v
                break
        if command:
            args = self.bits
            # Check the amount of parameters is correct
            if len(args) > command['arguments']:
                how_many = 'no' if command['arguments'] == 0 \
                                else 'no more than %s' % command['arguments']
                return 'Command %s accepts %s arguments' % (cname, how_many)
            if len(args) and not command['default']:
                return 'You must provide a parameter for command %s' % cname
            if command['validator']:
                validator = getattr(self, command['validator'])
                args = validator(*args)
                if not args:
                    msg = 'Parameters for "%s" command failed validation.' % \
                            cname
                    return msg
        else:
            msg = 'Invalid game command! (%s)' % issued
            return msg
        return (self.game_commands_processor, [cname, args])

class CommandLine(object):

    '''
    This class manage the command string composition, validation, etc...
    '''

    def __init__(self, surface, aerospace, game_commands_processor):
        self.chars = list('')
        self.surface = surface
        self.aerospace = aerospace
        # Properties for handling multiline console and history browsing
        self.command_history = []
        self.history_ptr = 0
        self.console_lines = deque(maxlen=S.CONSOLE_LINES_NUM)
        self.console_image = pygame.surface.Surface((0,0))
        self.last_console_snapshot = copy(self.console_lines)
        self.cmd_prefix = ' '.join((S.OUTBOUND_ID, S.PROMPT_SEPARATOR))
        # Pygame font initialisation
        if not pygame.font.get_init():
            pygame.font.init()
        # Font size calculations
        small_size = S.CLI_RECT.h * 0.9 / \
                     (S.CONSOLE_LINES_NUM + 1.0 / S.CONSOLE_FONT_SIZE_RATIO)
        large_size = int(small_size / S.CONSOLE_FONT_SIZE_RATIO)
        small_size = int(small_size)
        self.large_f = pygame.font.Font(S.MAIN_FONT, large_size)
        self.small_f = pygame.font.Font(S.MAIN_FONT, small_size)
        self.max_large_line_length = self.__get_max_line_length(self.large_f)
        self.max_small_line_length = self.__get_max_line_length(self.small_f)
        # Parser and processors
        self.gcomm_processor = game_commands_processor
        self.parser = Parser(aerospace, game_commands_processor)

    def __get_max_line_length(self, fontobj):
        '''
        Return the maximum number of characters that can fit on a line of the
        console.
        '''
        chars_number = 2
        while True:
            chars_number += 1
            lines = ['-' * chars_number]
            width = U.render_lines(fontobj, lines, S.WHITE).get_width()
            if width > S.CLI_RECT.width:
                return chars_number - 2  #always leave some space to the right

    def __get_all_spellings_all_commands(self, commands):
        '''
        Return a list of all possible spellings of all the commands in a pool
        of commands.
        '''
        ret = []
        for c in commands.values():
            ret.extend(c['spellings'])
        return ret

    def __keep_longest_aliases(self, aliases):
        '''
        Return a list in which only the longest alias of a group of aliases
        sharing the same root is kept. For example if the arguments are
        ``['H', 'HEAD', 'HEADING']``, ``['HEADING']`` will be returned.
        '''
        filtered = []
        aset = set(aliases)
        for pool in (GAME_COMMANDS, PLANE_COMMANDS):
            for values in pool.values():
                tmp = set(values['spellings']) & aset
                if tmp:
                    filtered.append(sorted(list(tmp), key=len).pop())
        return filtered

    def _pick_shortest_alias(self, command):
        '''
        Return the shortes form for a command or None if the command spelling
        hasn't been found.
        '''
        for pool in (GAME_COMMANDS, PLANE_COMMANDS):
            for values in pool.values():
                spellings = values['spellings']
                if command in spellings:
                    return min(spellings, key=len)
        return None

    def _get_list_of_existing(self, what, context=None):
        '''
        Return a list of existing (=valid) strings representing `what`
        ('planes', 'airports', 'runaways' or 'beacons'). The `contex` value
        is used for those `what` which are not global to the aerospace (e.g.:
        runaways can be given for a given airport, not aerospace).
        '''
        if what == 'planes':
            return [p.icao for p in self.aerospace.aeroplanes]
        elif what == 'plane_commands':
            return self.__get_all_spellings_all_commands(PLANE_COMMANDS)
        elif what == 'airports':
            return [iata for iata in self.aerospace.airports.keys()]
        elif what == 'runaways':
            assert context != None  #Context must be the name of the airport
            for iata, ap in self.aerospace.airports.items():
                if iata == context:
                    return [r for r in ap.runways.keys()]
            return []
        elif what == 'beacons':
            return [id for id in self.aerospace.beacons.keys()]
        elif what == 'game_commands':
            return self.__get_all_spellings_all_commands(GAME_COMMANDS)
        elif what == 'all_commands':
            r = self.__get_all_spellings_all_commands(GAME_COMMANDS)
            r.extend(self.__get_all_spellings_all_commands(PLANE_COMMANDS))
            return r
        else:
            raise BaseException('Unknown type of items: %s!' % what)

    def _get_common_beginning(self, strings):
        '''
        Return the strings that is common to the beginning of each string in
        the strings list.
        '''
        result = []
        if not strings:
            return result
        limit = min([len(s) for s in strings])
        for i in range(limit):
            chs = set([s[i] for s in strings])
            if len(chs) == 1:
                result.append(chs.pop())
            else:
                break
        return ''.join(result)

    def _render_console_lines(self):
        '''
        Return the image of the rendered multiline text.
        Lines are passed in the format: [color_of_text, text].
        '''
        lines = self.console_lines
        font_height = self.small_f.get_height()
        surfaces = [self.small_f.render(txt, True, col) for col, txt in lines]
        maxwidth = max([s.get_width() for s in surfaces])
        result = pygame.surface.Surface((maxwidth, len(lines)*font_height),
                                        SRCALPHA)
        for i in range(len(lines)):
            result.blit(surfaces[i], (0,i*font_height))
        return result

    def _short_commmand(self, commandline):
        '''
        Reduce a command to its shortest form. Accepts a command line.
        '''
        if len(commandline.split()) <= 5:
            out = commandline.split()[1:]
        else:
            out = []
            for el in commandline.split()[1:]:
                shorty = self._pick_shortest_alias(el)
                out.append(shorty if shorty else el)
        return ' '.join(out)

    @property
    def text(self):
        '''
        The text presently on the commandline.
        '''
        return ''.join(self.chars)

    def msg_append(self, colour, text):
        '''
        Append a message to the console.
        '''
        log.debug(text)
        wrapped = textwrap.wrap(text,
                                width=self.max_small_line_length,
                                subsequent_indent=' ' * S.CONSOLE_INDENTATION)
        for line in wrapped:
            self.console_lines.append((colour, line))

    def autocomplete(self):
        '''
        Autocomplete the word-stub under the cursor.
        '''
        splitted = self.text.split()
        if not splitted:
            return  #early exit for empty line
        spl_len = len(splitted)
        what = None
        context = None
        # get the last three bits, if available
        root, pre, prepre = None, None, None
        if spl_len > 0:
            root = splitted[-1]
        if spl_len > 1:
            pre = splitted[-2]
        if spl_len > 2:
            prepre = splitted[-3]
        # identify what is the context of autocompletion
        if self.chars[0] == '/':
            splitted = self.text[1:].split()
            if len(splitted) == 1:  #we are typing a game command
                what = 'game_commands'
            elif len(splitted) == 2:  #we are typing an argument
                if splitted[0] == 'HELP':
                    what = 'all_commands'
                elif splitted[0] == 'LIST':
                    what = None
                elif splitted[0] == 'LOAD':
                    what = None
                elif splitted[0] == 'SCORES':
                    what = None
                elif splitted[0] == 'SORT':
                    what = None
            elif len(splitted) == 3: #we are typing a flag
                if splitted[0] == 'LIST':
                    what = None
        else:
            if root == self.text:
                what = 'planes'
            elif pre:
                if self.parser._validate_icao(pre):
                    what = 'plane_commands'
                # the argument of circling can be 'L' (left) which could be
                # understood as the shorthand for 'LAND'
                elif pre in PLANE_COMMANDS['LAND']['spellings'] and \
                     prepre not in PLANE_COMMANDS['CIRCLE']['spellings']:
                    what = 'airports'
                elif pre in PLANE_COMMANDS['HEADING']['spellings'] or \
                     pre in PLANE_COMMANDS['CLEAR']['spellings']:
                    what = 'beacons'
                elif prepre:
                    if prepre in PLANE_COMMANDS['LAND']['spellings']:
                        what = 'runaways'
                        context = pre
                    elif (self.parser._validate_icao(splitted[0]) or \
                         self.parser._validate_icao(splitted[1])) and \
                         pre not in PLANE_COMMANDS.keys():
                        what = 'plane_commands'
        if not what:
            return
        pool = [el.upper() for el in self._get_list_of_existing(what, context)]
        matches = [i for i in pool if i.find(root)==0]
        if what in ('plane_commands', 'game_commands', 'all_commands'):
            matches = self.__keep_longest_aliases(matches)
        if len(matches) == 1:
            match = matches[0]+' '
        elif len(matches) > 1:
            match = self._get_common_beginning(matches)
        else:
            return
        self.chars.extend(list(match[len(root):]))

    def do_parsing(self):
        '''
        Parse the input on the commandline.
        '''
        self.parser.initialise(self.text)
        parsed = self.parser.parse()
        # If an empty line has been parsed, skip everything
        if parsed == []:
            return
        # Parsing outcome: an iterable if successful OR a string if failure
        if type(parsed) in (unicode, str):
            answer_prefix = 'ERROR: '
            self.msg_append(S.KO_COLOUR, answer_prefix+parsed)
        else:
            callable_, args = parsed
            fname = callable_.__name__
            # Successfully parsed plane commands get logged on console and
            # inserted into command history.
            if fname == 'do':
                shortened_command = self._short_commmand(self.text)
                callable_.__self__.order_being_processed = shortened_command
                self.msg_append(S.NEUTRAL_COLOUR,
                                ' '.join((self.cmd_prefix,self.text)))
                self.command_history.insert(0, self.text)
            # ...and executed
            callable_(args)
            # Command line is emptied
            self.chars = []

    def process_keystroke(self, event):
        '''
        React to keystrokes.
        '''
        mods = pygame.key.get_mods()
        if event.key == K_RETURN:
            self.do_parsing()
            self.history_ptr = 0
        elif event.key == K_PAUSE:
            self.gcomm_processor(('PAUSE', []))
        elif event.key == K_ESCAPE:
            self.chars = []
        elif event.key == K_BACKSPACE and self.chars:
            self.chars.pop()  #one char is taken away in any case
            if mods & KMOD_LCTRL:
                while self.chars and self.chars.pop() != ' ':
                    pass
                if len(self.chars) > 0:  #restore trailing space
                    self.chars.append(' ')
        elif event.key == K_TAB:
            self.autocomplete()
        elif event.key == K_UP and \
                            self.history_ptr < len(self.command_history):
            self.chars = list(self.command_history[self.history_ptr])
            self.history_ptr += 1
        elif event.key == K_DOWN:
            if self.history_ptr > 1:
                self.history_ptr -= 1
                self.chars = list(self.command_history[self.history_ptr-1])
            elif self.history_ptr == 1:
                self.chars = []
                self.history_ptr = 0
        elif event.unicode in S.VALID_CHARS:
            character = event.unicode.upper()
            # No unintentional spaces (issued by appending empty chars due
            # to modifiers keys)
            if character == '':
                return
            # No leading spaces, no double spaces
            if character == ' ' and \
               (len(self.chars) == 0 or self.chars[-1] == ' '):
                return
            self.chars.append(character)
            # game command modifyer
            if event.unicode == '/':
                self.chars.append(' ')

    def draw(self):
        # Basic blinking of cursor
        cursor = '_' if int(time.time()*2) % 2 else ''
        # Re-drawing of the console lines is only done if the console lines
        # have changed since last iteration
        if self.last_console_snapshot != self.console_lines:
            self.last_console_snapshot = copy(self.console_lines)
            self.console_image = self._render_console_lines()
        image = self.large_f.render(self.text + cursor, True, S.WHITE, S.BLACK)
        sw, sh = self.surface.get_size()
        x = sw*0.01
        y = sh*0.03
        self.surface.fill(S.BLACK)
        self.surface.blit(self.console_image, (x,y))
        self.surface.blit(
          image, (x, 2 * y + self.small_f.get_height() * S.CONSOLE_LINES_NUM))

    def say(self, who, what, colour):
        '''
        Output a message on the console.
        '''
        self.msg_append(colour, ' '.join([who, S.PROMPT_SEPARATOR, what]))
