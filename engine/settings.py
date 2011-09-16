#!/usr/bin/env python
# -*- coding: utf-8  -*-
'''
Globals variables and helper functions for the ATC game.

This module also provide "settings initilisation", meaning that it will scan
the user directory for a ``.atc-ng`` entry and either create it and populate it
with standard files, either load the custom files into the program.

Typical usage: "from globals import *"
'''

import pygame.display
import pygame.rect
import yaml
import os
import sys
import shutil
from pkg_resources import resource_filename as fname

__author__ = "Mac Ryan"
__copyright__ = "Copyright 2011, Mac Ryan"
__license__ = "GPL v3"
#__version__ = "1.0.0"
__maintainer__ = "Mac Ryan"
__email__ = "quasipedia@gmail.com"
__status__ = "Development"

# +------------------+
# | HELPER FUNCTIONS |
# +------------------+

def __get_ratioed_max_size(aspect_ratio):
    '''
    Return a list of screen modes that have the target ratio.
    '''
    # Not using `the lib.utils import rint` to avoid circular reference
    rint = lambda x : int(round(x))
    w, h = map(float, aspect_ratio.split(':'))
    # is it smaller the bounding window (MAX_WINDOW_SIZE) or the current
    # screen resolution?
    res_w = pygame.display.Info().current_w
    res_h = pygame.display.Info().current_h
    bound_w, bound_h = MAX_WINDOW_SIZE
    max_w, max_h = (res_w, res_h) if res_w < bound_w or res_h < bound_h \
                                  else (bound_w, bound_h)
    max_w, max_h = map(rint, (max_w, max_h))
    # Request available modes according to whether we are playing windowed
    # or full screen.
    if USE_FULLSCREEN:
        modes = pygame.display.list_modes()
    else:
        modes = pygame.display.list_modes(0,0)
    # -1 means "any values is ok" so...
    if modes == -1:
        # ...we return the size of the largest ratioed window within the box
        return (max_w, rint(max_w*h/w)) if w/h > max_w/max_h \
                                        else (rint(max_h*w/h), max_h)
    else:
        # ...we return the first "small" enough supported mode
        for ww, hh in modes:
            if ww/w == hh/h and ww <= max_w and hh <= max_h:
                return ww, hh

def __build_file_list(basedir):
    '''
    Return a list of all files relative under ``basedir``, relative to the base
    directory itself.
    '''
    files = []
    for dname, dlist, flist in os.walk(basedir):
        for fname in flist:
            absolute = os.path.join(dname, fname)
            files.append(os.path.relpath(absolute, basedir))
    return files

def __initialise_user_directory():
    '''
    If not present on the system, initialise the user directory ``.atc-ng``
    with a set of standard files.
    '''
    # if the target directory doesn't exist altogether
    if not os.path.isdir(__target_base):
        shutil.copytree(__template_base, __target_base)
        return
    # ...otherwise check file for file
    template_files = __build_file_list(__template_base)
    target_files = __build_file_list(__target_base)
    for fname in template_files:
        if fname not in target_files:
            template = os.path.join(__template_base, fname)
            target = os.path.join(__target_base, fname)
            target_dir = os.path.dirname(target)
            if not os.path.isdir(target_dir):
                os.mkdir(target_dir)
            shutil.copy2(template, target)

def __load_configuration_file(fname, filter=None):
    '''
    Load a configuration file, placing the values in the ``settings``
    namespace.
        If ``filter`` is passed (as a list), the function will import only
    those settings whose name is in the filter. This is primarily a way to
    impede a user to modify "protected" settings (like the scoring variables)
    from its own private settings.yml file.
        The function return a dictionary of imported property names.
    '''
    dict_ = yaml.load(open(fname))
    imported = []
    for k, v in dict_.items():
        if filter and k not in filter:
            #TODO: should be logged here, but it's circular reference...
            continue
        setattr(__current_module, k, v)
        imported.append(k)
    return imported

# +-----------------+
# | INITIALISATIONS |
# +-----------------+

pygame.init()
__home = os.path.expanduser('~')
__template_base = fname(__name__, os.path.join('data', 'template_user_dir'))
__target_base = os.path.join(__home, '.atc-ng')
__current_module = sys.modules[__name__]

# +---------------------+
# | LOAD DEFAULT VALUES |
# +---------------------+

__fname = fname(__name__, os.path.join('data', 'hardsettings.yml'))
__load_configuration_file(__fname)
__fname = os.path.join(__template_base, 'settings.yml')
__overridable_settings = __load_configuration_file(__fname)

# +------------------------------------+
# | OVERRIDES WITH USER-DEFINED VALUES |
# +------------------------------------+

__initialise_user_directory()
__fname = os.path.join(__home, '.atc-ng', 'settings.yml')
__load_configuration_file(__fname, __overridable_settings)

# +-----------------------------+
# | CALCULATE DERIVATIVE VALUES |
# +-----------------------------+

MAIN_FONT = fname(__name__, os.path.join('data', 'ex_modenine.ttf'))
WINDOW_SIZE = __get_ratioed_max_size(ASPECT_RATIO)
RADAR_RECT = pygame.rect.Rect(
     (WINDOW_SIZE[0]-WINDOW_SIZE[1]*(1-CONSOLE_HEIGHT))/2, 0,
      WINDOW_SIZE[1]*(1-CONSOLE_HEIGHT), WINDOW_SIZE[1]*(1-CONSOLE_HEIGHT))
METRES_PER_PIXEL = RADAR_RANGE*2.0/RADAR_RECT.width
CLI_RECT = pygame.rect.Rect(RADAR_RECT.x, RADAR_RECT.h+2,
                            RADAR_RECT.w, WINDOW_SIZE[1]-RADAR_RECT.h-2)
SCORE_RECT = pygame.rect.Rect(0, WINDOW_SIZE[1] - CLI_RECT.h/2,
                    # -2 for the lines separating GUI elements
                    (WINDOW_SIZE[0] - RADAR_RECT.w - 3) / 2, CLI_RECT.h/2)
STRIPS_RECT = pygame.rect.Rect(0, 0,
                    SCORE_RECT.w, WINDOW_SIZE[1] - SCORE_RECT.h - 1)
MAPS_RECT = pygame.rect.Rect(RADAR_RECT.x + RADAR_RECT.w + 1, 0,
        # -3 for the lines separating BUI elements
        (WINDOW_SIZE[0] - RADAR_RECT.w - STRIPS_RECT.w - 2), WINDOW_SIZE[1])


