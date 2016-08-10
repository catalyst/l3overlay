#
# IPsec overlay network manager (l3overlay)
# l3overlay/util/__init__.py - utility functions
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


import os
import jinja2

import distutils.spawn


#
## Command functions.
#

def command_path(command, not_found_ok=False):
    '''
    '''

    path = distutils.spawn.find_executable(command)

    if not not_found_ok and not path:
        raise RuntimeError("cannot find '%s' executable path" % command)

    return path


#
## Template functions.
#

def template_read(dir, file):
    '''
    '''

    return jinja2.Environment(trim_blocks=True,loader=FileSystemLoader(dir)).get_template(file)
