#
# IPsec overlay network manager (l3overlay)
# tests/l3overlayd/overlay/static_interface/__init__.py - base class for static interface unit tests
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


'''
Base class for static interface unit tests.
'''


import os
import unittest

from l3overlay import util

from l3overlay.l3overlayd import overlay

from tests.l3overlayd.overlay import OverlayBaseTest


class StaticInterfaceBaseTest(OverlayBaseTest):
    '''
    Base class for static interface-related unit tests.
    '''

    name = "test_static_interface"
    conf_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), name)


    #
    ##
    #


    def setUp(self):
        '''
        Set up the unit test runtime state.
        '''

        super().setUp()

        if self.name == "test_static_interface":
            raise unittest.SkipTest("cannot run base class as a test case")

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
        over = self.config_get(section, netmask_key, value="32")
        self.assert_ip_address(section, address_key, conf=over)

        # Test the netmask key.
        over = self.config_get(section, address_key, value="201.0.113.1")
        self.assert_netmask(section, netmask_key, is_ipv6=False, conf=over)

        over = self.config_get(section, address_key, value="2001:db8::1")
        self.assert_netmask(section, netmask_key, is_ipv6=True, conf=over)


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
        obj = self.object_get()
        self.assertTrue(
            next((si for si in obj.static_interfaces if si.name == self.section_name), None),
        )

        # Test invalid values.
        over = self.config_get()
        value = over[self.section].copy()
        del over[self.section]

        self.assert_fail(
            "%s:%s" % (self.section_type, self.section_name.replace("-", " ")),
            value=value,
            exception=util.GetError,
            conf=over,
        )
        self.assert_fail(
            "%s:%s" % (util.random_string(16), self.section_name),
            value=value,
            exception=overlay.UnsupportedSectionTypeError,
            conf=over,
        )
