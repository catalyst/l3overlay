#
# IPsec overlay network manager (l3overlay)
# tests/base/overlay.py - base class for overlay-related unit tests
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


import copy

import l3overlay.overlay

import l3overlay.overlay.static_interface

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


        def config_get(self, *args, value=None, conf=None):
            '''
            '''

            if len(args) > 2:
                raise RuntimeError("unrecognised non-keyword arguments: %s" % ",".join(args[2:]))
            elif len(args) == 2:
                section = args[0]
                key = args[1]
            else:
                section = None
                key = args[0] if args else None

            oc = copy.deepcopy(conf) if conf else copy.deepcopy(self.overlay_conf)

            # Section is optional. If specified,
            # add the key-value pair to the section
            # of the overlay config.
            if section:
                if section not in oc:
                    oc[section] = {}
                if value is None and key in oc[section]:
                    del oc[section][key]
                elif value is not None:
                    oc[section][key] = value

            # Otherwise, directly add the key-value pair
            # to the top level of the overlay config.
            elif key:
                if key not in oc:
                    oc[key] = {}
                if value is None and key in oc:
                    del oc[key]
                elif value is not None:
                    oc[key] = value

            # Need either at least key specified!
            elif value:
                raise RuntimeError("value specified but key not specified")

            return oc


        def object_get(self, conf=None):
            '''
            Create an object instance, use assertIsInstance to ensure
            it is of the correct type, and return it.
            '''

            overlay = l3overlay.overlay.read(
                self.global_conf["log"],
                self.global_conf["log_level"],
                config=conf if conf else self.overlay_conf,
            )
            self.assertIsInstance(overlay, l3overlay.overlay.Overlay)

            return overlay


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
                for si in obj.static_interfaces:
                    if name == si.name:
                        return vars(si)[key]

            elif section.startswith("active"):
                name = util.section_name_get(section)
                for ai in obj.active_interfaces:
                    if name == ai.name:
                        return vars(ai)[key]

            else:
                raise RuntimeError("unknown section type '%s'" % section)
