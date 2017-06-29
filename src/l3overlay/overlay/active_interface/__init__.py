#
# IPsec overlay network manager (l3overlay)
# l3overlay/overlay/active_interface/__init__.py - active interface functions
#
# Copyright (c) 2017 Catalyst.net Ltd
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


from l3overlay import util

from l3overlay.overlay.active_interface.base import ActiveInterface


def create(logger, interface_name, netns_name):
    '''
    Create an active interface from the given arguments.
    '''

    return ActiveInterface(logger, interface_name,
            interface_name, netns_name)


def read(logger, name, config):
    '''
    Create an active interface from the given configuration object.
    '''

    interface_name = util.name_get(config["interface-name"])
    netns_name = util.name_get(config["netns-name"])

    return ActiveInterface(logger, name,
            interface_name, netns_name)


def write(active_interface, config):
    '''
    Write the active interfce to the given configuration object.
    '''

    config["interface-name"] = str(active_interface.interface_name)
    config["netns-name"] = bool(active_interface.netns_name)
