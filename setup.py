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

# A setuptools based setup module.
# See:
# https://packaging.python.org/en/latest/distributing.html
# https://github.com/pypa/sampleproject


import codecs
import os
import setuptools
import stat
import re


here = os.path.abspath(os.path.dirname(__file__))


def config_read(config_file):
    '''
    Read variables from the given file into a dictionary, and return it.
    '''

    config = {}

    with codecs.open(config_file, encoding="UTF-8") as f:
        for line in f:
            match = re.match("^([_A-Za-z][_A-Za-z0-9]*)\s*=\s*(.*)$", line)

            if match:
                key = match.group(1)
                value = match.group(2)

                config[key] = value

    return config


def var_replace(template, output, config, keys):
    '''
    Replace values in a template file according to the dictionary
    of variables, and write the result to the output file.
    '''

    with codecs.open(template, mode="r", encoding="UTF-8") as f:
        with codecs.open(output, mode="w", encoding="UTF-8") as g:
            text = f.read()

            for k in keys:
                key = k.upper()
                text = re.sub("__%s__" % key, config[key], text)

            g.write(text)


# Get the long description from the README file.
with codecs.open(os.path.join(here, "README.md"), encoding="UTF-8") as f:
    long_description = f.read()


# Read the build system configuration.
config = config_read(os.path.join(here, ".config"))

prefix = config["PREFIX"]
sbin_dir = config["SBIN_DIR"]
config_dir = config["CONFIG_DIR"]

with_init_d  = config["WITH_INIT_D"] if "WITH_INIT_D" in config else None
with_upstart = config["WITH_UPSTART"] if "WITH_UPSTART" in config else None

l3overlayd = os.path.join(sbin_dir, "l3overlayd")


# Sanity check for Upstart config vs init.d script. These are mutually exclusive!
if with_upstart and with_init_d:
    raise RuntimeError("can only define one of 'WITH_UPSTART' or 'WITH_INIT_D'")


# Build data files from templates.
if with_upstart:
    var_replace(
        os.path.join(here, "upstart", "l3overlay.conf.in"),
        os.path.join(here, "upstart", "l3overlay.conf"),
        {"L3OVERLAYD": l3overlayd}, ["L3OVERLAYD"],
    )

if with_init_d:
    var_replace(
        os.path.join(here, "init.d", "l3overlay.in"),
        os.path.join(here, "init.d", "l3overlay"),
        {"L3OVERLAYD": l3overlayd}, ["L3OVERLAYD"],
    )

if with_upstart or with_init_d:
    var_replace(
        os.path.join(here, "default", "l3overlay.in"),
        os.path.join(here, "default", "l3overlay"),
        config, ["CONFIG_DIR"],
    )


# Set permissions.
if with_init_d:
    os.chmod(
        os.path.join(here, "init.d", "l3overlay"),
        stat.S_IRUSR|stat.S_IWUSR|stat.S_IXUSR|stat.S_IRGRP|stat.S_IXGRP|stat.S_IROTH|stat.S_IXOTH,
    )


# Map files to installation locations.
data_files = [
    (
        config_dir,
        [
            os.path.join(here, "l3overlay", "global.conf"),
        ],
    ),

    (
        os.path.join(config_dir, "overlays"),
        [
            os.path.join(here, "l3overlay", "overlays", "example.conf"),
        ],
    ),

    (
        os.path.join(config_dir, "templates"),
        [
            os.path.join(here, "l3overlay", "templates", "bird.conf"),
            os.path.join(here, "l3overlay", "templates", "ipsec.conf"),
            os.path.join(here, "l3overlay", "templates", "ipsec.secrets"),
        ],
    ),
]

if with_upstart:
    data_files.append((os.path.join("/", "etc", "init"), [os.path.join(here, "upstart", "l3overlay.conf")]))

if with_init_d:
    data_files.append((os.path.join("/", "etc", "init.d"), [os.path.join(here, "init.d", "l3overlay")]))

if with_upstart or with_init_d:
    data_files.append((os.path.join("/", "etc", "default"), [os.path.join(here, "default", "l3overlay")]))


# Setup the package.
setuptools.setup(
    name = "l3overlay",

    description = "IPsec overlay network manager",
    long_description = long_description,

    version = "1.0.0",

    url = "https://github.com/catalyst/l3overlay",

    author = "Callum Dickinson",
    author_email = "callum.dickinson@catalyst.net.nz",

    license = "GPLv3+",

    classifiers = [
        "Development Status :: 5 - Production/Stable",

        "Intended Audience :: System Administrators",
        "Topic :: System :: Networking",

        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",

        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
    ],

    keywords = "l3overlay ipsec bird routing namespace mesh network",

    install_requires = ["jinja2", "pyroute2>=0.4.6"],

    data_files = data_files,

    packages = setuptools.find_packages(where=os.path.join(here, "src")),
    package_dir = {"": "src"},

    entry_points = {
        "console_scripts": ["l3overlayd = l3overlay:main"],
    },
)
