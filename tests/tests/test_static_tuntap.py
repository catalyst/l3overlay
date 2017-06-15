#
# IPsec overlay network manager (l3overlay)
# tests/test_static_tuntap.py - unit test for reading static tuntap interfaces
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


import os
import unittest

from l3overlay import overlay
from l3overlay import util

from tests.base.static_interface import StaticInterfaceBaseTest


class StaticTuntapTest(StaticInterfaceBaseTest.Class):
    '''
    Unit test for reading static tuntap interfaces.
    '''

    name = "test_static_tuntap"

    #
    ##
    #


    def setUp(self):
        '''
        Set up the unit test runtime state.
        '''

        super().setUp()

        self.overlay_conf[self.section] = {
            "mode": "tun",
            "address": "201.0.113.1",
            "netmask": "32",
        }


    #
    ##
    #


    def test_mode(self):
        '''
        Test that 'mode' is properly handled by the static tuntap interface.
        '''

        self.assert_enum(self.section, "mode", ["tun", "tap"])


    def test_address_netmask(self):
        '''
        Test that 'address' and 'netmask' are properly handled by the static tuntap interface.
        '''

        self.assert_address_netmask(self.section, "address", "netmask")


    def test_uid(self):
        '''
        Test that 'uid' is properly handled by the static tuntap interface.
        '''

        self.assert_integer(self.section, "uid", minval=0)


    def test_gid(self):
        '''
        Test that 'gid' is properly handled by the static tuntap interface.
        '''

        self.assert_integer(self.section, "gid", minval=0)


if __name__ == "__main__":
    unittest.main()
