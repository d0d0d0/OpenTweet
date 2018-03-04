from distutils.core import setup
import py2exe, sys, os

## Generate executable for windows

sys.argv.append('py2exe')

setup(
    options = {'py2exe': {'bundle_files': 1}},
    windows = [{'script': "geotweet.py"}],
    zipfile = None,
)