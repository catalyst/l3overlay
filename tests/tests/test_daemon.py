#
# IPsec overlay network manager (l3overlay)
# tests/test_daemon.py - unit test for reading Daemon objects
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


import os
import unittest

from l3overlay import util

import l3overlay.daemon

from tests.base import BaseTest


class DaemonTest(BaseTest.Class):
    '''
    l3overlay unit test for reading Daemon objects.
    '''

    name = "test_daemon"


    #
    ##
    #


    def value_get(self, daemon, section, key):
        '''
        Get the value from the given section and key on the daemon.
        '''

        return vars(daemon)[section][key] if section else vars(daemon)[key]


    def assert_success(self, section, key, value):
        '''
        Try and read an l3overlay daemon using the given arguments.
        Assumes it will succeed, and will run an assertion test to make
        sure a Daemon is returned.
        '''

        gc = self.global_conf.copy()
        gc[key] = value

        daemon = l3overlay.daemon.read(gc)
        self.assertIsInstance(daemon, l3overlay.daemon.Daemon)

        return daemon


    def assert_fail(self, section, key, value, *exceptions):
        '''
        Try and read an l3overlay daemon using the given arguments.
        Assumes it will fail, and raises a RuntimeError if it doesn't.
        '''

        gc = self.global_conf.copy()
        gc[key] = value

        try:
            l3overlay.daemon.read(gc)
            raise RuntimeError('''l3overlay.daemon.read unexpectedly returned successfully
Expected exception types: %s
Arguments: %s''' % (str.join(", ", (e.__name__ for e in exceptions)), gc))
        except exceptions:
            pass


    #
    ##
    #


    def test_log_level(self):
        '''
        Test that 'log_level' is properly handled by the daemon.
        '''

        self.assert_enum(
            None,
            "log_level",
            ["NOTSET", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            test_default = True,
        )


    def test_use_ipsec(self):
        '''
        Test that 'use_ipsec' is properly handled by the daemon.
        '''

        self.assert_boolean(None, "use_ipsec", test_default=True)


    def test_ipsec_manage(self):
        '''
        Test that 'ipsec_manage' is properly handled by the daemon.
        '''

        self.assert_boolean(None, "ipsec_manage", test_default=True)


    def test_ipsec_psk(self):
        '''
        Test that 'ipsec_psk' is properly handled by the daemon.
        '''

        self.assert_hex_string(None, "ipsec_psk", min=6, max=64)


    def test_lib_dir(self):
        '''
        Test that 'lib_dir' is properly handled by the daemon.
        '''

        self.assert_path(None, "lib_dir", test_default=True)


    def test_fwbuilder_script_dir(self):
        '''
        Test that 'fwbuilder_script_dir' is properly handled by the daemon.
        '''

        self.assert_path(None, "fwbuilder_script_dir")


    def test_overlay_conf_dir(self):
        '''
        Test that 'overlay_conf_dir' is properly handled by the daemon.
        '''

        self.assert_path(None, "template_dir", test_default = True)


    def test_template_dir(self):
        '''
        Test that 'template_dir' is properly handled by the daemon.
        '''

        self.assert_path(None, "template_dir", test_default=True)


    def test_pid(self):
        '''
        Test that 'pid' is properly handled by the daemon.
        '''

        self.assert_path(None, "pid", test_default=True)


    def test_ipsec_conf(self):
        '''
        Test that 'ipsec_conf' is properly handled by the daemon.
        '''

        self.assert_path(None, "ipsec_conf", test_default=True)


    def test_ipsec_secrets(self):
        '''
        Test that 'ipsec_secrets' is properly handled by the daemon.
        '''

        self.assert_path(None, "ipsec_secrets", test_default=True)


    def test_overlay_conf(self):
        '''
        Test that 'overlay_conf' is properly handled by the daemon.
        '''

        overlay_conf_dir = self.global_conf["overlay_conf_dir"]

        # Test absolute paths.
        self.assert_success(
            None,
            "overlay_conf",
            [os.path.join(overlay_conf_dir, f) for f in os.listdir(overlay_conf_dir)],
        )

        # Test relative paths.
        self.assert_success(
            None,
            "overlay_conf",
            [os.path.relpath(os.path.join(overlay_conf_dir, f)) for f in os.listdir(overlay_conf_dir)],
        )

        # Test non-existent paths.
        self.assert_fail(None, "overlay_conf", [util.random_string(16)], FileNotFoundError)

        # Test invalid values.
        self.assert_fail(None, "overlay_conf", "", util.GetError)
        self.assert_fail(None, "overlay_conf", 1, l3overlay.daemon.ReadError)
        self.assert_fail(None, "overlay_conf", [""], util.GetError)
        self.assert_fail(None, "overlay_conf", [1], util.GetError)


if __name__ == "__main__":
    unittest.main()
