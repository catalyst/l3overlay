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

from tests.overlay.base import OverlayBaseTest


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
            self.section = util.section_header(self.section_type, self.section_name)

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
            oc = self.config_get(section, netmask_key, value="32")
            self.assert_ip_address(section, address_key, conf=oc)

            # Test the netmask key.
            oc = self.config_get(section, address_key, value="201.0.113.1")
            self.assert_netmask(section, netmask_key, is_ipv6=False, conf=oc)

            oc = self.config_get(section, address_key, value="2001:db8::1")
            self.assert_netmask(section, netmask_key, is_ipv6=True, conf=oc)


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
            o = self.object_get()
            self.assertTrue(next((si for si in o.static_interfaces if si.name == self.section_name), None))

            # Test invalid values.
            oc = self.config_get()
            value = oc[self.section].copy()
            del oc[self.section]

            self.assert_fail(
                "%s:%s" % (self.section_type, self.section_name.replace("-", " ")),
                value=value,
                exception=util.GetError,
                conf=oc,
            )
            self.assert_fail(
                "%s:%s" % (util.random_string(16), self.section_name),
                value=value,
                exception=overlay.UnsupportedSectionTypeError,
                conf=oc,
            )
