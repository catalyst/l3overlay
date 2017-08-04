#
# IPsec overlay network manager (l3overlay)
# l3overlay/l3overlayd/overlay/static_interface/mesh_tunnel.py - mesh tunnel interface
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
Mesh tunnel interface.
'''


from l3overlay import util

from l3overlay.l3overlayd.network.interface import bridge
from l3overlay.l3overlayd.network.interface import gre
from l3overlay.l3overlayd.network.interface import veth

from l3overlay.l3overlayd.overlay import active_interface

from l3overlay.l3overlayd.overlay.static_interface.base import StaticInterface


# pylint: disable=too-many-instance-attributes
class MeshTunnel(StaticInterface):
    '''
    Used to configure a mesh tunnel interface.
    '''

    # pylint: disable=too-many-arguments
    def __init__(self, logger, name,
                 node_local, node_remote,
                 physical_local, physical_remote,
                 virtual_local, virtual_remote):
        '''
        Set up mesh tunnel internal fields.
        '''

        super().__init__(logger, name)

        self.node_local = node_local
        self.node_remote = node_remote

        self.physical_local = physical_local
        self.physical_remote = physical_remote

        self.virtual_local = virtual_local
        self.virtual_remote = virtual_remote
        self.virtual_netmask = 127 if util.ip_address_is_v6(self.virtual_local) else 31

        # Initialised in setup().
        self.asn = None
        self.bridge_name = None
        self.root_veth_name = None
        self.netns_veth_name = None


    def setup(self, daemon, overlay):
        '''
        Set up mesh tunnel runtime state.
        '''

        super().setup(daemon, overlay)

        self.bridge_name = "%sbr" % self.name
        self.root_veth_name = "%sv0" % self.name
        self.netns_veth_name = "%sv1" % self.name

        self.asn = self.overlay.asn

        self.daemon.gre_key_add(self.physical_local, self.physical_remote, self.asn)
        self.daemon.mesh_link_add(self.physical_local, self.physical_remote)


    def start(self):
        '''
        Start the mesh tunnel.
        '''

        self.logger.info("starting mesh tunnel '%s'" % self.name)

        tunnel_if = gre.create(
            self.dry_run,
            self.logger,
            self.name,
            "gretap",
            self.physical_local,
            self.physical_remote,
            key=self.asn,
            root_ipdb=self.root_ipdb,
        )

        root_veth_if = veth.create(
            self.dry_run,
            self.logger,
            self.root_veth_name,
            self.netns_veth_name,
            root_ipdb=self.root_ipdb,
        )

        netns_veth_if = root_veth_if.peer_get(peer_netns=self.netns)
        netns_veth_if.netns_set(self.netns)

        bridge_if = bridge.create(
            self.dry_run,
            self.logger,
            self.bridge_name,
            root_ipdb=self.root_ipdb,
        )
        bridge_if.add_port(tunnel_if)
        bridge_if.add_port(root_veth_if)

        # Add an address to the network namespace veth interface, so it can
        # be addressed from either side of the mesh tunnel.
        netns_veth_if.add_ip(self.virtual_local, self.virtual_netmask)

        tunnel_if.up()
        root_veth_if.up()
        netns_veth_if.up()
        bridge_if.up()

        self.logger.info("finished starting mesh tunnel '%s'" % self.name)


    def stop(self):
        '''
        Stop the mesh tunnel.
        '''

        self.logger.info("stopping mesh tunnel '%s'" % self.name)

        bridge.get(self.dry_run, self.logger, self.bridge_name, root_ipdb=self.root_ipdb).remove()
        veth.get(
            self.dry_run,
            self.logger,
            self.root_veth_name,
            self.netns_veth_name,
            root_ipdb=self.root_ipdb,
        ).remove()
        gre.get(self.dry_run, self.logger, self.name, "gretap", root_ipdb=self.root_ipdb).remove()

        self.logger.info("finished stopping mesh tunnel '%s'" % self.name)


    def remove(self):
        '''
        Remove the mesh tunnel.
        '''

        self.daemon.gre_key_remove(self.physical_local, self.physical_remote, self.asn)
        self.daemon.mesh_link_remove(self.physical_local, self.physical_remote)


    def is_ipv6(self):
        '''
        Returns True if this mesh tunnel interface uses an IPv6
        virtual subnet.
        '''

        if self.virtual_netmask == 127:
            return True
        elif self.virtual_netmask == 31:
            return False
        else:
            raise RuntimeError("unexpected virtual netmask value '%s', expected 127 or 31" %
                               self.virtual_netmask)


    def active_interfaces(self):
        '''
        Return an iterable of ActiveInterface objects representing the
        physical interfaces this static interface uses.
        '''

        return (
            active_interface.create(self.logger, self.bridge_name, None),
            active_interface.create(self.logger, self.root_veth_name, None),
            active_interface.create(self.logger, self.name, None),
        )

StaticInterface.register(MeshTunnel)


# pylint: disable=too-many-arguments
def create(logger, name,
           node_local, node_remote,
           physical_local, physical_remote,
           virtual_local, virtual_remote):
    '''
    Create a mesh tunnel.
    '''

    return MeshTunnel(
        logger, name,
        node_local, node_remote,
        physical_local, physical_remote,
        virtual_local, virtual_remote,
    )
