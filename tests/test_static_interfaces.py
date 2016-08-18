#
# IPsec overlay network manager (l3overlay)
# l3overlay/tests/test_static_interfaces.py - unit test for testing static interfaces
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
import unittest

from l3overlay import util

import l3overlay.daemon


class StaticInterfacesTest(unittest.TestCase):
    '''
    l3overlay unit test for testing static interfaces.
    '''

    def test_static_interfaces(self):
        '''
        Do a dry run of the l3overlay daemon with overlay configurations
        designed to test each static interface type.
        '''

        conf_dir = os.path.join(util.path_my_dir(), "test_static_interfaces")
        root_dir = os.path.join(util.path_my_dir(), "..")
        tmp_dir = tempfile.mkdtemp(prefix="l3overlay-test_static_interfaces")

        args = {
            "dry_run": "true",

            "log": os.path.join(tmp_dir, "l3overlay.log"),
            "log_level": "DEBUG",

            "use_ipsec": "true",
            "ipsec_manage": "true",

            "overlay_conf_dir": os.path.join(conf_dir, "overlays"),

            "template_dir": os.path.join(root_dir, "l3overlay", "templates"),

            "lib_dir": os.path.join(tmp_dir, "lib"),
        }

        daemon = l3overlay.daemon.read(args)
        daemon.setup()

        daemon.start()

        daemon.stop()
        daemon.remove()


if __name__ == "__main__":
    unittest.main()
