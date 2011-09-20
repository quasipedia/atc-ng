#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Provide support for handling version numbers for packaging python programs whose
code is mantained in a git repository.

©2011 - Mac Ryan - Released into the public domain.

The script will assing a version number to your program based on the last
signed tag on the repository branch you are building your package from.

The script assumes that source files where the version number needs to be
inserted contains a commented line whose first non-hash characters are
``__version__``. This is done to preserve the versioning number of third-party
modules that must not follow your code versioning schema, but can be overridden
from commandline.
'''

import argparse
import os
import sys
import re
import fileinput
from subprocess import Popen, PIPE

__all__ = ("get_git_version",)
__author__ = "Mac Ryan"
__copyright__ = "Copyright 2011, Mac Ryan"
__license__ = "Public Domain"

def get_git_version(branch, dump_to_file=False):
    '''
    Return the ``git describe --abbrev`` of a given branch.
    '''
    try:
        HASH_LEN = 4
        p = Popen(['git', 'describe', '--abbrev=%d' % HASH_LEN, branch],
                  stdout=PIPE, stderr=PIPE)
        p.stderr.close()
        version = p.stdout.readlines()[0].strip()
        if dump_to_file:
            f = open('version-number', 'w')
            f.write(version)
            f.close()
        return version
    except:
        raise ValueError("Cannot find the version number!")

def __get_source_files():
    '''
    Return a list of all source files, search in all subdirectories of the
    curren one (=ignores the current one).
    '''
    fnames = []
    for dirname, dirlist, filelist in os.walk('.'):
        if dirname == '.' or dirname.find('./.git') != -1:
            continue
        for name in filelist:
            if name[-3:] != '.py':
                continue
            fnames.append(os.path.join(dirname, name))
    return fnames

def __replace_in_file(fname, version_number, substite_uncommented=False):
    '''
    Replace ``__version__`` metadata in a given file.
    '''
    if substite_uncommented:
        pattern = re.compile(r'^#*__version__')
    else:
        pattern = re.compile(r'#+__version__')
    counter = 0
    for line in fileinput.input(fname, inplace=True):
        if pattern.search(line):
            counter += 1
            line = '__version__ = "%s"\n' % version_number
        sys.stdout.write(line)
    if counter:
        return counter, fname
    return None

def substitute_in_source(branch, substite_uncommented=False):
    '''
    Substitute program version number in source files.
    '''
    version = get_git_version(branch, dump_to_file=False)
    fnames = __get_source_files()
    substitutions = []
    for fn in fnames:
        r = __replace_in_file(fn, version, substite_uncommented)
        if r:
            substitutions.append(r)
    return substitutions

def parse():
    '''
    Argparse descriptor.
    '''
    # General description of the program
    desc = 'Support for automatic version numbers in python .deb packages.'
    parser = argparse.ArgumentParser(description=desc)
    # The action to untertake
    hlpmsg = 'The action to untertake.'
    parser.add_argument('action', choices=['get', 'substitute'], nargs=1,
                        help=hlpmsg)
    # Specify a particular branch
    hlpmsg = 'Specify a git branch to get the version number from. Defaults ' \
             'to `master`.'
    parser.add_argument('-b', '--branch', default='master', help=hlpmsg)
    # Dump to file option
    hlpmsg = 'Whether the version number should also be dumped in the ' \
             '`version-number` file.'
    parser.add_argument('-d', '--dump', action='store_true', help=hlpmsg)
    # Substitute uncommented too
    hlpmsg = 'Whether the subtitution in source files should also apply to' \
             'uncommented ``__version__`` declarations.'
    parser.add_argument('-u', '--uncommented', action='store_true', help=hlpmsg)
    # Parse!
    args = parser.parse_args()
    if args.action == ['get']:
        version = get_git_version(args.branch, args.dump)
        print "Software version on branch `%s`: %s." % (args.branch, version)
    elif args.action == ['substitute']:
        subs = substitute_in_source(args.branch, args.uncommented)
        if not subs:
            print "No substitutions have been performed."
        else:
            fnumb = len(subs)
            total = sum([n for n,f in subs])
            print "Substitution happened in the follwing files:"
            for data in subs:
                print "%i : %s" % data
            print "Overall total substitutions: %i in %i files" % (total, fnumb)

if __name__ == "__main__":
    parse()
