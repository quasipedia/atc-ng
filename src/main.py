#!/usr/bin/env python
# -*- coding: utf-8  -*-from pygamehelper import *
'''
This is the main program of the ATC game.

The ATC game is one of the many "Air Traffic Controller" games available "out
there". It's implemented in python (with pygame).

This module sole purpose is to initialise and manage the pygame environment.
'''

from settings import *
from pygame.locals import *
import pygame.display

__author__ = "Mac Ryan"
__copyright__ = "Copyright 2011, Mac Ryan"
__license__ = "GPL v3"
#__version__ = "1.0.0"
__maintainer__ = "Mac Ryan"
__email__ = "quasipedia@gmail.com"
__status__ = "Development"

class MainWindow(object):

    def __init__(self):
        # Initialisation of pygame environment
        pygame.init()
        self.screen = pygame.display.set_mode(WINDOW_SIZE)
        self.screen.fill(BLACK)
        pygame.display.flip()
        # Create timer
        self.clock = pygame.time.Clock() #to track FPS
        self.fps= 0
        # Create game logic - the import happens here because the module
        # initialisation requires the pygame environment to be initialised
        import gamelogic
        self.game_logic = gamelogic.GameLogic()
        # State machine
        self.running = False

    def handle_events(self):
        '''
        Route pygame events to the appropriate handler.
        '''
        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False
#            elif event.type == KEYDOWN:
#                self.keyDown(event.key)
#            elif event.type == KEYUP:
#                if event.key == K_ESCAPE:
#                    self.running = False
#                self.keyUp(event.key)
#            elif event.type == MOUSEBUTTONUP:
#                self.mouseUp(event.button, event.pos)
#            elif event.type == MOUSEMOTION:
#                self.mouseMotion(event.buttons, event.pos, event.rel)

    def main_loop(self):
        '''
        Start the main loop.
        The mainloop is active until the machine state "running" is set to
        False.
        '''
        self.running = True

        while self.running:
            pygame.display.set_caption("FPS: %i" % self.clock.get_fps())
            self.handle_events()
            self.game_logic.update()
            self.game_logic.draw(self.screen)
            pygame.display.flip()
            self.clock.tick(MAX_FRAMERATE)

if __name__ == '__main__':
    MainWindow().main_loop()