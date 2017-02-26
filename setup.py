#!/usr/bin/env python3

from setuptools import setup

setup(
    name='ntsh',
    description='Interactive tool for line-based protocols',
    version='0.1',
    packages=['ntsh'],
    install_requires=['prompt_toolkit', 'pygments'],
    python_requires='>=3.5',
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
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: System :: Networking'
    ]
)
