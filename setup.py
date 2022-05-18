#!/usr/bin/env python

from setuptools import setup
import os
import sys

HERE = os.path.abspath(os.path.dirname(__file__))
VERSION_NS = {}
with open(os.path.join(HERE, 'nbpublish', '_version.py')) as f:
    exec(f.read(), {}, VERSION_NS)

setup_args = dict(
    name='nbpublish',
    version=VERSION_NS['__version__'],
    description='Noteboook cleaner to publish',
    packages=['nbpublish'],
    package_dir={'nbpublish': 'nbpublish'},
    install_requires=[
        'nbformat>=5.0.0'
    ],
    python_requires='>=3.6',
    entry_points={
        'console_scripts': [
            'nbpublish = nbpublish.nbpublish:main'
        ]
    }
)

if __name__ == '__main__':
    setup(**setup_args)
