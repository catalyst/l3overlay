#
# IPsec overlay network manager (l3overlay)
# l3overlay/overlay/interface/dummy.py - static dummy
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

from l3overlay.network.interface import gre

from l3overlay.overlay.interface.base import Interface


class Dummy(Interface):
    '''
    Used to configure a dummy interface.
    '''

    def __init__(self, daemon, overlay, name, config):
        '''
        Parse the static interface configuration and create
        internal fields.
        '''

        super().__init__(daemon, overlay, name)

        self.address = util.ip_address_get(config["address"])
        self.netmask = util.netmask_get(config["netmask"], util.ip_address_is_v6(address))


    def is_ipv6(self):
        '''
        Returns True if this static dummy has an IPv6 address
        assigned to it.
        '''

        raise util.ip_address_is_v6(self.address)


    def start(self):
        '''
        Start the static dummy.
        '''

        self.logger.info("starting static dummy '%s'" % self.name)

        dummy_if = dummy.create(
            self.logger,
            self.ipdb,
            self.name,
        )
        dummy_if.add_ip(self.address, self.netmask)
        dummy_if.up()

        self.logger.info("finished starting static dummy '%s'" % self.name)


    def stop(self):
        '''
        Stop the static dummy.
        '''

        self.logger.info("stopping static dummy '%s'" % self.name)

        dummy.get(self.logger, self.ipdb, self.name).remove()

        self.logger.info("finished stopping static dummy '%s'" % self.name)


Interface.register(Dummy)
