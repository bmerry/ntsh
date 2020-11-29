#!/usr/bin/env python3

# ntsh: an interactive tool for line-based protocols
# Copyright (C) 2017, 2018, 2020  Bruce Merry
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from setuptools import setup, find_packages

setup(
    name='ntsh',
    description='Interactive tool for line-based protocols',
    version='1.1.1',
    packages=find_packages(),
    install_requires=['prompt_toolkit>=3,<4', 'pygments', 'appdirs'],
    python_requires='>=3.6',
    author='Bruce Merry',
    entry_points={
        'console_scripts': [
            'ntsh = ntsh.main:main'
        ]
    },
    long_description='''
        ntsh is an interactive tool for line-based protocols, such as HTTP
        or SMTP. It can be thought of as a netcat that's better suited to
        interactive use by a human. Features include an editable prompt,
        history, and syntax highlighting, and asynchronous replies from
        the server won't interfere with the prompt.
        ''',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: System :: Networking'
    ]
)
