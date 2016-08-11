#
# IPsec overlay network manager (l3overlay)
# l3overlay/overlay/interface/__init__.py - static interface abstract base class
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


import abc

from l3overlay import util

from l3overlay.overlay.interface.dummy import Dummy
from l3overlay.overlay.interface.overlay_link import OverlayLink
from l3overlay.overlay.interface.tunnel import Tunnel
from l3overlay.overlay.interface.tuntap import Tuntap
from l3overlay.overlay.interface.veth import VETH
from l3overlay.overlay.interface.vlan import VLAN


class Interface(metaclass=abc.ABCMeta):
    '''
    Abstract base class for an overlay static interface.
    '''

    def __init__(self, daemon, overlay, name=None):
        '''
        Set internal fields for the static interface to use.
        '''

        self.daemon = daemon
        self.logger = self.daemon.logger
        self.root_ipdb = self.daemon.root_ipdb

        self.overlay = overlay
        self.netns = self.overlay.netns
        self.ipdb = self.netns.ipdb

        self.name = name


    @abc.abstractmethod
    def is_ipv6(self):
        '''
        Returns True if this static interface has an IPv6 address
        assigned to it.
        '''

        raise NotImplementedError()


    @abc.abstractmethod
    def start(self):
        '''
        Required method to start a static interface.
        '''

        return


    @abc.abstractmethod
    def stop(self):
        '''
        Required method to stop a static interface.
        '''

        return


    def remove(self):
        '''
        Optional method to clean up a static interface runtime state.
        '''

        return


def read(daemon, overlay, section, config):
    '''
    '''

    interface_type, name = util.section_split(section)

    if interface_type == "static-dummy":
        return Dummy(daemon, overlay, name, config)
    elif interface_type == "static-overlay-link":
        return OverlayLink(daemon, overlay, name, config)
    elif interface_type == "static-tunnel":
        return Tunnel(daemon, overlay, name, config)
    elif interface_type == "static-tuntap":
        return Tuntap(daemon, overlay, name, config)
    elif interface_type == "static-veth":
        return VETH(daemon, overlay, name, config)
    elif interface_type == "static-vlan":
        return VLAN(daemon, overlay, name, config)
    elif name.startswith("static"):
        raise RuntimeError("unsupported static interface type '%s' with name '%s'" % (interface_type, name))
    else:
        raise RuntimeError("unknown section type: %s" % section)
