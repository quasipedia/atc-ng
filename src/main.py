#!/usr/bin/env python
# -*- coding: utf-8  -*-from pygamehelper import *
'''
Docstring.

Docstring. Docstring. Docstring. Docstring. Docstring. Docstring.
'''

import pygamehelper
import aeroplane
from pygame import *
from pygame.locals import *

__author__ = "Mac Ryan"
__copyright__ = "Copyright 2011, Mac Ryan"
__license__ = "GPL v3"
#__version__ = "1.0.0"
__maintainer__ = "Mac Ryan"
__email__ = "quasipedia@gmail.com"
__status__ = "Development"

class MainWindow(pygamehelper.PygameHelper):

    def __init__(self, width=1024, height=768):
        self.w, self.h = width, height
        super(MainWindow, self).__init__(size=(width, height), fill=((0,0,0)))
        self.planes = []
        for i in range(5):
            self.planes.append(aeroplane.Aeroplane())

    def update(self):
        for plane in self.planes:
            plane.update()

    def keyUp(self, key):
        pass

    def mouseUp(self, button, pos):
        pass

    def mouseMotion(self, buttons, pos, rel):
        pass

    def draw(self):
        self.screen.fill((0,0,0))
        for plane in self.planes:
            plane.draw(self.screen)

if __name__ == '__main__':
    mw = MainWindow()
    mw.mainLoop(40)