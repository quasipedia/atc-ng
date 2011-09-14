#! /bin/bash
rm -r -d *.egg-info/ dist/ distribute*.gz distribute*.egg distribute_setup.pyc deb_dist/ debian/
find . -name ".pyc" -type d -exec rm -rf {} \;
