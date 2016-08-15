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

from l3overlay.overlay.interface import bgp
from l3overlay.overlay.interface import dummy
from l3overlay.overlay.interface import overlay_link
from l3overlay.overlay.interface import tunnel
from l3overlay.overlay.interface import tuntap
from l3overlay.overlay.interface import veth
from l3overlay.overlay.interface import vlan


def read(daemon, overlay, section, config):
    '''
    '''

    interface_type, name = util.section_split(section)

    if interface_type == "static-bgp":
        return bgp.read(daemon, overlay, name, config)
    elif interface_type == "static-dummy":
        return dummy.read(daemon, overlay, name, config)
    elif interface_type == "static-overlay-link":
        return overlay_link.read(daemon, overlay, name, config)
    elif interface_type == "static-tunnel":
        return tunnel.read(daemon, overlay, name, config)
    elif interface_type == "static-tuntap":
        return tuntap.read(daemon, overlay, name, config)
    elif interface_type == "static-veth":
        return veth.read(daemon, overlay, name, config)
    elif interface_type == "static-vlan":
        return vlan.read(daemon, overlay, name, config)
    elif name.startswith("static"):
        raise RuntimeError("unsupported static interface type '%s' with name '%s'" % (interface_type, name))
    else:
        raise RuntimeError("unknown section type: %s" % section)
