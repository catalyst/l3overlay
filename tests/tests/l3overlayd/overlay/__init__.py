#
# IPsec overlay network manager (l3overlay)
# tests/l3overlayd/overlay/__init__.py - base class for overlay-level tests
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
Base class for overlay-level tests.
'''


import copy
import os
import unittest

from l3overlay import util

from l3overlay.l3overlayd import overlay

from tests.l3overlayd import L3overlaydBaseTest


class OverlayBaseTest(L3overlaydBaseTest):
    '''
    Base class for overlay-related unit tests.
    '''

    name = "test_overlay_base"
    conf_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), name)


    #
    ##
    #


    def setUp(self):
        '''
        Set up the unit test runtime state.
        '''

        super().setUp()

        if self.name == "test_overlay_base":
            raise unittest.SkipTest("cannot run base class as a test case")

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


    def config_get(self, *args, value=None, conf=None):
        '''
        Create an object config instance, using the given arguments
        to override values in it. An existing config instance can also
        be specified to base the result from, rather than the test class
        default.
        '''

        if len(args) > 2:
            raise RuntimeError("unrecognised non-keyword arguments: %s" % ",".join(args[2:]))
        elif len(args) == 2:
            section = args[0]
            key = args[1]
        else:
            section = None
            key = args[0] if args else None

        obje = copy.deepcopy(conf) if conf else copy.deepcopy(self.overlay_conf)

        # Section is optional. If specified,
        # add the key-value pair to the section
        # of the overlay config.
        if section:
            if section not in obje:
                obje[section] = {}
            if value is None and key in obje[section]:
                del obje[section][key]
            elif value is not None:
                obje[section][key] = value

        # Otherwise, directly add the key-value pair
        # to the top level of the overlay config.
        elif key:
            if key not in obje:
                obje[key] = {}
            if value is None and key in obje:
                del obje[key]
            elif value is not None:
                obje[key] = value

        # Need either at least key specified!
        elif value:
            raise RuntimeError("value specified but key not specified")

        return obje


    def object_get(self, conf=None):
        '''
        Create an object instance, use assertIsInstance to ensure
        it is of the correct type, and return it.
        '''

        over = overlay.read(
            self.global_conf["log"],
            self.global_conf["log_level"],
            config=conf if conf else self.overlay_conf,
        )
        self.assertIsInstance(over, overlay.Overlay)

        return over


    def value_get(self, *args, obj=None, internal_key=None):
        '''
        Get a value from the given object, using the supplied
        key-value pair (and internal key if used).
        '''

        if len(args) > 2:
            raise RuntimeError("unrecognised non-keyword arguments: %s" % ",".join(args[2:]))
        elif len(args) == 2:
            section = args[0]
            key = args[1]
        else:
            section = None
            key = args[0]

        key = internal_key if internal_key else key
        key = key.replace("-", "_")

        if not section or section == "overlay":
            return vars(obj)[key]

        elif section.startswith("static"):
            name = util.section_name_get(section)
            for stat in obj.static_interfaces:
                if name == stat.name:
                    return vars(stat)[key]

        elif section.startswith("active"):
            name = util.section_name_get(section)
            for acti in obj.active_interfaces:
                if name == acti.name:
                    return vars(acti)[key]

        else:
            raise RuntimeError("unknown section type '%s'" % section)
