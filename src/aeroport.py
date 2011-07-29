#!/usr/bin/env python
# -*- coding: utf-8  -*-
'''
Aeroports modelling of the ATC simulation game.
'''

#import  modules_names_here

__author__ = "Mac Ryan"
__copyright__ = "Copyright 2011, Mac Ryan"
__license__ = "GPL v3"
#__version__ = "1.0.0"
__maintainer__ = "Mac Ryan"
__email__ = "quasipedia@gmail.com"
__status__ = "Development"


class Aeroport(object):

    '''
    Docstring.
    '''

    def __init__(self, iata, runaways):
        self.iata = iata
        self.runaways = runaways
