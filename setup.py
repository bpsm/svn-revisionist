#!/usr/bin/env python

from distutils.core import setup
setup(
    name='revisionist',
    version='1.0.0',
    description='Library to parse and modify Subversion dumpfiles.',
    author="Ben Smith-Mannschott",
    author_email="benpsm@gmail.com",
    packages=["revisionist"],
    scripts=['revisionist-fixprops.py'],
    package_data={'revisionist': ['*.dump2', '*.dump3']}
    )
    
    
