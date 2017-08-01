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

from tests.base import BaseTest


class DaemonBaseTest(object):
    class Class(BaseTest.Class):
        '''
        l3overlay unit test for reading Daemon objects.
        '''

        name = "test_daemon_base"


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

            gc = conf.copy() if conf else self.global_conf.copy()

            if key and value is not None:
                gc[key] = value

            return gc


        def object_get(self, conf=None):
            '''
            Create an object instance, use assertIsInstance to ensure
            it is of the correct type, and return it.
            '''

            daemon = l3overlay.daemon.read(conf if conf else self.global_conf)
            self.assertIsInstance(daemon, l3overlay.daemon.Daemon)

            return daemon


        def value_get(self, *args, obj=None, internal_key=None):
            '''
            Get a value from the given object, using the supplied
            key-value pair (and internal key if used).
            '''

            if len(args) > 1:
                raise RuntimeError("unrecognised non-keyword arguments: %s" % ",".join(args[1:]))

            key = internal_key if internal_key else args[0]
            return vars(obj)[key]


        def assert_boolean(self, *args, test_default=False):
            '''
            Test that key, of type boolean, is properly handled by the object.
            '''

            key = args[0]
            no_key = "no_%s" % key

            # Test default value.
            if test_default:
                gc = self.global_conf.copy()
                gc[key] = False
                gc[no_key] = True
                self.assert_success(key, conf=gc)

            # Test valid values.
            gc = self.global_conf.copy()
            gc.pop(key)
            gc[no_key] = True
            self.assert_success(key, value=True, expected_value=True, conf=gc)
            self.assert_success(key, value="true", expected_value=True, conf=gc)
            self.assert_success(key, value=1, expected_value=True, conf=gc)
            self.assert_success(key, value=2, expected_value=True, conf=gc)

            gc = self.global_conf.copy()
            gc[key] = False
            gc.pop(no_key)
            self.assert_success(no_key, internal_key=key, value=False, expected_value=False, conf=gc)
            self.assert_success(no_key, internal_key=key, value="false", expected_value=False, conf=gc)
            self.assert_success(no_key, internal_key=key, value=0, expected_value=False, conf=gc)
            self.assert_success(no_key, internal_key=key, value=-1, expected_value=False, conf=gc)

            # Test invalid values.
            gc = self.global_conf.copy()
            gc.pop(key)
            gc[no_key] = True
            self.assert_fail(key, value="", exception=util.GetError, conf=gc)
            self.assert_fail(key, value=util.random_string(6), exception=util.GetError, conf=gc)

            gc = self.global_conf.copy()
            gc[key] = False
            gc.pop(no_key)
            self.assert_fail(no_key, value="", exception=util.GetError, conf=gc)
            self.assert_fail(no_key, value=util.random_string(6), exception=util.GetError, conf=gc)
