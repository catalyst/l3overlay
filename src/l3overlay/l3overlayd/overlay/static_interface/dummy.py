#
# IPsec overlay network manager (l3overlay)
# l3overlay/l3overlayd/overlay/static_interface/dummy.py - static dummy
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

from l3overlay.l3overlayd.network.interface import dummy

from l3overlay.l3overlayd.overlay import active_interface

from l3overlay.l3overlayd.overlay.static_interface.base import StaticInterface


class Dummy(StaticInterface):
    '''
    Used to configure a dummy interface.
    '''

    def __init__(self, logger, name,
            address, netmask):
        '''
        Set up static dummy fields.
        '''

        super().__init__(logger, name)

        self.address = address
        self.netmask = netmask


    def setup(self, daemon, overlay):
        '''
        Set up static dummy internal state.
        '''

        super().setup(daemon, overlay)

        self.dummy_name = self.daemon.interface_name(self.name)


    def start(self):
        '''
        Start the static dummy.
        '''

        self.logger.info("starting static dummy '%s'" % self.name)

        dummy_if = dummy.create(
            self.dry_run,
            self.logger,
            self.dummy_name,
            netns = self.netns,
        )
        dummy_if.add_ip(self.address, self.netmask)
        dummy_if.up()

        self.logger.info("finished starting static dummy '%s'" % self.name)


    def stop(self):
        '''
        Stop the static dummy.
        '''

        self.logger.info("stopping static dummy '%s'" % self.name)

        dummy.get(self.dry_run, self.logger, self.dummy_name, netns=self.netns).remove()

        self.logger.info("finished stopping static dummy '%s'" % self.name)


    def is_ipv6(self):
        '''
        Returns True if this static dummy has an IPv6 address
        assigned to it.
        '''

        return util.ip_address_is_v6(self.address)


    def active_interfaces(self):
        '''
        Return an iterable of ActiveInterface objects representing the
        physical interfaces this static interface uses.
        '''

        return (active_interface.create(self.logger, self.dummy_name, self.netns.name),)

StaticInterface.register(Dummy)


def read(logger, name, config):
    '''
    Create a static dummy from the given configuration object.
    '''

    address = util.ip_address_get(config["address"])
    netmask = util.netmask_get(config["netmask"], util.ip_address_is_v6(address))

    return Dummy(logger, name,
            address, netmask)


def write(dummy, config):
    '''
    Write the static dummy to the given configuration object.
    '''

    config["address"] = str(dummy.address)
    config["netmask"] = str(dummy.netmask)
