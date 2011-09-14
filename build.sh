#! /bin/bash
./clean.sh
#python setup.py --command-packages=stdeb.command debianize
python setup.py --command-packages=stdeb.command bdist_deb
