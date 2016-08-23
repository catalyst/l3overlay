#
# IPsec overlay network manager (l3overlay)
# l3overlay/tests/test_daemon.py - unit test for testing daemon
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


import argparse
import os
import tempfile
import tests
import unittest

from l3overlay import util

import l3overlay.daemon


class DaemonTest(unittest.TestCase):
    '''
    l3overlay unit test for testing static interfaces.
    '''

    def setUp(self):
        '''
        Set up the unit test runtime state.
        '''

        self.global_conf = tests.global_conf_get("test_l3overlayd")

        self.args_base = {
            "dry_run": True,

            "lib_dir": self.global_conf["lib_dir"],

            "overlay_conf_dir": self.global_conf["overlay_conf_dir"],
            "template_dir": self.global_conf["template_dir"],

            "log": None,
        }


    def tearDown(self):
        '''
        Clean up the unit test runtime state.
        '''

        tests.global_conf_cleanup(self.global_conf)


    #
    ## TODO: implement assert_<type> in base test class.
    #


    def assert_boolean(self, key):
        '''
        Test that key, of type boolean, is properly handled by the daemon.
        '''

        # Test default values.

        # Test valid values.
        self.assert_success({key: True})
        self.assert_success({key: "true"})
        self.assert_success({key: 1})
        self.assert_success({key: 2})

        self.assert_success({key: False})
        self.assert_success({key: "false"})
        self.assert_success({key: 0})
        self.assert_success({key: -1})

        # Test invalid values.
        self.assert_fail({key: ""}, ValueError)
        self.assert_fail({key: "foo"}, ValueError)


    def assert_hex_string(self, key, min=None, max=None):
        '''
        Test that key, of type hex string, is properly handled by the daemon.
        Optionally checks if digit limits are properly handled, by specifying
        a miniumum and maximum digit size.
        '''

        valid_values = "0123456789abcdef"

        _min = min if min is not None else 1
        _max = max if max is not None else max(_min + 1, 16)

        # Test default values.

        # Test valid values.
        for v in valid_values:
            self.assert_success({key: str.join("", [v for __ in range(0, _min)])})

        self.assert_success({
            key: str.join("", [valid_values[i % 16] for i in range(0, _max)]),
        })

        # Test invalid values.
        self.assert_fail({key: ""}, ValueError)

        self.assert_fail({
            key: str.join("", ["z" for __ in range(0, _min)]),
        }, ValueError)

        if min is not None and _min > 1:
            self.assert_fail({
                key: str.join("", [valid_values[i % 16] for i in range(0, _min - 1)]),
            }, ValueError)

        if max is not None and _max > 1:
            self.assert_fail({
                key: str.join("", [valid_values[i % 16] for i in range(0, _max + 1)]),
            }, ValueError)


    def assert_enum(self, enum, key, *invalid_value):
        '''
        Test that key, of type enum, is properly handled by the daemon.
        '''

        # Test default values.

        # Test valid values.
        for e in enum:
            self.assert_success({key: e.upper()})
            self.assert_success({key: e.lower()})

        # Test invalid values.
        self.assert_fail({key: ""}, ValueError)
        self.assert_fail({key: 1}, ValueError)

        for iv in invalid_value:
            self.assert_fail({key: iv}, ValueError)


    #
    ##
    #


    def assert_fail(self, args, *exceptions):
        '''
        Try and read an l3overlay daemon using the given arguments.
        Assumes it will fail, and raises a RuntimeError if it doesn't.
        '''

        a = self.args_base.copy()
        a.update(args)

        try:
            l3overlay.daemon.read(a)
            raise RuntimeError('''l3overlay.daemon.read unexpectedly returned successfully
Expected exception types: %s
Arguments: %s''' % (str.join(", ", (e.__name__ for e in exceptions)), a))
        except exceptions:
            pass


    def assert_success(self, args):
        '''
        Try and read an l3overlay daemon using the given arguments.
        Assumes it will succeed, and will run an assertion test to make
        sure a Daemon is returned.
        '''

        a = self.args_base.copy()
        a.update(args)

        self.assertIsInstance(l3overlay.daemon.read(a), l3overlay.daemon.Daemon)


    #
    ##
    #


    def test_log_level(self):
        '''
        Test that 'log_level' is properly handled by the daemon.
        '''

        self.assert_enum(
            ["NOTSET", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            "log_level",
            "FOO",
        )


    def test_use_ipsec(self):
        '''
        Test that 'use_ipsec' is properly handled by the daemon.
        '''

        self.assert_boolean("use_ipsec")


    def test_ipsec_manage(self):
        '''
        Test that 'ipsec_manage' is properly handled by the daemon.
        '''

        self.assert_boolean("ipsec_manage")


    def test_ipsec_psk(self):
        '''
        Test that 'ipsec_psk' is properly handled by the daemon.
        '''

        self.assert_hex_string("ipsec_psk", min=6, max=64)


if __name__ == "__main__":
    unittest.main()
