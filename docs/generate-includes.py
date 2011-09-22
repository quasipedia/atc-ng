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
#__version__ = "<dev>"
#__date__ = "<unknown>"
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
                           os.path.join('..', package, 'data', fname + '.yml'))
        return yaml.load(data)

    def __attach_combo_info(self, commands):
        '''
        Attach the information on combatible commands to the PLANE_COMMANDS dict.
        '''
        combos = self.__load_yaml('engine', 'pcombos')
        dict_ = {}
        # Create initial dictionary
        for combo in combos:
            for command in combo:
                try:
                    dict_[command].extend(combo)
                except KeyError:
                    dict_[command] = combo
        # Eliminates redoundancies and self and attach on target dictionary
        for k, v in dict_.items():
            commands[k]['combos'] = list(set(v) - set([k]))

    def parse_commands_description_file(self, fname):
        '''
        Parse the commands description file and return the rst output.
        ``fname`` is both the name of the .yml file to load the data from and
        that of the .inc file into which to dump the rst content.
        '''
        assert fname in ['pcommands', 'gcommands']
        commands = self.__load_yaml('engine', fname)
        if fname == 'pcommands':
            extended_name = 'Aeroplane command'
            self.__attach_combo_info(commands)
        if fname == 'gcommands':
            extended_name = 'Game command'
        lines = []
        lines.append('.. highlight:: none\n')
        for cname in sorted(commands):
            data = commands[cname]
            lines.append('.. index:: ' + extended_name + '; ' + cname + '\n')
            lines.append('.. _' + fname + '-' + cname + ':\n')  #anchor
            lines.append(cname) #command title
            lines.append('-'*len(cname)) #make it subsection
            lines.append('**Example Usage:**')
            lines.append(data['examples'])
            lines.append('**Description:**')
            lines.append('  ' + data['description'])
            lines.append('**Possible spellings:**')
            lines.append('  ' + ', '.join(data['spellings']))
#            lines.append('**Number of arguments:**')
#            lines.append('  ' + self.eng_numbers[data['arguments']])
            lines.append('**Accepted flags:**')
            flags = data['flags']
            if flags:
                for flag, spellings in flags.items():
                    lines.append('  * ' + flag + '  (*spellings:* ' +
                                 ', '.join(spellings) + ')')
            else:
                lines.append('  ---')
            if 'combos' in data.keys():
                lines.append('**Can be combined with:**')
                lines.append('  ' + ', '.join([c+'_' for c in data['combos']]))
            lines.append('\n')
        #Save the file
        rst = '\n'.join(lines)
        f = open(fname + '.inc', 'w')
        f.write(rst)
        f.close()

    def generate_all(self):
        '''
        Generate all inclusion files.
        '''
        for fname in ['pcommands', 'gcommands']:
            self.parse_commands_description_file(fname)

if __name__ == '__main__':
    Generator().generate_all()
