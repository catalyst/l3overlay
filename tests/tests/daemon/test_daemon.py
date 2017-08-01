#
# IPsec overlay network manager (l3overlay)
# tests/test_daemon.py - unit test for reading Daemon objects
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


import l3overlay
import os
import unittest

from l3overlay import util

import l3overlay.daemon

from tests.daemon.base import DaemonBaseTest


class DaemonTest(DaemonBaseTest.Class):
    '''
    l3overlay unit test for reading Daemon objects.
    '''

    name = "test_daemon"


    def test_log_level(self):
        '''
        Test that 'log_level' is properly handled by the daemon.
        '''

        self.assert_enum(
            "log_level",
            enum=["NOTSET", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            test_default=True,
        )


    def test_use_ipsec(self):
        '''
        Test that 'use_ipsec' is properly handled by the daemon.
        '''

        self.assert_boolean("use_ipsec", test_default=True)


    def test_ipsec_manage(self):
        '''
        Test that 'ipsec_manage' is properly handled by the daemon.
        '''

        self.assert_boolean("ipsec_manage", test_default=True)


    def test_ipsec_psk(self):
        '''
        Test that 'ipsec_psk' is properly handled by the daemon.
        '''

        self.assert_hex_string("ipsec_psk", min=6, max=64)


    def test_lib_dir(self):
        '''
        Test that 'lib_dir' is properly handled by the daemon.
        '''

        self.assert_path("lib_dir", test_default=True)


    def test_fwbuilder_script_dir(self):
        '''
        Test that 'fwbuilder_script_dir' is properly handled by the daemon.
        '''

        self.assert_path("fwbuilder_script_dir")


    def test_overlay_conf_dir(self):
        '''
        Test that 'overlay_conf_dir' is properly handled by the daemon.
        '''

        self.assert_path("overlay_conf_dir", test_default=True)


    def test_template_dir(self):
        '''
        Test that 'template_dir' is properly handled by the daemon.
        '''

        self.assert_path("template_dir", test_default=True)


    def test_pid(self):
        '''
        Test that 'pid' is properly handled by the daemon.
        '''

        self.assert_path("pid", test_default=True)


    def test_ipsec_conf(self):
        '''
        Test that 'ipsec_conf' is properly handled by the daemon.
        '''

        self.assert_path("ipsec_conf", test_default=True)


    def test_ipsec_secrets(self):
        '''
        Test that 'ipsec_secrets' is properly handled by the daemon.
        '''

        self.assert_path("ipsec_secrets", test_default=True)


    def test_overlay_conf(self):
        '''
        Test that 'overlay_conf' is properly handled by the daemon.
        '''

        overlay_conf_dir = self.global_conf["overlay_conf_dir"]

        gc = self.global_conf.copy()
        gc["overlay_global_conf"] = None

        # Test absolute paths.
        value = [os.path.join(overlay_conf_dir, f) for f in os.listdir(overlay_conf_dir)]
        self.assert_success(
            "overlay_conf",
            value=value,
            conf=gc,
        )

        # Test relative paths.
        value = [os.path.relpath(os.path.join(overlay_conf_dir, f)) for f in os.listdir(overlay_conf_dir)]
        self.assert_success(
            "overlay_conf",
            value=value,
            conf=gc,
        )

        # Test non-existent paths.
        self.assert_fail(
            "overlay_conf",
            value=[util.random_string(16)],
            exception=FileNotFoundError,
            conf=gc,
        )

        # Test invalid values.
        self.assert_fail("overlay_conf", value="", exception=util.GetError, conf=gc)
        self.assert_fail("overlay_conf", value=1, exception=l3overlay.daemon.ReadError, conf=gc)
        self.assert_fail("overlay_conf", value=[""], exception=util.GetError, conf=gc)
        self.assert_fail("overlay_conf", value=[1], exception=util.GetError, conf=gc)


if __name__ == "__main__":
    unittest.main()
