#
# IPsec overlay network manager (l3overlay)
# tests/base/overlay.py - base class for overlay-related unit tests
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


import copy

import l3overlay.overlay

from l3overlay import util

from tests.base import BaseTest


class OverlayBaseTest(object):
    class Class(BaseTest.Class):
        '''
        Base class for overlay-related unit tests.
        '''

        name = "test_overlay_base"


        #
        ##
        #


        def setUp(self):
            '''
            Set up the unit test runtime state.
            '''

            super().setUp()

            self.overlay_conf = {
                "overlay": {
                    "name": "test-overlay-base",
                    "enabled": False,
                    "asn": 65000,
                    "linknet-pool": "198.51.100.0/31",
                    "this-node": "test-1",
                    "node-0": "test-1 192.0.2.1",
                    "node-1": "test-2 192.0.2.2",
                },
            }


        #
        ##
        #

        def _overlay_conf_copy(self, section, key, value):
            '''
            Make a deep copy of the overlay configuration dictionary,
            update the copy's values, and return the copy.
            '''

            oc = copy.deepcopy(self.overlay_conf)

            if section:
                if section not in oc:
                    oc[section] = {}
                oc[section][key] = value
            elif key:
                if key not in oc:
                    oc[key] = {}
                oc[key] = value

            return oc


        def assert_success(self, section, key, value):
            '''
            Try and read an l3overlay daemon using the given arguments.
            Assumes it will succeed, and will run an assertion test to make
            sure a Daemon is returned.
            '''

            oc = self._overlay_conf_copy(section, key, value)

            overlay = l3overlay.overlay.read(
                self.global_conf["log"],
                self.global_conf["log_level"],
                config = oc,
            )
            self.assertIsInstance(overlay, l3overlay.overlay.Overlay)

            return overlay


        def assert_fail(self, section, key, value, *exceptions):
            '''
            Try and read an l3overlay daemon using the given arguments.
            Assumes it will fail, and raises a RuntimeError if it doesn't.
            '''

            try:
                oc = self._overlay_conf_copy(section, key, value)

                l3overlay.overlay.read(
                    self.global_conf["log"],
                    self.global_conf["log_level"],
                    config = oc,
                )
                raise RuntimeError('''l3overlay.overlay.read unexpectedly returned successfully
    Expected exception types: %s
    Arguments: %s''' % (str.join(", ", (e.__name__ for e in exceptions)), oc))
            except exceptions:
                pass
