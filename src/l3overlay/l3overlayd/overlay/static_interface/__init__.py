#
# IPsec overlay network manager (l3overlay)
# l3overlay/l3overlayd/overlay/static_interface/__init__.py - static interface functions
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


'''
Static interface functions.
'''


from l3overlay import util

from l3overlay.l3overlayd.overlay.interface import ReadError
from l3overlay.l3overlayd.overlay.interface import WriteError

from l3overlay.l3overlayd.overlay.static_interface import bgp
from l3overlay.l3overlayd.overlay.static_interface import dummy
from l3overlay.l3overlayd.overlay.static_interface import external_tunnel
from l3overlay.l3overlayd.overlay.static_interface import overlay_link
from l3overlay.l3overlayd.overlay.static_interface import tunnel
from l3overlay.l3overlayd.overlay.static_interface import tuntap
from l3overlay.l3overlayd.overlay.static_interface import veth
from l3overlay.l3overlayd.overlay.static_interface import vlan


def read(logger, interface_type, name, config):
    '''
    Read an interface from the given configuration object.
    '''

    # pylint: disable=too-many-return-statements

    if interface_type == "static-bgp":
        return bgp.read(logger, name, config)
    elif interface_type == "static-dummy":
        return dummy.read(logger, name, config)
    elif interface_type == "static-external-tunnel":
        return external_tunnel.read(logger, name, config)
    elif interface_type == "static-overlay-link":
        return overlay_link.read(logger, name, config)
    elif interface_type == "static-tunnel":
        return tunnel.read(logger, name, config)
    elif interface_type == "static-tuntap":
        return tuntap.read(logger, name, config)
    elif interface_type == "static-veth":
        return veth.read(logger, name, config)
    elif interface_type == "static-vlan":
        return vlan.read(logger, name, config)
    else:
        raise ReadError("unsupported static interface type '%s' with name '%s'" %
                        (interface_type, name))


def write(interface, config):
    '''
    Write an interface to the given configuration object.
    '''

    section = None
    interface_class = None

    if isinstance(interface, bgp.BGP):
        section = util.section_header("static-bgp", interface.name)
        interface_class = bgp
    elif isinstance(interface, dummy.Dummy):
        section = util.section_header("static-dummy", interface.name)
        interface_class = dummy
    elif isinstance(interface, external_tunnel.ExternalTunnel):
        section = util.section_header("static-external-tunnel", interface.name)
        interface_class = external_tunnel
    elif isinstance(interface, overlay_link.OverlayLink):
        section = util.section_header("static-overlay-link", interface.name)
        interface_class = overlay_link
    elif isinstance(interface, tunnel.Tunnel):
        section = util.section_header("static-tunnel", interface.name)
        interface_class = tunnel
    elif isinstance(interface, tuntap.Tuntap):
        section = util.section_header("static-tuntap", interface.name)
        interface_class = tuntap
    elif isinstance(interface, veth.VETH):
        section = util.section_header("static-veth", interface.name)
        interface_class = veth
    elif isinstance(interface, vlan.VLAN):
        section = util.section_header("static-vlan", interface.name)
        interface_class = vlan
    else:
        raise WriteError("unsupported interface type '%s'" % str(type(interface)))

    config[section] = {}
    interface_class.write(interface, config[section])
