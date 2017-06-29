#
# IPsec overlay network manager (l3overlay)
# tests/base/static_interface.py - base class for static interface-related unit tests
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

from l3overlay import overlay
from l3overlay import util

from tests.base.overlay import OverlayBaseTest


class StaticInterfaceBaseTest(object):
    class Class(OverlayBaseTest.Class):
        '''
        Base class for static interface-related unit tests.
        '''

        name = "test_static_interface"

        #
        ##
        #


        def setUp(self):
            '''
            Set up the unit test runtime state.
            '''

            super().setUp()

            self.section_name = self.name.replace("_", "-")
            self.section_type = self.section_name.replace("test-", "")
            self.section = "%s:%s" % (self.section_type, self.section_name)

            self.overlay_conf["overlay"]["name"] = self.section_name
            self.overlay_conf[self.section] = {}

        #
        ##
        #


        def assert_address_netmask(self, section, address_key, netmask_key):
            '''
            Test that an address and netmask pair, dependent on each other,
            is properly handled by the static interface.
            '''

            # Test the IP address key.
            self.overlay_conf[section][netmask_key] = "32"
            self.assert_ip_address(section, address_key)

            # Test the netmask key.
            self.overlay_conf[section][address_key] = "201.0.113.1"
            self.assert_netmask(section, netmask_key, is_ipv6=False)

            self.overlay_conf[section][address_key] = "2001:db8::1" 
            self.assert_netmask(section, netmask_key, is_ipv6=True)


        #
        ##
        #


        def test_name(self):
            '''
            Test that the static interface section name is properly parsed by
            the overlay.
            '''

            # Test that the static interface is parsed successfully with a valid
            # name, and is available.
            overlay = self.assert_success(None, None, None)
            self.assertTrue(next((si for si in overlay.static_interfaces if si.name == self.section_name), None))

            # Test the same section, with a section name containing spaces.
            # Make sure it fails.
            value = self.overlay_conf[self.section].copy()
            del self.overlay_conf[self.section]

            self.assert_fail(
                None,
                "%s:%s" % (self.section_type, self.section_name.replace("-", " ")),
                value,
                util.GetError,
            )
