#
# IPsec overlay network manager (l3overlay)
# l3overlay/l3overlayd/overlay/static_interface/tuntap.py - static tuntap
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

from l3overlay.l3overlayd.network.interface import tuntap

from l3overlay.l3overlayd.overlay import active_interface

from l3overlay.l3overlayd.overlay.static_interface.base import StaticInterface


class Tuntap(StaticInterface):
    '''
    Used to configure a TUN/TAP interface.
    '''

    def __init__(self, logger, name,
            mode, address, netmask, uid, gid):
        '''
        Set up static tuntap internal state.
        '''

        super().__init__(logger, name)

        self.mode = mode
        self.address = address
        self.netmask = netmask
        self.uid = uid
        self.gid = gid


    def setup(self, daemon, overlay):
        '''
        Set up static tuntap runtime state.
        '''

        super().setup(daemon, overlay)

        self.tuntap_name = self.daemon.interface_name(self.name)


    def start(self):
        '''
        Start the static tuntap.
        '''

        self.logger.info("starting static tuntap '%s'" % self.name)

        tuntap_if = tuntap.create(
            self.dry_run,
            self.logger,
            self.tuntap_name,
            self.mode,
            self.uid,
            self.gid,
            netns = self.netns,
        )
        tuntap_if.add_ip(self.address, self.netmask)
        tuntap_if.up()

        self.logger.info("finished starting static tuntap '%s'" % self.name)


    def stop(self):
        '''
        Stop the static tuntap.
        '''

        self.logger.info("stopping static tuntap '%s'" % self.name)

        tuntap.get(self.dry_run, self.logger, self.tuntap_name, self.mode, netns=self.netns).remove()

        self.logger.info("finished stopping static tuntap '%s'" % self.name)


    def is_ipv6(self):
        '''
        Returns True if this static tuntap has an IPv6 address
        assigned to it.
        '''

        return util.ip_address_is_v6(self.address)


    def active_interfaces(self):
        '''
        Return an iterable of ActiveInterface objects representing the
        physical interfaces this static interface uses.
        '''

        return (active_interface.create(self.logger, self.tuntap_name, self.netns.name),)

StaticInterface.register(Tuntap)


def read(logger, name, config):
    '''
    Create a static tuntap from the given configuration object.
    '''

    mode = util.enum_get(config["mode"], ["tun", "tap"])
    address = util.ip_address_get(config["address"])
    netmask = util.netmask_get(config["netmask"], util.ip_address_is_v6(address))
    uid = util.integer_get(config["uid"], minval=0) if "uid" in config else None
    gid = util.integer_get(config["gid"], minval=0) if "gid" in config else None

    return Tuntap(logger, name,
            mode, address, netmask, uid, gid)


def write(tuntap, config):
    '''
    Write the static tuntap to the given configuration object.
    '''

    config["mode"] = tuntap.mode.lower()
    config["address"] = str(tuntap.address)
    config["netmask"] = str(tuntap.netmask)
    if tuntap.uid:
        config["uid"] = str(tuntap.uid)
    if tuntap.gid:
        config["gid"] = str(tuntap.gid)
