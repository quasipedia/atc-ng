#!/usr/bin/env python
# -*- coding: utf-8  -*-
'''
This utility scrapes the wikipedia entry for airline ICAO codes.

Source: http://en.wikipedia.org/wiki/Airline_codes-All
'''

from BeautifulSoup import BeautifulSoup as Soup
from collections import OrderedDict
from textwrap import dedent
from datetime import datetime as dt
import openanything
import yaml
import re

__author__ = "Mac Ryan"
__copyright__ = "Copyright 2011, Mac Ryan"
__license__ = "GPL v3"
#__version__ = "1.0.0"
__maintainer__ = "Mac Ryan"
__email__ = "quasipedia@gmail.com"
__status__ = "Development"

HEADER = '''\
    # ICAO codes for known airlines
    #
    # ©2011 Mac Ryan - Licensed under GPL v.3
    #
    # This file is intended to work with the ATC-NG game available at
    # https://github.com/quasipedia/atc-ng)
    #
    '''

def run_as_script():
    # Get the page content, this requires changing the user-agent, as the
    # default one is filtered out by wikipedia.
    url = 'http://en.wikipedia.org/wiki/Airline_codes-All'
    result = openanything.fetch(url)
    if result['status'] != 200:
        exit('The server returned: %s' % result['status'])
    soup = Soup(result['data'])
    # Find the table and parse the data
    table = soup('table', {'class' : 'toccolours sortable'})[0]
    data = [[c.text.encode('UTF-8') \
             for (n, c) in enumerate(row.findAll('td')) if n in (1,2,3,4)] \
             for row in table.findAll('tr')]
    # Remove empty lines and convert it to an ordered dictionary (this is only
    # useful for facilitating inspection of the file - that will be sorted
    # alphabetically)
    dict_keys = ('airline', 'callsign', 'country')
    main_dict = {}
    for row in data:
        if row and row[0] and row[1]:
            main_dict[row[0]] = dict(zip(dict_keys, row[1:]))
    # YAML generation
    data = yaml.dump(main_dict, default_flow_style=False, allow_unicode=False,
                                width = 79)
    f = open('airline-codes.yml', 'w')
    f.write(dedent(HEADER))
    now = dt.now().strftime('%d %B %Y')
    f.write('# Last scraped from wikipedia on: %s\n\n' % now)
    f.write(data)
    f.close()

if __name__ == '__main__':
    run_as_script()