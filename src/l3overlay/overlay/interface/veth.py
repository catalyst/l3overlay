#
# IPsec overlay network manager (l3overlay)
# l3overlay/interface/veth.py - static veth
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

from l3overlay.network import netns
from l3overlay.network import interface

from l3overlay.network.interface import bridge
from l3overlay.network.interface import dummy
from l3overlay.network.interface import veth

from l3overlay.overlay.interface import Interface


class VETH(Interface):
    '''
    Used to configure a veth pair interface.
    '''

    def __init__(self, daemon, overlay, name, config):
        '''
        Parse the static interface configuration and create
        internal fields.
        '''

        super().__init__(daemon, overlay, name)

        self.inner_address = util.ip_address_get(config["inner-address"]) if "inner-address" in config else None
        self.outer_address = util.ip_address_get(config["outer-address"]) if "outer-address" in config else None
        self.inner_namespace = util.name_get(config["inner-namespace"]) if "outer-namespace" in config else None
        self.outer_interface_bridged = util.boolean_get(config["outer-interface-bridged"]) if "outer-interface-bridged" in config else False

        if self.inner_address:
            use_ipv6 = util.ip_address_is_v6(inner_address)
        elif self.outer_address:
            use_ipv6 = util.ip_address_is_v6(outer_address)

        self.netmask = util.netmask_get(config["netmask"], use_ipv6)

        if self.inner_address and self.outer_address:
            if type(self.inner_address) != type(self.outer_address):
                raise ValueError("inner-address '%s' (%s) and outer-address '%s' (%s) must be the same type of IP address" % (str(self.inner_address), str(type(self.inner_address)), str(self.outer_address), str(type(self.outer_address))))

        self.dummy_name = self.daemon.interface_name(self.name, limit=12)
        self.bridge_name = self.daemon.interface_name(self.dummy_name, suffix="br")
        self.inner_name = self.daemon.interface_name(self.dummy_name, suffix="v")
        self.outer_name = self.daemon.interface_name(self.dummy_name, suffix="v")

        # Get the outer interface network namespace.
        self.outer_netns = self.overlay.netns
        self.outer_ipdb = self.outer_netns.ipdb

        # Get the inner interface network namespace.
        # More complicated than it really should be.
        inner_overlay = None
        inner_netns = None
        inner_ipdb = None

        if self.inner_namespace:
            try:
                self.inner_netns = self.daemon.overlays[self.inner_namespace].netns
                self.logger.debug("setting inner namespace to overlay '%s'" % self.inner_namespace)
            except ValueError:
                self.logger.debug("setting inner namespace to network namespace '%s'" % self.inner_namespace)
                self.inner_netns = netns.get(inner_namespace)
                self.inner_netns.start()
                self.inner_ipdb = self.inner_netns.ipdb
        else:
            self.logger.debug("setting inner namespace to root namespace")
            inner_ipdb = self.daemon.root_ipdb


    def is_ipv6(self):
        '''
        Returns True if this static veth uses an IPv6
        point-to-point subnet. Returns False if no addresses
        are assigned.
        '''

        if self.outer_address:
            return util.ip_address_is_v6(self.outer_address)
        elif self.inner_address:
            return util.ip_address_is_v6(self.inner_address)
        else:
            return False


    def start(self):
        '''
        Start the static overlay link.
        '''

        self.logger.info("starting static veth '%s'" % self.name)

        # Create the inner veth interface in the inner namespace,
        # and move the outer veth interface into the overlay namespace.
        inner_if = veth.create(self.logger, self.inner_ipdb, self.inner_name, self.outer_name)
        outer_if = interface.netns_set(self.logger, self.inner_ipdb, self.outer_name, outer_netns)

        # Set the interface to assign the inner address.
        inner_address_if = inner_if

        # Set the interface to assign the outer address.
        #
        # If the outer veth interface is to be bridged to a dummy
        # interface, do so, and make sure the outeraddress gets
        # assigned to the bridge instead.
        if self.outer_interface_bridged:
            dummy_if = dummy.create(self.logger, self.outer_ipdb, self.dummy_name)
            bridge_if = bridge.create(self.logger, self.outer_ipdb, self.bridge_name)

            bridge_if.add_port(outer_if)
            bridge_if.add_port(dummy_if)

            self.logger.debug("setting bridge interface '%s' as the outer address interface" % self.bridge_name)
            outer_address_if = bridge_if
        else:
            self.logger.debug("setting outer veth interface '%s' as the outer address interface" % self.outer_name)
            outer_address_if = outer_if

        # Assign IP addresses to the interfaces, if configured.
        if self.inner_address:
            inner_address_if.add_ip(self.inner_address, self.netmask)

        if self.outer_address:
            outer_address_if.add_ip(self.outer_address, self.netmask)

        # Bring up all interfaces.
        outer_if.up()
        inner_if.up()

        if outer_interface_bridged:
            dummy_if.up()
            bridge_if.up()

        self.logger.info("finished starting static veth '%s'" % self.name)

                # Add the interfaces to the list of routed interfaces.
                #static_veth = {
                #    'name': name,
                #    'inner_interface': inner_name,
                #    'outer_interface': outer_name,
                #    'inner_address_interface': inner_address_name,
                #}

                #if inner_interface_bridged:
                #    static_veth['dummy_interface'] = dummy_name
                #    static_veth['bridge_interface'] = bridge_name

                #if outer_namespace:
                #    static_veth['outer_namespace'] = outer_namespace

                #logging.debug("adding %s to list of static veths" % name)
                #self.static_veths.append(static_veth)

                #logging.debug("adding BGP route for static veth %s" % name)
                #if use_ipv6:
                #    self.bird6_config_add('veths', [static_veth])
                #else:
                #    self.bird_config_add('veths', [static_veth])


    def stop(self):
        '''
        Stop the static veth.
        '''

        self.logger.info("stopping static veth '%s'" % self.name)

        if self.outer_interface_bridged:
            bridge.get(self.logger, self.outer_ipdb, self.bridge_name).remove()
            vlan.get(self.logger, self.outer_ipdb, self.dummy_name).remove()

        veth.get(self.logger, self.inner_ipdb, self.inner_name).remove()

        self.logger.info("finished stopping static veth '%s'" % self.name)


    def remove(self):
        '''
        Clean up the static veth runtime state.
        '''

        if self.inner_namespace and not self.inner_overlay:
             self.inner_netns.stop()
             self.inner_netns.remove()


Interface.register(VETH)
