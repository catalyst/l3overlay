#
# IPsec overlay network manager (l3overlay)
# tests/test_static_bgp.py - unit test for reading static bgp protocols
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


class StaticBGPTest(StaticInterfaceBaseTest.Class):
    '''
    Unit test for reading static bgp protocols.
    '''

    name = "test_static_bgp"

    #
    ##
    #


    def setUp(self):
        '''
        Set up the unit test runtime state.
        '''

        super().setUp()

        self.overlay_conf[self.section] = {
            "neighbor": "201.0.113.1",
        }


    #
    ##
    #


    def test_neighbor(self):
        '''
        Test that 'neighbor' is properly handled by the static bgp protocol.
        '''

        self.assert_ip_address(self.section, "neighbor")


    def test_local(self):
        '''
        Test that 'local' is properly handled by the static bgp protocol.
        '''

        self.assert_ip_address(self.section, "local")


    def test_local_asn(self):
        '''
        Test that 'local-asn' is properly handled by the static bgp protocol.
        '''

        self.assert_integer(self.section, "local-asn", minval=0, maxval=65535)


    def test_neighbor_asn(self):
        '''
        Test that 'neighbor-asn' is properly handled by the static bgp protocol.
        '''

        self.assert_integer(self.section, "neighbor-asn", minval=0, maxval=65535)


    def test_bfd(self):
        '''
        Test that 'bfd' is properly handled by the static bgp protocol.
        '''

        self.assert_boolean(self.section, "bfd", test_default=True)


    def test_ttl_security(self):
        '''
        Test that 'ttl-security' is properly handled by the static bgp protocol.
        '''

        self.assert_boolean(self.section, "ttl-security", test_default=True)


    def test_description(self):
        '''
        Test that 'description' is properly handled by the static bgp protocol.
        '''

        self.assert_success(self.section, "description", value="test description for static BGP")


    def test_import_prefix(self):
        '''
        Test that 'import-prefix' is properly handled by the static bgp protocol.
        '''

        # Test invalid values.
        self.assert_fail(self.section, "import-prefix", value="172.16.0.0/-1", exception=util.GetError)
        self.assert_fail(self.section, "import-prefix", value="172.16.0.0/33", exception=util.GetError)
        self.assert_fail(self.section, "import-prefix", value="2001:db8::/129", exception=util.GetError)
        self.assert_fail(self.section, "import-prefix", value="172.16.0.0/16{-1,33}", exception=util.GetError)
        self.assert_fail(self.section, "import-prefix", value="2001:db8::/32{-1,129}", exception=util.GetError)

        # Test valid values.
        self.assert_success(self.section, "import-prefix", value="172.16.0.0/16")
        self.assert_success(self.section, "import-prefix", value="172.16.0.0/16+")
        self.assert_success(self.section, "import-prefix", value="172.16.0.0/16-")
        self.assert_success(self.section, "import-prefix", value="172.16.0.0/16{20,24}")

        self.assert_success(self.section, "import-prefix", value="2001:db8::/32")
        self.assert_success(self.section, "import-prefix", value="2001:db8::/32+")
        self.assert_success(self.section, "import-prefix", value="2001:db8::/32-")
        self.assert_success(self.section, "import-prefix", value="2001:db8::/32{48,64}")

        oc = self.config_get(self.section, "import-prefix-0", value="172.16.0.0/24")
        self.assert_success(self.section, "import-prefix-1", value="172.16.1.0/24", conf=oc)


if __name__ == "__main__":
    unittest.main()
