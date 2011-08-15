#!/usr/bin/env python
# -*- coding: utf-8  -*-
'''
Manage the collection of ICAO codes for airlines.

The collection of ICAO codes for airlines is huge. This module provide a class
to handle it, trying to optimise memory usage and processing speed.
'''

from random import randint
from yaml import load
try:  #try using the faster C version of the loader
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader
import re

__author__ = "Mac Ryan"
__copyright__ = "Copyright 2011, Mac Ryan"
__license__ = "GPL v3"
#__version__ = "1.0.0"
__maintainer__ = "Mac Ryan"
__email__ = "quasipedia@gmail.com"
__status__ = "Development"


class Handler(object):

    '''
    Handle the complete list of ICAO codes.
    '''

    def __init__(self):
        fname = '../descriptions/airline-codes.yml'
        self.__allcodes = load(open(fname), Loader=Loader)
        k, v = self.random_airline().popitem()
        self.valid_attributes = [k for k in v.keys()]

    def __filter_keys(self, **kwargs):
        '''
        Return a list of keys matching the filter criteria. Filter criteria are
        expressed as a dictionary whose entries are in the form:
        attribute_to_filter=regex_to_match
        '''
        # Check the parameters are sensible (correspond to existing attributes
        # of the airline entries or to their codes).
        for karg in kwargs.keys():
            if karg not in self.valid_attributes and karg!='code':
                msg = 'Unknown attribute to filter according to: "%s".' % karg
                raise BaseException(msg)
        # Iteratively reduce the matched set of keys
        ac = self.__allcodes
        if 'code' not in kwargs.keys():
            matched_keys = [k for k in ac.keys()]
        else:
            cmp = re.compile(kwargs['code'])
            matched_keys = [k for k in ac.keys() if cmp.search(k)]
            del kwargs['code']
        for key, regex in kwargs.iteritems():
            cmp = re.compile(regex)
            matched_keys = [k for k in matched_keys \
                            if cmp.search(ac[k][key])]
        return matched_keys

    def get(self, **kwargs):
        '''
        Return a list of airlines matching the filter criteria.
        (see self.__filter_keys() for info on the format of the search.
        No criteria = return the complete list.
        '''
        ac = self.__allcodes
        matched_keys = self.__filter_keys(**kwargs)
        return dict((k,ac[k]) for k in matched_keys)

    def random_airline(self):
        '''
        Return a list of only one random element from the complete list.
        '''
        keys = self.__allcodes.keys()
        key = keys[randint(1, len(keys))-1]
        return { key : self.__allcodes[key]}

    def random_flight(self):
        '''
        Return a randomly-generated flight number and its callsign.
        '''
        icao, vals = self.random_airline().popitem()
        num = randint(1,9999)
        fn = icao + str(num).zfill(4)
        cs = ' '.join((vals['callsign'], str(num))) if vals['callsign'] else fn
        return { 'icao' : fn, 'callsign' : cs}

    def shrink_self(self, **kwargs):
        '''
        Shrink the handler in place, by removing from the list of known ICAO's
        all the items that do not match the filtering criteria.
        (see self.__filter_keys() for info on the filtering format).
        '''
        ac = self.__allcodes
        matched_keys = self.__filter_keys(**kwargs)
        self.__allcodes = dict((k,ac[k]) for k in matched_keys)

    def len(self):
        '''
        Return the length of the list of known airlines.
        '''
        return len(self.__allcodes)