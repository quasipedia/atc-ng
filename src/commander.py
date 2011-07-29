#!/usr/bin/env python
# -*- coding: utf-8  -*-
'''
Provide functionality for entering commands and processing them.
'''

#import  modules_names_here

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

    def __init__(self):
        self.chars = []

    @property
    def text(self):
        return ''.join(self.chars)

    def autocomplete(self):
        self.chars.extend(list('-auto-'))

    def validate(self):
        return True

def run_as_script():
    '''
    Allow to test the autocompletion and validation of commands.
    '''
    # Local initialisations
    valid_chars = \
        'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ 0123456789'
    cl = CommandLine()
    # World initialisation
    import world
    w = world.Aerospace()
    w.add_aeroport('ARN', ['18L', '18R'])
    w.add_aeroport('BMA', ['36'])
    w.add_plane('ABC1234')
    w.add_plane('XYZ1234')
    w.add_plane('MNO1234')
    # Curses initialisation
    import curses
    stdscr = curses.initscr()
    curses.savetty()
    stdscr.nodelay(True)
    curses.noecho()
    stdscr.addstr(2,5, '* Press `!` to end simulation')
    stdscr.addstr(3,5, '* Aeroplanes: ABC1234, XYZ1234, MNO1234')
    stdscr.addstr(3,5, '* Aeroports and runaways: ARN(18L,18R), BMA(36)')
    stdscr.addstr(6,5, '')
    while True:
        c = stdscr.getch()
        if c == -1:
            continue
        c = curses.unctrl(c)
        if c == '!':
            break
        if c == '^I':  #tab key
            cl.autocomplete()
        elif c == '^?' and len(cl.chars) > 0:  #backspace
            cl.chars.pop()
        elif c in valid_chars:
            # clear command validation message if any
            stdscr.addstr(8,5,'')
            stdscr.clrtoeol()
            # append valid char
            cl.chars.append(c)
        stdscr.addstr(5, 5, cl.text)
        stdscr.clrtoeol()
        if c == '^J':  #enter
            if cl.validate():
                stdscr.addstr(7,5,'VALID COMMAND!')
            else:
                stdscr.addstr(7,5,'Invalid command')
            stdscr.clrtoeol()
            cl.chars = []
    curses.resetty()
    curses.endwin()

if __name__ == '__main__':
    run_as_script()