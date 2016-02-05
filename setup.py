#!/usr/bin/env python3
#
# Copyright (c) 2016 Catalyst.net Ltd
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
#

"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
# File functions
from os import chmod
from os import path
import stat
# Regular expression functionality
import re

def get_build_var(name):
    """
    Get a build variable from the l3overlay Makefile build system.
    These will be placed in files, starting with '.', then the variable name.

    If the variables don't exist, return an empty string.
    """

    fn = path.join(here, ".%s" % name.strip())

    if path.exists(fn):
        with open(fn, encoding='UTF-8') as f:
            return f.read().strip()
    else:
        return ""

#
# Start the build process.
#

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='UTF-8') as f:
    long_description = f.read()

# Get l3overlay-specific build data.
sbin_dir = get_build_var("sbin_dir")
data_root = get_build_var("data_root")
with_init_d = get_build_var("with_init_d")
with_upstart = get_build_var("with_upstart")

data_files = [
    ("%s/etc/l3overlay" % data_root, ['global.conf']),
    ("%s/etc/l3overlay/overlays" % data_root, ['overlays/example.conf']),

    ("%s/etc/l3overlay/templates" % data_root, [
        'templates/bird.conf',
        'templates/ipsec.conf',
        'templates/ipsec.secrets',
    ]),
]

scripts = ['l3overlayd']

# Sanity check for Upstart config vs init.d script. These are mutually
# exclusive!
if with_upstart and with_init_d:
    raise Exception("can only define one of 'WITH_UPSTART' or 'WITH_INIT_D'")

# Generate the Upstart config file for l3overlayd, if Upstart is to be used.
# Add it to the list of data files to be installed.
if with_upstart:
    with open('upstart/l3overlay.conf.in', encoding='UTF-8') as f:
        with open('upstart/l3overlay.conf', mode='w', encoding='UTF-8') as g:
            g.write(re.sub("__L3OVERLAYD__", path.join(sbin_dir, scripts[0]), f.read()))

    data_files.append(("/etc/init", ['upstart/l3overlay.conf']))

# Generate the init.d script for l3overlayd, if init.d is to be used.
# Add it to the list of data files to be installed.
if with_init_d:
    with open('init.d/l3overlay.in', encoding='UTF-8') as f:
        with open('init.d/l3overlay', mode='w', encoding='UTF-8') as g:
            g.write(re.sub("__L3OVERLAYD__", path.join(sbin_dir, scripts[0]), f.read()))

    chmod(
        'init.d/l3overlay',
        stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH
    )

    data_files.append(("/etc/init.d", ['init.d/l3overlay']))

# Setup the package.
setup(
    name='l3overlay',

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version='1.0.0.dev1',

    description='IPsec overlay network manager',
    long_description=long_description,

    # The project's main homepage.
    url='https://github.com/catalyst/l3overlay',

    # Author details
    author='Callum Dickinson',
    author_email='callum.dickinson@catalyst.net.nz',

    # Choose your license
    license='GPLv3+',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: System Administrators',
        'Topic :: System :: Networking',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],

    # What does your project relate to?
    keywords='l3overlay ipsec bird routing namespace mesh network',

    # List run-time dependencies here.  These will be installed by pip when
    # your project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=['jinja2', 'pyroute2>=0.3.15.post15'],

    # Although 'package_data' is the preferred approach, in some case you may
    # need to place data files outside of your packages. See:
    # http://docs.python.org/3.4/distutils/setupscript.html#installing-additional-files # noqa
    # In this case, 'data_file' will be installed into '<sys.prefix>/my_data'
    data_files=data_files,

    # Install the l3overlayd executable file.
    scripts=scripts,
)
