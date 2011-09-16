#!/usr/bin/env python
# -*- coding: utf-8  -*-
'''
Generate the include files needed for the documentation.
'''

import yaml
import sys
import os
from pkg_resources import resource_stream


__author__ = "Mac Ryan"
__copyright__ = "Copyright 2011, Mac Ryan"
__license__ = "GPL v3"
#__version__ = "1.0.0"
__maintainer__ = "Mac Ryan"
__email__ = "quasipedia@gmail.com"
__status__ = "Development"


class Generator(object):

    '''
    Generator class to generate include files for rst documentation.

    Each method generate one of the files to be included in the documentation.
    '''

    def __init__(self):
        floc = os.path.abspath(__file__)
        thisdir = os.path.abspath(os.path.join(os.path.dirname(floc), '..'))
        sys.path.append(thisdir)
        self.eng_numbers = ['zero', 'one', 'two', 'three', 'four', 'five']

    def __load_yaml(self, package, fname):
        '''
        Load and return a yml file stored in the /data directory of `package`.
        '''
        data = resource_stream(__name__,
                           os.path.join('..', package, 'data', fname+'.yml'))
        return yaml.load(data)

    def generate_plane_commands(self):
        '''
        Description list with plane commands.
        '''
        commands = self.__load_yaml('engine', 'pcommands')
        lines = []
        for cname in sorted(commands):
            data = commands[cname]
            lines.append(cname.upper())       #command title
            lines.append('-'*len(cname))      #make it subsection
            lines.append('**Example Usage:**')
            lines.append(data['examples'])
            lines.append('**Description:**')
            lines.append('  ' + data['description'])
            lines.append('**Possible spellings:**')
            lines.append('  ' + ', '.join(data['spellings']).upper())
#            lines.append('**Number of arguments:**')
#            lines.append('  ' + self.eng_numbers[data['arguments']])
            lines.append('**Accepted flags:**')
            flags = data['flags']
            if flags:
                for flag, spellings in flags.items():
                    lines.append('  * ' + flag.upper() + '  (*spellings:* ' +
                                 ', '.join(spellings).upper() + ')')
            else:
                lines.append('  ---')
            lines.append('\n')
        #Save the file
        rst = '\n'.join(lines)
        f = open('pcommands.inc', 'w')
        f.write(rst)
        f.close()

    def generate_all(self):
        '''
        Generate all inclusion files.
        '''
        self.generate_plane_commands()

if __name__ == '__main__':
    Generator().generate_all()
