#
# IPsec overlay network manager (l3overlay)
# l3overlay/l3overlayd/overlay/static_interface/vlan.py - static vlan
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

from l3overlay.l3overlayd.network import interface

from l3overlay.l3overlayd.network.interface import bridge
from l3overlay.l3overlayd.network.interface import veth
from l3overlay.l3overlayd.network.interface import vlan

from l3overlay.l3overlayd.overlay import active_interface

from l3overlay.l3overlayd.overlay.static_interface.base import StaticInterface


class VLAN(StaticInterface):
    '''
    Used to configure a IEEE 802.1Q VLAN interface.
    '''

    def __init__(self, logger, name,
                id, physical_interface, address, netmask):
        '''
        Set up static vlan internal fields.
        '''

        super().__init__(logger, name)

        self.id = id
        self.physical_interface = physical_interface
        self.address = address
        self.netmask = netmask


    def setup(self, daemon, overlay):
        '''
        Set up static vlan runtime state.
        '''

        super().setup(daemon, overlay)

        self.vlan_name = self.daemon.interface_name(self.name, suffix="vl", limit=12)
        self.root_veth_name = self.daemon.interface_name(self.vlan_name, suffix="v")
        self.netns_veth_name = self.daemon.interface_name(self.vlan_name, suffix="v")
        self.bridge_name = self.daemon.interface_name(self.vlan_name, suffix="br")


    def start(self):
        '''
        Start the static vlan.
        '''

        self.logger.info("starting static vlan '%s'" % self.name)

        # Find the physical interface.
        physical_if = interface.get(
            self.dry_run,
            self.logger,
            self.physical_interface,
            root_ipdb = self.root_ipdb,
        )

        # Create the VLAN interface.
        vlan_if = vlan.create(
            self.dry_run,
            self.logger,
            self.vlan_name,
            physical_if, 
            self.id,
            root_ipdb = self.root_ipdb,
        )

        # Create the veth pair.
        root_veth_if = veth.create(
            self.dry_run,
            self.logger,
            self.root_veth_name,
            self.netns_veth_name,
            root_ipdb = self.root_ipdb,
        )

        # Move the netns veth interface to the network namespace.
        netns_veth_if = root_veth_if.peer_get(peer_netns=self.netns)
        netns_veth_if.netns_set(self.netns)

        # Add the assigned address for the VLAN to the netns veth
        # interface.
        netns_veth_if.add_ip(self.address, self.netmask)

        # Create a bridge for the physical interface to connect to the
        # network namespace via the veth pair.
        bridge_if = bridge.create(
            self.dry_run,
            self.logger,
            self.bridge_name,
            root_ipdb = self.root_ipdb,
        )

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


    def stop(self):
        '''
        Stop the static vlan.
        '''

        self.logger.info("stopping static vlan '%s'" % self.name)

        bridge.get(self.dry_run, self.logger, self.bridge_name, root_ipdb=self.root_ipdb).remove()
        veth.get(
            self.dry_run,
            self.logger,
            self.root_veth_name,
            self.netns_veth_name,
            root_ipdb = self.root_ipdb,
        ).remove()
        vlan.get(self.dry_run, self.logger, self.vlan_name, root_ipdb=self.root_ipdb).remove()

        self.logger.info("finished stopping static vlan '%s'" % self.name)


    def is_ipv6(self):
        '''
        Returns True if this static vlan has an IPv6 address
        assigned to it.
        '''

        return util.ip_address_is_v6(self.address)


    def active_interfaces(self):
        '''
        Return an iterable of ActiveInterface objects representing the
        physical interfaces this static interface uses.
        '''

        return (
            active_interface.create(self.logger, self.bridge_name, None),
            active_interface.create(self.logger, self.root_veth_name, None),
            active_interface.create(self.logger, self.vlan_name, None),
        )

StaticInterface.register(VLAN)


def read(logger, name, config):
    '''
    Create a static vlan from the given configuration object.
    '''

    id = util.integer_get(config["id"], minval=0, maxval=4096)
    physical_interface = util.name_get(config["physical-interface"])
    address = util.ip_address_get(config["address"])
    netmask = util.netmask_get(config["netmask"], util.ip_address_is_v6(address))

    return VLAN(logger, name,
            id, physical_interface, address, netmask)


def write(vlan, config):
    '''
    Write the static vlan to the given configuration object.
    '''

    config["id"] = str(vlan.id)
    config["physical-interface"] = vlan.physical_interface
    config["address"] = str(vlan.address)
    config["netmask"] = str(vlan.netmask)
