#
# IPsec overlay network manager (l3overlay)
# l3overlay/l3overlayd/overlay/static_interface/overlay_link.py - static overlay link
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
Overlay link overlay static interface.
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
class OverlayLink(StaticInterface):
    '''
    Used to configure a fully addressed and linked
    point-to-point connection between two overlays.
    '''

    # pylint: disable=too-many-arguments
    def __init__(self, logger, name,
                 outer_address, inner_address, inner_overlay_name, netmask):
        '''
        Set up static overlay link internal state.
        '''

        super().__init__(logger, name)

        self.outer_address = outer_address
        self.inner_address = inner_address
        self.inner_overlay_name = inner_overlay_name
        self.netmask = netmask

        # Initialised in setup().
        self.outer_overlay_name = None
        self.outer_asn = None
        self.inner_overlay = None
        self.inner_netns = None
        self.inner_asn = None
        self.dummy_name = None
        self.bridge_name = None
        self.outer_name = None
        self.inner_name = None


    def setup(self, daemon, overlay):
        '''
        Set up overlay link runtime state.
        '''

        super().setup(daemon, overlay)

        self.outer_overlay_name = overlay.name
        self.outer_asn = overlay.asn

        self.inner_overlay = self.daemon.overlays[self.inner_overlay_name]
        self.inner_netns = netns.get(self.dry_run, self.logger, self.inner_overlay_name)
        self.inner_asn = self.inner_overlay.asn

        self.dummy_name = self.daemon.interface_name(self.name, limit=13)
        self.bridge_name = self.daemon.interface_name(self.dummy_name, suffix="br")
        self.outer_name = self.daemon.interface_name(self.dummy_name, suffix="v")
        self.inner_name = self.daemon.interface_name(self.dummy_name, suffix="v")


    def is_ipv6(self):
        '''
        Returns True if this static overlay link uses an IPv6
        point-to-point subnet.
        '''

        return util.ip_address_is_v6(self.outer_address)


    def start(self):
        '''
        Start the static overlay link.
        '''

        self.logger.info("starting static overlay link '%s'" % self.name)

        # Start the network namespace object for the linked overlay.
        self.inner_netns.start()

        # Create the inner and outer veth interfaces, which link the
        # overlays together. At the same time, move the inner veth
        # interface to the inner overlay.
        outer_if = veth.create(
            self.dry_run,
            self.logger,
            self.outer_name,
            self.inner_name,
            netns=self.netns,
        )

        inner_if = outer_if.peer_get(peer_netns=self.inner_netns)
        inner_if.netns_set(self.inner_netns)

        # Create a dummy interface for the outer veth interface to be
        # bridged with.
        dummy_if = dummy.create(
            self.dry_run,
            self.logger,
            self.dummy_name,
            netns=self.netns,
        )

        # Create the bridge interface for the dummy interface and the
        # veth pair interface, and add the bridge ports.
        bridge_if = bridge.create(
            self.dry_run,
            self.logger,
            self.bridge_name,
            netns=self.netns,
        )
        bridge_if.add_port(outer_if)
        bridge_if.add_port(dummy_if)

        # Assign address to the interfaces.
        bridge_if.add_ip(self.outer_address, self.netmask)
        inner_if.add_ip(self.inner_address, self.netmask)

        # Bring up both the inner and outer interfaces, and their
        # linking interfaces.
        outer_if.up()
        inner_if.up()
        dummy_if.up()
        bridge_if.up()

        # Stop the network namespace object for the linked overlay,
        # to remove its process from memory.
        self.inner_netns.stop()

        self.logger.info("finished starting static overlay link '%s'" % self.name)


    def stop(self):
        '''
        Stop the static overlay link.
        '''

        self.logger.info("stopping static overlay link '%s'" % self.name)

        self.inner_netns.start()

        bridge.get(self.dry_run, self.logger, self.bridge_name, netns=self.netns).remove()
        dummy.get(self.dry_run, self.logger, self.dummy_name, netns=self.netns).remove()
        veth.get(
            self.dry_run,
            self.logger,
            self.outer_name,
            self.inner_name,
            netns=self.netns,
        ).remove()

        self.inner_netns.stop()

        self.logger.info("finished stopping static overlay link '%s'" % self.name)


    def active_interfaces(self):
        '''
        Return an iterable of ActiveInterface objects representing the
        physical interfaces this static interface uses.
        '''

        return (
            active_interface.create(self.logger, self.bridge_name, self.inner_netns.name),
            active_interface.create(self.logger, self.dummy_name, self.inner_netns.name),
            active_interface.create(self.logger, self.outer_name, self.inner_netns.name),
        )

StaticInterface.register(OverlayLink)


def read(logger, name, config):
    '''
    Create a static overlay link from the given configuration object.
    '''

    outer_address = util.ip_address_get(config["outer-address"])
    inner_address = util.ip_address_get(config["inner-address"])
    inner_overlay_name = util.name_get(config["inner-overlay-name"])
    netmask = util.netmask_get(config["netmask"], util.ip_address_is_v6(inner_address))

    if not isinstance(inner_address, type(outer_address)):
        raise ReadError(
            "inner address '%s' (%s) and outer address '%s' (%s) "
            "must be the same type of IP address" %
            (
                inner_address, str(type(inner_address)),
                outer_address, str(type(outer_address)),
            ),
        )

    return OverlayLink(
        logger, name,
        outer_address, inner_address, inner_overlay_name, netmask,
    )


def write(overlay_link, config):
    '''
    Write the static overlay link to the given configuration object.
    '''

    config["outer-address"] = str(overlay_link.outer_address)
    config["inner-address"] = str(overlay_link.inner_address)
    config["inner-overlay-name"] = overlay_link.inner_overlay_name
    config["netmask"] = str(overlay_link.netmask)
