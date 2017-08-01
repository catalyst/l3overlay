#
# IPsec overlay network manager (l3overlay)
# tests/test_static_tunnel.py - unit test for reading static tunnel interfaces
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

from tests.overlay.static_interface.base import StaticInterfaceBaseTest


class StaticTunnelTest(StaticInterfaceBaseTest.Class):
    '''
    Unit test for reading static tunnel interfaces.
    '''

    name = "test_static_tunnel"

    #
    ##
    #


    def setUp(self):
        '''
        Set up the unit test runtime state.
        '''

        super().setUp()

        self.overlay_conf[self.section] = {
            "mode": "gre",
            "local": "198.18.0.0",
            "remote": "198.18.0.1",
            "address": "201.0.113.1",
            "netmask": "32",
        }


    #
    ##
    #


    def test_mode(self):
        '''
        Test that 'mode' is properly handled by the static tunnel interface.
        '''

        self.assert_enum(self.section, "mode", enum=["gre", "gretap"])


    def test_local(self):
        '''
        Test that 'local' is properly handled by the static tunnel interface.
        '''

        self.assert_ip_address(self.section, "local")


    def test_remote(self):
        '''
        Test that 'remote' is properly handled by the static tunnel interface.
        '''

        self.assert_ip_address(self.section, "remote")


    def test_address_netmask(self):
        '''
        Test that 'address' and 'netmask' are properly handled by the static tunnel interface.
        '''

        self.assert_address_netmask(self.section, "address", "netmask")


    def test_key(self):
        '''
        Test that 'key' is properly handled by the static tunnel interface.
        '''

        self.assert_integer(self.section, "key", minval=0)


    def test_ikey(self):
        '''
        Test that 'ikey' is properly handled by the static tunnel interface.
        '''

        # Fail when okey is undefined.
        self.assert_fail(self.section, "ikey", value="0", exception=overlay.interface.ReadError)

        # Success when okey is defined at the same time.
        # Also test argument handling at the same time.
        oc = self.config_get(self.section, "okey", value="0")
        self.assert_integer(self.section, "ikey", minval=0, conf=oc)


    def test_okey(self):
        '''
        Test that 'okey' is properly handled by the static tunnel interface.
        '''

        # Fail when ikey is undefined.
        self.assert_fail(self.section, "okey", value="0", exception=overlay.interface.ReadError)

        # Success when ikey is defined at the same time.
        # Also test argument handling at the same time.
        oc = self.config_get(self.section, "ikey", value="0")
        self.assert_integer(self.section, "okey", minval=0, conf=oc)


if __name__ == "__main__":
    unittest.main()
