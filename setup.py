#!/usr/bin/env python
# -*- coding: utf-8  -*-

from setuptools import setup, find_packages
from version import *

#v = open(os.path.join(os.path.dirname(__file__), 'mako', '__init__.py'))
#VERSION = re.compile(r".*__version__ = '(.*?)'", re.S).match(v.read()).group(1)
#v.close()

#_top_dir = os.path.dirname(os.path.abspath(__file__))
#sys.path.insert(0, os.path.join(_top_dir, "lib"))
#try:
#    import appdirs
#finally:
#    del sys.path[0]
#README = open(os.path.join(_top_dir, 'README.rst')).read()

setup(
    name = "atc-ng",
    version = get_git_version(),
    description = "Air Traffic Controller - Next Generation",
    packages = find_packages(exclude=['utils']),
    include_package_data = True,
    data_files=[('/usr/share/pixmaps/', ['atc-ng.xpm'])],
    install_requires = ['Pygame>=1.8', 'PyYAML >= 3.9'],
    entry_points = {
        'gui_scripts': ['atc-ng = engine.main:main']
    },
    # metadata for upload to PyPI
    author = "Mac Ryan",
    author_email = "quasipedia@gmail.com",
    license = "GPL v3",
    keywords = "game atc radar air traffic controller strategy",
    url = "https://github.com/quasipedia/atc-ng",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: X11 Applications',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Other Audience',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Topic :: Games/Entertainment',
        'Topic :: Games/Entertainment :: Real Time Strategy',
        'Topic :: Games/Entertainment :: Simulation',
    ],
    long_description = '''A real-time strategy game in which you must guide
aeroplanes through the airspace you monitor at your radar station.
This game is inspired from the original text-only game from the '80s called ATC [available in Ubuntu in the 'bsdgames' package.]'"'''
)
