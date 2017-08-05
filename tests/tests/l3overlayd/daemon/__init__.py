#
# IPsec overlay network manager (l3overlay)
# tests/l3overlayd/daemon/__init__.py - base class for daemon-level tests
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
Base class for daemon-level tests.
'''


import os
import unittest

from l3overlay import util

from l3overlay.l3overlayd import daemon

from tests.l3overlayd import L3overlaydBaseTest


class DaemonBaseTest(L3overlaydBaseTest):
    '''
    Base class for daemon-level tests.
    '''

    name = "test_daemon_base"
    conf_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), name)


    #
    ##
    #


    def setUp(self):
        '''
        Set up the unit test runtime state.
        '''

        super().setUp()

        if self.name == "test_daemon_base":
            raise unittest.SkipTest("cannot run base class as a test case")


    #
    ##
    #


    def config_get(self, *args, value=None, conf=None):
        '''
        Create an object config instance, using the given arguments
        to override values in it. An existing config instance can also
        be specified to base the result from, rather than the test class
        default.
        '''

        if len(args) > 1:
            raise RuntimeError("unrecognised non-keyword arguments: %s" % ",".join(args[1:]))

        key = args[0] if args else None

        glob = conf.copy() if conf else self.global_conf.copy()

        if key and value is not None:
            glob[key] = value

        return glob


    def object_get(self, conf=None):
        '''
        Create an object instance, use assertIsInstance to ensure
        it is of the correct type, and return it.
        '''

        daem = daemon.read(conf if conf else self.global_conf)
        self.assertIsInstance(daem, daemon.Daemon)

        return daem


    def value_get(self, *args, obj=None, internal_key=None):
        '''
        Get a value from the given object, using the supplied
        key-value pair (and internal key if used).
        '''

        if len(args) > 1:
            raise RuntimeError("unrecognised non-keyword arguments: %s" % ",".join(args[1:]))

        key = internal_key if internal_key else args[0]
        return vars(obj)[key]


    def assert_boolean(self, *args, test_default=False,
                       internal_key=None,
                       conf=None):
        '''
        Test that key, of type boolean, is properly handled by the object.
        '''

        key = args[0]
        no_key = "no_%s" % key

        if not internal_key:
            internal_key = key

        # Test default value.
        if test_default:
            glob = conf.copy() if conf else self.global_conf.copy()
            glob[key] = False
            glob[no_key] = True
            self.assert_success(key, conf=glob)

        # Test valid values.
        glob = conf.copy() if conf else self.global_conf.copy()
        glob.pop(key)
        glob[no_key] = True
        self.assert_success(
            key,
            value=True, expected_value=True,
            internal_key=internal_key,
            conf=glob,
        )
        self.assert_success(
            key,
            value="true", expected_value=True,
            internal_key=internal_key,
            conf=glob,
        )
        self.assert_success(
            key,
            value=1, expected_value=True,
            internal_key=internal_key,
            conf=glob,
        )
        self.assert_success(
            key,
            value=2, expected_value=True,
            internal_key=internal_key,
            conf=glob,
        )

        glob = conf.copy() if conf else self.global_conf.copy()
        glob[key] = False
        glob.pop(no_key)
        self.assert_success(
            no_key,
            value=False, expected_value=False,
            internal_key=internal_key,
            conf=glob,
        )
        self.assert_success(
            no_key,
            value="false", expected_value=False,
            internal_key=internal_key,
            conf=glob,
        )
        self.assert_success(
            no_key,
            value=0, expected_value=False,
            internal_key=internal_key,
            conf=glob,
        )
        self.assert_success(
            no_key,
            value=-1, expected_value=False,
            internal_key=internal_key,
            conf=glob,
        )

        # Test invalid values.
        glob = conf.copy() if conf else self.global_conf.copy()
        glob.pop(key)
        glob[no_key] = True
        self.assert_fail(
            key,
            value="", exception=util.GetError,
            conf=glob,
        )
        self.assert_fail(
            key,
            value=util.random_string(6), exception=util.GetError,
            conf=glob,
        )

        glob = conf.copy() if conf else self.global_conf.copy()
        glob[key] = False
        glob.pop(no_key)
        self.assert_fail(
            no_key,
            value="", exception=util.GetError,
            conf=glob,
        )
        self.assert_fail(
            no_key,
            value=util.random_string(6), exception=util.GetError,
            conf=glob,
        )
