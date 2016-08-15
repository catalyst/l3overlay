#
# IPsec overlay network manager (l3overlay)
# l3overlay/overlay/interface/tuntap.py - static tuntap
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

from l3overlay.network.interface import tuntap

from l3overlay.overlay.interface.base import Interface


class Tuntap(Interface):
    '''
    Used to configure a TUN/TAP interface.
    '''

    def __init__(self, daemon, overlay, name,
            mode, uid, gid, address, netmask):
        '''
        Set up static tuntap internal state.
        '''

        super().__init__(daemon, overlay, name)

        self.mode = mode
        self.uid = uid
        self.gid = gid
        self.address = address
        self.netmask = netmask

        self.tuntap_name = self.daemon.interface_name(self.name)


    def is_ipv6(self):
        '''
        Returns True if this static tuntap has an IPv6 address
        assigned to it.
        '''

        raise util.ip_address_is_v6(self.address)


    def start(self):
        '''
        Start the static tuntap.
        '''

        self.logger.info("starting static tuntap '%s'" % self.name)

        tuntap_if = tuntap.create(
            self.logger,
            self.netns.ipdb,
            self.tuntap_name,
            self.mode,
            self.uid,
            self.gid,
        )
        tuntap_if.add_ip(self.address, self.netmask)
        tuntap_if.up()

        self.logger.info("finished starting static tuntap '%s'" % self.name)


    def stop(self):
        '''
        Stop the static tuntap.
        '''

        self.logger.info("stopping static tuntap '%s'" % self.name)

        tuntap.get(self.logger, self.netns.ipdb, self.tuntap_name).remove()

        self.logger.info("finished stopping static tuntap '%s'" % self.name)

Interface.register(Tuntap)


def read(daemon, overlay, name, config):
    '''
    Create a static tuntap from the given configuration object.
    '''

    mode = util.enum_get(config["mode"], ["tun", "tap"])
    uid = util.integer_get(config["uid"])
    gid = util.integer_get(config["gid"])
    address = util.ip_address_get(config["address"])
    netmask = util.netmask_get(config["netmask"], util.ip_address_is_v6(address))

    return Tuntap(daemon, overlay, name,
            mode, uid, gid, address, netmask)


def write(tuntap, config):
    '''
    Write the static tuntap to the given configuration object.
    '''

    config["mode"] = tuntap.mode.lower()
    config["uid"] = str(tuntap.uid)
    config["gid"] = str(tuntap.gid)
    config["address"] = str(tuntap.address)
    config["netmask"] = str(tuntap.netmask)
