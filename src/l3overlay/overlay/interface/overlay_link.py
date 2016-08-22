#
# IPsec overlay network manager (l3overlay)
# l3overlay/interface/overlay_link.py - static overlay link
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
from l3overlay.network.interface import dummy
from l3overlay.network.interface import veth

from l3overlay.overlay.interface.base import Interface
from l3overlay.overlay.interface.base import ReadError


class OverlayLink(Interface):
    '''
    Used to configure a fully addressed and linked
    point-to-point connection between two overlays.
    '''

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


    def setup(self, daemon, overlay):
        '''
        Set up overlay link runtime state.
        '''

        super().setup(daemon, overlay)

        self.outer_overlay_name = overlay.name
        self.outer_asn = overlay.asn

        self.inner_overlay = self.daemon.overlays[self.inner_overlay_name]
        self.inner_netns = self.inner_overlay.netns
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

        # Create the inner and outer veth interfaces, which link the
        # overlays together. At the same time, move the inner veth
        # interface to the inner overlay.
        outer_if = veth.create(
            self.dry_run,
            self.logger,
            self.netns.ipdb,
            self.outer_name,
            self.inner_name,
        )

        inner_if = interface.netns_set(
            self.dry_run,
            self.logger,
            self.netns.ipdb,
            self.inner_name,
            self.inner_netns,
        )

        # Create a dummy interface for the outer veth interface to be
        # bridged with.
        dummy_if = dummy.create(
            self.dry_run,
            self.logger,
            self.netns.ipdb,
            self.dummy_name,
        )

        # Create the bridge interface for the dummy interface and the
        # veth pair interface, and add the bridge ports.
        bridge_if = bridge.create(
            self.dry_run,
            self.logger,
            self.netns.ipdb,
            self.bridge_name,
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

        self.logger.info("finished starting static overlay link '%s'" % self.name)


    def stop(self):
        '''
        Stop the static overlay link.
        '''

        self.logger.info("stopping static overlay link '%s'" % self.name)

        bridge.get(self.dry_run, self.logger, self.netns.ipdb, self.bridge_name).remove()
        dummy.get(self.dry_run, self.logger, self.netns.ipdb, self.dummy_name).remove()
        veth.get(self.dry_run, self.logger, self.netns.ipdb, self.outer_name).remove()

        self.logger.info("finished stopping static overlay link '%s'" % self.name)

Interface.register(OverlayLink)


def read(logger, name, config):
    '''
    Create a static overlay link from the given configuration object.
    '''

    outer_address = util.ip_address_get(config["outer-address"])
    inner_address = util.ip_address_get(config["inner-address"])
    inner_overlay_name = util.name_get(config["inner-overlay-name"])
    netmask = util.netmask_get(config["netmask"], util.ip_address_is_v6(inner_address))

    if (type(inner_address) != type(outer_address)):
        raise ReadError("inner address '%s' (%s) and outer address '%s' (%s) must be the same type of IP address" %
                (inner_address, str(type(nner_address)),
                    outer_address, str(type(outer_address))))

    return OverlayLink(logger, name,
            outer_address, inner_address, inner_overlay_name, netmask)


def write(overlay_link, config):
    '''
    Write the static overlay link to the given configuration object.
    '''

    config["outer-address"] = str(overlay_link.outer_address)
    config["inner-address"] = str(overlay_link.inner_address)
    config["inner-overlay-name"] = overlay_link.inner_overlay_name
    config["netmask"] = str(overlay_link.netmask)
