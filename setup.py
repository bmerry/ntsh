#!/usr/bin/env python3

from setuptools import setup

setup(
    name='kcpsh',
    version='0.1',
    packages=['kcpsh'],
    install_requires=['prompt_toolkit', 'pygments'],
    python_requires='>=3.5',
    author='Bruce Merry',
    entry_points={
        'console_scripts': [
            'kcpsh = kcpsh.main:main'
        ]
    }
)