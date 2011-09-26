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
from pkg_resources import resource_filename as fname #@UnresolvedImport

__author__ = "Mac Ryan"
__copyright__ = "Copyright 2011, Mac Ryan"
__license__ = "GPL v3"
#__version__ = "<dev>"
#__date__ = "<unknown>"
__maintainer__ = "Mac Ryan"
__email__ = "quasipedia@gmail.com"
__status__ = "Development"
__all__ = ['settings']


class Settings(object):

    '''
    Container class for all program-wide settings. @DynamicAttrs

    It implements the borg pattern as suggested by Alex Martelli:
    http://code.activestate.com/recipes/66531
    '''

    __shared_state = {}
    __home = os.path.expanduser('~')
    __template_base = fname(__name__, os.path.join('data',
                                                   'template_user_dir'))
    __target_base = os.path.join(__home, '.atc-ng')
    __current_module = sys.modules[__name__]

    def __init__(self):
        '''
        Check that the class hasn't been instantiated before, then load all
        the settings.
        '''
        self.__dict__ = self.__shared_state # borg pattern!

        # +---------------------+
        # | LOAD DEFAULT VALUES |
        # +---------------------+

        __fname = fname(__name__, os.path.join('data', 'hardsettings.yml'))
        self.__load_configuration_file(__fname)
        __fname = os.path.join(self.__template_base, 'settings.yml')
        __overridable_settings = self.__load_configuration_file(__fname)

        # +------------------------------------+
        # | OVERRIDES WITH USER-DEFINED VALUES |
        # +------------------------------------+

        self.__initialise_user_directory()
        __fname = os.path.join(self.__home, '.atc-ng', 'settings.yml')
        self.__load_configuration_file(__fname, __overridable_settings)

        # +--------------------+
        # | HARDCORE VARIABLES |
        # +--------------------+

        self.LEFT = self.CCW = self.L = -1
        self.RIGHT = self.CW = self.R = +1

        # +-----------------------------+
        # | CALCULATE DERIVATIVE VALUES |
        # +-----------------------------+

        self.PING_IN_SECONDS = self.PING_PERIOD / 1000.0
        self.MAIN_FONT = fname(
              __name__, os.path.join('data', 'ex_modenine.ttf'))
        self.WINDOW_SIZE = self.__get_ratioed_max_size(self.ASPECT_RATIO)
        self.RADAR_RECT = pygame.rect.Rect(
              (self.WINDOW_SIZE[0] - self.WINDOW_SIZE[1] * \
              (1 - self.CONSOLE_HEIGHT)) / 2, 0,
              self.WINDOW_SIZE[1] * (1-self.CONSOLE_HEIGHT),
              self.WINDOW_SIZE[1] * (1-self.CONSOLE_HEIGHT))
        self.METRES_PER_PIXEL = self.RADAR_RANGE * 2.0 / self.RADAR_RECT.width
        self.CLI_RECT = pygame.rect.Rect(
              self.RADAR_RECT.x, self.RADAR_RECT.h+2,
              self.RADAR_RECT.w, self.WINDOW_SIZE[1] - self.RADAR_RECT.h-2)
        self.SCORE_RECT = pygame.rect.Rect(
              0, self.WINDOW_SIZE[1] - self.CLI_RECT.h / 2,
              # -2 for the lines separating GUI elements
              (self.WINDOW_SIZE[0] - self.RADAR_RECT.w - 3) / 2,
              self.CLI_RECT.h/2)
        self.STRIPS_RECT = pygame.rect.Rect(
              0, 0, self.SCORE_RECT.w,
              self.WINDOW_SIZE[1] - self.SCORE_RECT.h - 1)
        self.MAPS_RECT = pygame.rect.Rect(
              self.RADAR_RECT.x + self.RADAR_RECT.w + 1, 0,
              # -3 for the lines separating BUI elements
              (self.WINDOW_SIZE[0] - self.RADAR_RECT.w - \
               self.STRIPS_RECT.w - 2), self.WINDOW_SIZE[1])

    def __get_ratioed_max_size(self, aspect_ratio):
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
        bound_w, bound_h = self.MAX_WINDOW_SIZE
        max_w, max_h = (res_w, res_h) if res_w < bound_w or res_h < bound_h \
                                      else (bound_w, bound_h)
        max_w, max_h = map(rint, (max_w, max_h))
        # Request available modes according to whether we are playing windowed
        # or full screen.
        if self.USE_FULLSCREEN:
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

    def __build_file_list(self, basedir):
        '''
        Return a list of all files under ``basedir``, relative to the base
        directory itself.
        '''
        files = []
        for dname, dlist, flist in os.walk(basedir):
            for fname in flist:
                absolute = os.path.join(dname, fname)
                files.append(os.path.relpath(absolute, basedir))
        return files

    def __initialise_user_directory(self):
        '''
        If not present on the system, initialise the user directory ``.atc-ng``
        with a set of standard files.
        '''
        # if the target directory doesn't exist altogether
        if not os.path.isdir(self.__target_base):
            shutil.copytree(self.__template_base, self.__target_base)
            return
        # ...otherwise check file for file
        template_files = self.__build_file_list(self.__template_base)
        target_files = self.__build_file_list(self.__target_base)
        for fname in template_files:
            if fname not in target_files:
                template = os.path.join(self.__template_base, fname)
                target = os.path.join(self.__target_base, fname)
                target_dir = os.path.dirname(target)
                if not os.path.isdir(target_dir):
                    os.mkdir(target_dir)
                shutil.copy2(template, target)

    def __load_configuration_file(self, fname, filter=None):
        '''
        Load a configuration file, placing the values in the ``settings``
        namespace.
            If ``filter`` is passed (as a list), the function will import only
        those settings whose name is in the filter. This is primarily a way to
        impede a user to modify "protected" settings (like the scoring
        variables) from its own private settings.yml file.
            The function return a dictionary of imported property names.
        '''
        dict_ = yaml.load(open(fname))
        imported = []
        for k, v in dict_.items():
            if filter and k not in filter:
                #TODO: should be logged here, but it's circular reference...
                continue
            setattr(self, k, v)
            imported.append(k)
        return imported



# THIS ONLY RUN ONCE, WHEN THE MODULE IS FIRST LOADED.
pygame.init()
settings = Settings()