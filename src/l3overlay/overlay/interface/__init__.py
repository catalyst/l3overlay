#
# IPsec overlay network manager (l3overlay)
# l3overlay/overlay/interface/__init__.py - static interface functions
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


from l3overlay import util

from l3overlay.overlay.interface.dummy import Dummy
from l3overlay.overlay.interface.overlay_link import OverlayLink
from l3overlay.overlay.interface.tunnel import Tunnel
from l3overlay.overlay.interface.tuntap import Tuntap
from l3overlay.overlay.interface.veth import VETH
from l3overlay.overlay.interface.vlan import VLAN


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
