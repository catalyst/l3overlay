#
# IPsec overlay network manager (l3overlay)
# l3overlay/overlay/interface/vlan.py - static vlan
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

from l3overlay.network import interface

from l3overlay.network.interface import bridge
from l3overlay.network.interface import veth
from l3overlay.network.interface import vlan

from l3overlay.overlay.interface import Interface


class VLAN(Interface):
    '''
    Used to configure a IEEE 802.1Q VLAN interface.
    '''

    def __init__(self, daemon, overlay, name, config):
        '''
        Parse the static interface configuration and create
        internal fields.
        '''

        super().__init__(daemon, overlay, name)

        self.id = util.integer_get(config["id"])
        self.physical_interface = util.name_get(config["physical-interface"])
        self.address = util.ip_address_get(config["address"])
        self.netmask = util.netmask_get(config[["netmask"], util.ip_address_is_v6(self.address))

        self.vlan_name = self.daemon.interface_name(name=name, suffix="vl", limit=12)
        self.root_veth_name = self.daemon.interface_name(name=self.vlan_name, suffix="v")
        self.netns_veth_name = self.daemon.interface_name(name=self.vlan_name, suffix="v")
        self.bridge_name = self.daemon.interface_name(name=self.vlan_name, suffix="br")


    def start(self):
        '''
        Start the static vlan.
        '''

        self.logger.info("starting static vlan '%s'" % self.name)

        # Find the physical interface.
        physical_if = interface.get(self.logger, self.daemon.root_ipdb, self.physical_interface)

        # Create the VLAN interface.
        vlan_if = vlan.create(self.logger, self.ipdb, self.vlan_name, physical_if, self.id)

        # Create the veth pair.
        root_veth_if = veth.create(
            self.logger,
            self.daemon.root_ipdb,
            self.root_veth_name,
            self.netns_veth_name,
        )

        # Move the netns veth interface to the network namespace.
        netns_veth_if = interface.netns_set(self.logger, self.ipdb, self.netns_veth_name, self.netns)

        # Add the assigned address for the VLAN to the netns veth
        # interface.
        netns_veth_if.add_ip(self.address, self.netmask)

        # Create a bridge for the physical interface to connect to the
        # network namespace via the veth pair.
        bridge_if = bridge.create(self.daemon.root_ipdb, self.bridge_name)

        # Add the physical interface and the root veth interface to the
        # bridge.
        bridge_if.add_port(vlan_if)
        bridge_if.add_port(root_veth_if)

        # Finally, we're done! Bring up the interfaces!
        physical_if.up()
        vlan_if.up()
        root_veth_if.up()
        netns_veth_if.up()
        bridge_if.up()

        self.logger.info("finished starting static vlan '%s'" % self.name)

        # Add the veth interface connected to the VLAN to the list of 
        # routed interfaces.
        # static_vlan = {
        #     'name': name,
        #     'interface': netns_veth_name,
        #     'vlan_interface': vlan_name,
        #     'root_interface': root_veth_name,
        #     'bridge_interface': bridge_name,
        # }

        # logging.debug("adding %s to list of static VLANs" % name)
        # self.static_vlans.append(static_vlan)

        # logging.debug("adding BGP route for static VLAN %s" % name)
        # if Util.ip_address_is_v6(address):
        #     self.bird6_config_add('vlans', [static_vlan])
        # else:
        #     self.bird_config_add('vlans', [static_vlan])



    def stop(self):
        '''
        Stop the static vlan.
        '''

        self.logger.info("stopping static vlan '%s'" % self.name)

        bridge.get(self.logger, self.daemon.root_ipdb, self.bridge_name).remove()
        veth.get(self.logger, self.ipdb, self.root_netns_name).remove()
        vlan.get(self.logger, self.ipdb, self.vlan_name).remove()

        self.logger.info("finished stopping static vlan '%s'" % self.name)


Interface.register(VLAN)
