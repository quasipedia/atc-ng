#!/usr/bin/env python
# -*- coding: utf-8  -*-
'''
Manage data stored as YAML files on system.

The collection of ICAO codes for airlines is huge. This module provide a class
to handle it, trying to optimise memory usage and processing speed.

Aeroplanes, airports and Scenarios are also built through classes of this
module.
'''

# Regular imports
import random
import re
import entities.airport
import entities.waypoints
import os.path as path
from os import listdir
from pkg_resources import resource_stream, resource_listdir
# Yaml imports. It tries to use the faster C version of the loader.
from yaml import load
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

__author__ = "Mac Ryan"
__copyright__ = "Copyright 2011, Mac Ryan"
__license__ = "GPL v3"
#__version__ = "1.0.0"
__maintainer__ = "Mac Ryan"
__email__ = "quasipedia@gmail.com"
__status__ = "Development"


class YamlHandler(object):

    '''
    Ancestor class for handlers that provide some helper method.
    '''

    DIRECTORY = 'data'
    EXT = '.yml'

    def load(self, fname):
        '''
        Load a yaml file and store it in the self._data property.
        '''
        data = resource_stream(__name__,
                               path.join(self.DIRECTORY, fname + self.EXT))
        self._data = load(data, Loader=Loader)


class AirlinesHandler(YamlHandler):

    '''
    Handle the complete list of ICAO codes.
    '''

    def __init__(self):
        self.load('airline-codes')
        # For a number of good reasons, the icao code of airlines is stored in
        # the file as the key of the dictionary. We also want that bit of
        # information stored amongs values, though.
        for k in self._data.keys():
            self._data[k]['icao'] = k
        rdm = self.random_airline()
        self.valid_attributes = [k for k in rdm.keys()]

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
        ac = self._data
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
        ac = self._data
        matched_keys = self.__filter_keys(**kwargs)
        return dict((k,ac[k]) for k in matched_keys)

    def random_airline(self):
        '''
        Return a list of only one random element from the complete list.
        '''
        return random.choice(self._data.values())

    def random_flight(self):
        '''
        Return a randomly-generated flight number and its callsign.
        '''
        rnd = self.random_airline()
        num = random.randint(1,9999)
        fn = rnd['icao'] + str(num).zfill(4)
        cs = ' '.join((rnd['callsign'], str(num))) if rnd['callsign'] else fn
        return { 'icao' : fn, 'callsign' : cs}

    def shrink_self(self, **kwargs):
        '''
        Shrink the handler in place, by removing from the list of known ICAO's
        all the items that do not match the filtering criteria.
        (see self.__filter_keys() for info on the filtering format).
        '''
        ac = self._data
        matched_keys = self.__filter_keys(**kwargs)
        self._data = dict((k,ac[k]) for k in matched_keys)

    def len(self):
        '''
        Return the length of the list of known airlines.
        '''
        return len(self.__allcodes)


class airportHandler(YamlHandler):

    '''
    Handle airports descriptions.
    '''

    def __init__(self, iata):
        self.DIRECTORY = path.join(self.DIRECTORY, 'airports')
        self.load(iata)
        strips = [entities.airport.AsphaltStrip(**rw)
                  for rw in self._data['strips']]
        self.airport = \
            entities.airport.airport(strips=strips, **self._data['airport'])


class ScenarioHandler(YamlHandler):

    '''
    Handle scenario descriptions.
    '''

    def __init__(self, fname):
        self.DIRECTORY = path.join(self.DIRECTORY, 'scenarios')
        self.load(fname)
        # airports
        self.airports = []
        for item in self._data['airports']:
            ap = airportHandler(item['real_iata']).airport
            ap.iata = item['new_iata']
            ap.name = item['new_name']
            ap.location = item['location']
            self.airports.append(ap)
        # Gates
        self.gates = []
        for item in self._data['gates']:
            gate = entities.waypoints.Gate(**item)
            self.gates.append(gate)
        # Beacons
        self.beacons = []
        for item in self._data['beacons']:
            beacon = entities.waypoints.Beacon(**item)
            self.beacons.append(beacon)


class PlaneModelHandler(YamlHandler):

    '''
    Handle aeroplanes model descriptions.
    '''

    def __init__(self):
        self.DIRECTORY = path.join(self.DIRECTORY, 'aeroplanes')
        data = {}
        fnames = resource_listdir('entities', self.DIRECTORY)
        fnames = [n[:-4] for n in fnames if n[-4:] == '.yml']
        for fname in fnames:
            self.load(fname)
            # Convert data in kph to m/s
            self._data['max_speed'] /= 3.6
            self._data['landing_speed'] /= 3.6
            data[self._data['model']] = self._data
        del self._data
        self.__models = data

    def random_model(self):
        '''
        Return the dictionary descriptor of a random model.
        '''
        return random.choice(self.__models.values())