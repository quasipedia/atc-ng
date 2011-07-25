#!/usr/bin/env python
# -*- coding: utf-8  -*-
'''
Provides the game logic for the ATC game.

Amongst others:
    - manage the appearance / disappearance of planes on the world
    - keep track of score
    - invokes AI support for planes in emergency
'''

from settings import *
import world

__author__ = "Mac Ryan"
__copyright__ = "Copyright 2011, Mac Ryan"
#__credits__ = ["Name Lastname", "Name Lastname"]
__license__ = "GPL v3"
#__version__ = "1.0.0"
__maintainer__ = "Mac Ryan"
__email__ = "quasipedia@gmail.com"
__status__ = "Development"


class GameLogic(object):

    '''
    Docstring.
    '''

    def __init__(self):
        self.world = world.Aerospace()
        self.__quick_start()

    def __quick_start(self):
        for i in range(1):
            self.world.add_plane()

    def update(self):
        self.world.update()

    def draw(self, surface):
        self.world.draw(surface)


