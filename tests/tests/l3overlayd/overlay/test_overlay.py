#
# IPsec overlay network manager (l3overlay)
# tests/l3overlayd/overlay/test_overlay.py - unit test for reading Overlay objects
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


import ipaddress
import os
import unittest

from l3overlay import util

from l3overlay.l3overlayd import overlay

from tests.l3overlayd.overlay.base import OverlayBaseTest


class OverlayTest(OverlayBaseTest.Class):
    '''
    l3overlay unit test for reading Overlay objects.
    '''

    name = "test_overlay"


    #
    ##
    #


    def setUp(self):
        '''
        Set up the unit test runtime state.
        '''

        super().setUp()

        self.global_conf["fwbuilder_script_dir"] = os.path.join(
            self.tmp_dir,
            "fwbuilder-scripts",
        )

        self.overlay_conf["overlay"]["name"] = "test-overlay"


    #
    ##
    #


    def test_name(self):
        '''
        Test that 'name' is properly handled by the overlay.
        '''

        self.assert_name("overlay", "name")


    def test_asn(self):
        '''
        Test that 'asn' is properly handled by the overlay.
        '''

        self.assert_integer("overlay", "asn", minval=0, maxval=65535)


    def test_linknet_pool(self):
        '''
        Test that 'linknet-pool' is properly handled by the overlay.
        '''

        self.assert_ip_network("overlay", "linknet-pool")


    def test_this_node(self):
        '''
        Test that 'this-node' is properly handled by the overlay.
        '''

        this_node = self.overlay_conf["overlay"]["this-node"]
        self.assert_success(
            "overlay",
            "this-node",
            value=this_node,
            expected_value=(
                this_node,
                ipaddress.ip_address(next(
                    (
                        v for k, v in self.overlay_conf["overlay"].items() if
                                k.startswith("node-") and v.startswith(this_node)
                    ),
                ).split(" ")[1]),
            )
        )

        self.assert_fail(
            "overlay",
            "this-node",
            value=util.random_string(6),
            exception=overlay.MissingThisNodeError,
        )


    def test_fwbuilder_script(self):
        '''
        Test that 'linknet-pool' is properly handled by the overlay.
        '''

        self.assert_value(
            "overlay",
            "fwbuilder-script",
            value="test_fwbuilder_script.conf",
        )

        self.assert_value(
            "overlay",
            "fwbuilder-script",
            value=os.path.join(
                self.global_conf["fwbuilder_script_dir"],
                "test_fwbuilder_script.conf",
            ),
        )


    def test_node(self):
        '''
        Test that 'node-*' is properly handled by the overlay.
        '''

        ## Test valid values.
        oc = self.config_get()
        for key in oc["overlay"].copy():
            if key.startswith("node-"):
                del oc["overlay"][key]

        # Add the node which corresponds to 'this-node'.
        oc["overlay"]["node-1"] = "%s 192.0.2.1" % self.overlay_conf["overlay"]["this-node"]
        self.assert_success(conf=oc)

        # Add a second (separate) test node.
        self.assert_success(
            "overlay",
            "node-2",
            value="test-overlay-2 192.0.2.2",
            conf=oc,
        )

        ## Test invalid values.
        oc = self.config_get()
        for key in oc["overlay"].copy():
            if key.startswith("node-"):
                del oc["overlay"][key]

        # Test that no nodes causes it to fail.
        self.assert_fail(exception=overlay.NoNodeListError, conf=oc)

        # Add invalid data to the list.
        self.assert_fail("overlay", "node-1", value=1, exception=util.GetError)
        self.assert_fail(
            "overlay",
            "node-1",
            value="%s 192.0.2.1 fail" % self.overlay_conf["overlay"]["this-node"],
            exception=util.GetError,
            conf=oc,
        )

        # Test that 'this-node' is missing, by having a single-node list
        # that does not contain 'this-node'.
        self.assert_fail(
            "overlay",
            "node-1",
            value="%s 192.0.2.1" % util.random_string(6),
            exception=overlay.MissingThisNodeError,
            conf=oc,
        )


    def test_section(self):
        '''
        Test that unsupported section types are properly handled by the overlay.
        '''

        self.assert_fail(
            util.random_string(8),
            value={util.random_string(4): util.random_string(16)},
            exception=overlay.UnsupportedSectionTypeError,
        )


if __name__ == "__main__":
    unittest.main()
