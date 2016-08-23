#
# IPsec overlay network manager (l3overlay)
# l3overlay/tests/tests/__init__.py - unit test constants and helper functions
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
import string
import tempfile
import unittest

from l3overlay import util


MY_DIR   = util.path_my_dir()
ROOT_DIR = os.path.join(MY_DIR, "..", "..")
SRC_DIR  = os.path.join(ROOT_DIR, "src")

LOG_DIR = os.path.join(ROOT_DIR, ".tests")


class L3overlayTest(unittest.TestCase):
    '''
    Unit test base class.
    '''

    name = "test_l3overlay"


    #
    ##
    #


    def setUp(self):
        '''
        Set up the unit test runtime state.
        '''

        conf_dir = os.path.join(MY_DIR, self.name)
        tmp_dir = tempfile.mkdtemp(prefix="l3overlay-%s-" % self.name)

        log_dir = os.path.join(LOG_DIR, os.path.basename(tmp_dir))

        self.global_conf = {
            "dry_run": "true",

            "log_level": "DEBUG",

            "use_ipsec": "true",
            "ipsec_manage": "true",

            "lib_dir": os.path.join(tmp_dir, "lib"),

            "overlay_conf_dir": os.path.join(conf_dir, "overlays"),
            "template_dir": os.path.join(ROOT_DIR, "l3overlay", "templates"),


            "log": os.path.join(log_dir, "l3overlay.log"),
            "pid": os.path.join(tmp_dir, "l3overlayd.pid"),
        }


    def tearDown(self):
        '''
        Tear down the unit test runtime state.
        '''

        util.directory_remove(self.global_conf["lib_dir"])
        util.directory_remove(os.path.dirname(self.global_conf["pid"]))


    #
    ##
    #


    def assert_success(self, args):
        '''
        Assertion abstract method for success.
        Process:
        * Take in an argument dictionary
        * Create an object
        * Run assertions
        * Return the object
        '''

        raise NotImplementedError()


    def assert_fail(self, args, *exceptions):
        '''
        Assertion abstract method for failure.
        Process:
        * Take in an argument dictionary and a
          list of exceptions that could be thrown
        * Create an object
        * Run assertions
        '''

        raise NotImplementedError()


    #
    ##
    #


    def assert_boolean(self, key, test_default=False):
        '''
        Test that key, of type boolean, is properly handled by the daemon.
        '''

        # Test default value, if specified.
        if test_default:
            object = self.assert_success({key: None})
            self.assert_success({key: vars(object)[key]})

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


    def assert_hex_string(self, key, min=None, max=None, test_default=False):
        '''
        Test that key, of type hex string, is properly handled by the daemon.
        Optionally checks if digit limits are properly handled, by specifying
        a miniumum and maximum digit size.
        '''

        vvs = string.hexdigits

        _min = min if min is not None else 1
        _max = max if max is not None else max(_min + 1, 16)

        # Test default value, if specified.
        if test_default:
            object = self.assert_success({key: None})
            self.assert_success({key: vars(object)[key]})

        # Test valid values.
        for v in vvs:
            self.assert_success({key: str.join("", [v for __ in range(0, _min)])})

        self.assert_success({
            key: str.join("", [vvs[i % len(vvs)] for i in range(0, _max)]),
        })

        # Test invalid values.
        self.assert_fail({key: ""}, ValueError)

        self.assert_fail({
            key: str.join("", ["z" for __ in range(0, _min)]),
        }, ValueError)

        if min is not None and _min > 1:
            self.assert_fail({
                key: str.join("", [vvs[i % len(vvs)] for i in range(0, _min - 1)]),
            }, ValueError)

        if max is not None and _max > 1:
            self.assert_fail({
                key: str.join("", [vvs[i % len(vvs)] for i in range(0, _max + 1)]),
            }, ValueError)


    def assert_enum(self, enum, key, test_default=False):
        '''
        Test that key, of type enum, is properly handled by the daemon.
        '''

        # Test default value, if specified.
        if test_default:
            object = self.assert_success({key: None})
            self.assert_success({key: vars(object)[key]})

        # Test valid values.
        for e in enum:
            self.assert_success({key: e.upper()})
            self.assert_success({key: e.lower()})

        # Test invalid values.
        self.assert_fail({key: ""}, ValueError)
        self.assert_fail({key: util.random_string(16)}, ValueError)
        self.assert_fail({key: 1}, ValueError)


def main():
    '''
    Unit test main routine.
    '''

    unittest.main()
