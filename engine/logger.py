#!/usr/bin/env python
# -*- coding: utf-8  -*-
'''
Provide logging capabilities to the ATC-NG game.
'''

from engine.settings import *
from time import strftime
import logging
import inspect
import os

__author__ = "Mac Ryan"
__copyright__ = "Copyright 2011, Mac Ryan"
__license__ = "GPL v3"
#__version__ = "<dev>"
#__date__ = "<unknown>"
__maintainer__ = "Mac Ryan"
__email__ = "quasipedia@gmail.com"
__status__ = "Development"


def __remove_old_logs():
    '''
    Removes old logs from the system.
    '''
    logs = [el for el in os.listdir(__log_dir) if el[-4:] == '.log']
    logs = sorted(logs, reverse=True)
    while len(logs) >= LOG_NUMBER:
        os.unlink(os.path.join(__log_dir, logs.pop()))

def __get_logger():
    '''
    Prepare and reuturn the main logger object, used throughout ATC-NG.
    '''
    YAML_LOOKUP = dict(debug = logging.DEBUG,
                       info = logging.INFO,
                       warning = logging.WARNING,
                       error = logging.ERROR,
                       critical = logging.CRITICAL)
    # Establish what level of logging is required
    if LOG_THRESHOLD not in YAML_LOOKUP:
        msg = 'Incorrect LOG_THRESHOLD value in the setting file!'
        raise BaseException(msg)
    # Create a logging instance and set it's threshold
    log = logging.getLogger('main')
    log.setLevel(YAML_LOOKUP[LOG_THRESHOLD])
    # Set the handler (file output)
    fname = os.path.join(__log_dir, strftime('%Y-%m-%d@%Hh%M.log'))
    handler_file = logging.FileHandler(fname)
    # Set the format of the logging messages
    fmt = '%(relativeCreated)8d %(levelname)-9s %(module)-20s %(message)s'
    datefmt='%H:%M:%S'
    handler_file.setFormatter(logging.Formatter(fmt=fmt, datefmt=datefmt))
    log.addHandler(handler_file)
    return log

__log_dir = os.path.join(os.path.expanduser('~'), '.atc-ng', 'logs')
__remove_old_logs()
log = __get_logger()