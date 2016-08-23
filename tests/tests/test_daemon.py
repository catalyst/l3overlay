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

from l3overlay import util

import l3overlay.daemon


class DaemonTest(tests.L3overlayTest):
    '''
    l3overlay unit test for testing static interfaces.
    '''

    name = "test_daemon"


    #
    ##
    #


    def assert_success(self, args):
        '''
        Try and read an l3overlay daemon using the given arguments.
        Assumes it will succeed, and will run an assertion test to make
        sure a Daemon is returned.
        '''

        a = self.global_conf.copy()
        a.update(args)

        daemon = l3overlay.daemon.read(a)
        self.assertIsInstance(daemon, l3overlay.daemon.Daemon)

        return daemon


    def assert_fail(self, args, *exceptions):
        '''
        Try and read an l3overlay daemon using the given arguments.
        Assumes it will fail, and raises a RuntimeError if it doesn't.
        '''

        a = self.global_conf.copy()
        a.update(args)

        try:
            l3overlay.daemon.read(a)
            raise RuntimeError('''l3overlay.daemon.read unexpectedly returned successfully
Expected exception types: %s
Arguments: %s''' % (str.join(", ", (e.__name__ for e in exceptions)), a))
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
            ["NOTSET", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            "log_level",
            test_default = True,
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


if __name__ == "__main__":
    tests.main()
