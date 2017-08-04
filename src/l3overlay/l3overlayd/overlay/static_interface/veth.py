#
# IPsec overlay network manager (l3overlay)
# l3overlay/l3overlayd/overlay/static_interface/veth.py - static veth
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
veth pair overlay static interface.
'''


from l3overlay import util

from l3overlay.l3overlayd.network import netns

from l3overlay.l3overlayd.network.interface import bridge
from l3overlay.l3overlayd.network.interface import dummy
from l3overlay.l3overlayd.network.interface import veth

from l3overlay.l3overlayd.overlay import active_interface

from l3overlay.l3overlayd.overlay.interface import ReadError

from l3overlay.l3overlayd.overlay.static_interface.base import StaticInterface


# pylint: disable=too-many-instance-attributes
class VETH(StaticInterface):
    '''
    Used to configure a veth pair interface.
    '''

    # pylint: disable=too-many-arguments
    def __init__(self, logger, name,
                 inner_address, outer_address, inner_namespace, outer_interface_bridged, netmask):
        '''
        Set up static veth internal fields.
        '''

        super().__init__(logger, name)

        self.inner_address = inner_address
        self.outer_address = outer_address
        self.inner_namespace = inner_namespace
        self.outer_interface_bridged = outer_interface_bridged
        self.netmask = netmask

        # Initialised in setup().
        self.dummy_name = None
        self.bridge_name = None
        self.inner_name = None
        self.outer_name = None
        self.outer_netns = None
        self.inner_netns = None


    def setup(self, daemon, overlay):
        '''
        Set up static veth runtime state.
        '''

        super().setup(daemon, overlay)

        self.dummy_name = self.daemon.interface_name(self.name, limit=12)
        self.bridge_name = self.daemon.interface_name(self.dummy_name, suffix="br")
        self.inner_name = self.daemon.interface_name(self.dummy_name, suffix="v")
        self.outer_name = self.daemon.interface_name(self.dummy_name, suffix="v")

        # Get the outer interface network namespace.
        self.outer_netns = self.overlay.netns

        # Get the inner interface network namespace, if inner-namespace is set.
        # Otherwise, use the root namespace.
        if self.inner_namespace:
            self.logger.debug("setting inner namespace to network namespace '%s'" %
                              self.inner_namespace)
            self.inner_netns = netns.get(self.dry_run, self.logger, self.inner_namespace)
        else:
            self.logger.debug("setting inner namespace to root namespace")
            self.inner_netns = None


    def start(self):
        '''
        Start the static overlay link.
        '''

        self.logger.info("starting static veth '%s'" % self.name)

        if self.inner_namespace:
            self.inner_netns.start()

        inner_if = veth.create(
            self.dry_run,
            self.logger,
            self.inner_name,
            self.outer_name,
            netns=self.inner_netns if self.inner_namespace else None,
            root_ipdb=self.root_ipdb if not self.inner_namespace else None,
        )

        outer_if = inner_if.peer_get(peer_netns=self.outer_netns)
        outer_if.netns_set(self.outer_netns)

        self.logger.debug("setting inner veth interface '%s' as the inner address interface" %
                          self.inner_name)
        inner_address_if = inner_if

        if self.outer_interface_bridged:
            dummy_if = dummy.create(
                self.dry_run,
                self.logger,
                self.dummy_name,
                netns=self.outer_netns,
            )

            bridge_if = bridge.create(
                self.dry_run,
                self.logger,
                self.bridge_name,
                netns=self.outer_netns,
            )
            bridge_if.add_port(outer_if)
            bridge_if.add_port(dummy_if)

            self.logger.debug("setting bridge interface '%s' as the outer address interface" %
                              self.bridge_name)
            outer_address_if = bridge_if
        else:
            self.logger.debug("setting outer veth interface '%s' as the outer address interface" %
                              self.outer_name)
            outer_address_if = outer_if

        if self.inner_address:
            inner_address_if.add_ip(self.inner_address, self.netmask)

        if self.outer_address:
            outer_address_if.add_ip(self.outer_address, self.netmask)

        outer_if.up()
        inner_if.up()

        if self.outer_interface_bridged:
            dummy_if.up()
            bridge_if.up()

        if self.inner_namespace:
            self.inner_netns.stop()

        self.logger.info("finished starting static veth '%s'" % self.name)


    def stop(self):
        '''
        Stop the static veth.
        '''

        self.logger.info("stopping static veth '%s'" % self.name)

        if self.inner_namespace:
            self.inner_netns.start()

        if self.outer_interface_bridged:
            bridge.get(
                self.dry_run,
                self.logger,
                self.bridge_name,
                netns=self.outer_netns,
            ).remove()

            dummy.get(
                self.dry_run,
                self.logger,
                self.dummy_name,
                netns=self.outer_netns,
            ).remove()

        veth.get(
            self.dry_run,
            self.logger,
            self.inner_name,
            self.outer_name,
            netns=self.inner_netns if self.inner_namespace else None,
            root_ipdb=self.root_ipdb if not self.inner_namespace else None,
        ).remove()

        if self.inner_namespace:
            self.inner_netns.stop()

        self.logger.info("finished stopping static veth '%s'" % self.name)


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

        return False


    def active_interfaces(self):
        '''
        Return an iterable of ActiveInterface objects representing the
        physical interfaces this static interface uses.
        '''

        active_interfaces = [
            active_interface.create(
                self.logger,
                self.inner_name,
                self.inner_netns.name if self.inner_namespace else None,
            ),
        ]

        if self.outer_interface_bridged:
            active_interfaces.extend([
                active_interface.create(self.logger, self.bridge_name, self.outer_netns.name),
                active_interface.create(self.logger, self.dummy_name, self.outer_netns.name),
            ])

        return tuple(active_interfaces)

StaticInterface.register(VETH)


def read(logger, name, config):
    '''
    Create a static veth from the given configuration object.
    '''

    # pylint: disable=too-many-branches

    if "inner-address" in config:
        inner_address = util.ip_address_get(config["inner-address"])
    else:
        inner_address = None
    if "outer-address" in config:
        outer_address = util.ip_address_get(config["outer-address"])
    else:
        outer_address = None
    if "inner-namespace" in config:
        inner_namespace = util.name_get(config["inner-namespace"])
    else:
        inner_namespace = None
    if "outer-interface-bridged" in config:
        outer_interface_bridged = util.boolean_get(config["outer-interface-bridged"])
    else:
        outer_interface_bridged = False

    netmask = None
    if outer_address:
        netmask = util.netmask_get(config["netmask"], util.ip_address_is_v6(outer_address))
    elif inner_address:
        netmask = util.netmask_get(config["netmask"], util.ip_address_is_v6(inner_address))

    if inner_address is not None and outer_address is not None:
        if not outer_interface_bridged:
            raise ReadError(
                "inner-address and outer-address can only be defined at the same time "
                "if outer-interface-bridged is true",
            )

        if not isinstance(inner_address, type(outer_address)):
            raise ReadError(
                "inner-address '%s' (%s) and outer-address '%s' (%s) "
                "must be the same type of IP address" %
                (
                    str(inner_address), str(type(inner_address)),
                    str(outer_address), str(type(outer_address)),
                ),
            )

    return VETH(
        logger, name,
        inner_address, outer_address, inner_namespace, outer_interface_bridged, netmask,
    )


def write(vet, config):
    '''
    Write the static veth to the given configuration object.
    '''

    if vet.inner_address:
        config["inner-address"] = str(vet.inner_address)
    if vet.outer_address:
        config["outer-address"] = str(vet.outer_address)
    if vet.inner_namespace:
        config["inner-namespace"] = vet.inner_namespace
    config["outer-interface-bridged"] = str(vet.outer_interface_bridged).lower()
    if vet.netmask:
        config["netmask"] = str(vet.netmask)
