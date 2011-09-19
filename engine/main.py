#!/usr/bin/env python
# -*- coding: utf-8  -*-from pygamehelper import *
'''
This is the main program of the ATC game.

The ATC game is one of the many "Air Traffic Controller" games available "out
there". It's implemented in python (with pygame).

This module sole purpose is to initialise and manage the pygame environment.
'''

from engine.settings import *
from engine.logger import log
from pygame.locals import *
from logger import log
import engine.settings
import pygame.display
import pygame.image
import traceback
from pkg_resources import resource_filename

__author__ = "Mac Ryan"
__copyright__ = "Copyright 2011, Mac Ryan"
__license__ = "GPL v3"
#__version__ = "1.0.0"
__maintainer__ = "Mac Ryan"
__email__ = "quasipedia@gmail.com"
__status__ = "Development"

#TODO: verify .deb package with `lintian`
#FIXME: the game will break with airports below seal level (e.g. Schiphol)
#       due to the use of plane.position.z < -1 throughout the code.
#TODO: REFACTOR using pygame events? Check if makes sense with PyGLets

class MainWindow(object):

    def __init__(self):
        # Initialisation of pygame environment
        fn = resource_filename(__name__, os.path.join('data', 'icon.png'))
        icon = pygame.image.load(fn)
        pygame.display.set_icon(icon)
        if USE_FULLSCREEN:
            self.screen = pygame.display.set_mode(WINDOW_SIZE,
                                                  pygame.FULLSCREEN)
            pygame.display.toggle_fullscreen()
        else:
            self.screen = pygame.display.set_mode(WINDOW_SIZE)
        self.screen.fill(BLACK)
        pygame.display.flip()
        # Create timer
        self.clock = pygame.time.Clock() #to track FPS
        self.fps= 0
        # Create game logic - the import happens here because the module
        # initialisation requires the pygame environment to be initialised
        import gamelogic
        self.game_logic = gamelogic.GameLogic(self.screen)
        # State machine
        self.running = False

    def handle_events(self):
        '''
        Route pygame events to the appropriate handler.
        '''
        for event in pygame.event.get():
            if event.type == QUIT:
                self.game_logic.machine_state = MS_QUIT
            elif event.type == KEYDOWN:
                self.game_logic.key_pressed(event)

    def main_loop(self):
        '''
        Start the main loop.
        The mainloop is active until the machine state "running" is set to
        False.
        '''
        while self.game_logic.machine_state == MS_RUN:
            capt = "Air Traffic Controller - NG     (FPS: %i)"
            pygame.display.set_caption(capt % self.clock.get_fps())
            self.handle_events()
            self.game_logic.update(self.clock.get_time())
            pygame.display.flip()
            self.clock.tick(MAX_FRAMERATE)

def main():
    try:
        version = __version__  #this is normallly set when package is buit
    except NameError:
        version = '<unknown>'
    try:
        log.info('### NEW MATCH - Game version: %s ################' % version)
        MainWindow().main_loop()
    except:
        trace = traceback.format_exc()
        log.critical(trace)
        print trace
        sys.exit(1)

if __name__ == '__main__':
    main()
