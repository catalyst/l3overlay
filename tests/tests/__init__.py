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
import tempfile

from l3overlay import util


MY_DIR   = util.path_my_dir()
ROOT_DIR = os.path.join(MY_DIR, "..", "..")
SRC_DIR  = os.path.join(ROOT_DIR, "src")

LOG_DIR = os.path.join(ROOT_DIR, ".tests")


def global_conf_get(test_name, daemon_name = None):
    '''
    Create an l3overlay daemon test global configuration,
    prefixing required file and directory paths with the
    given daemon name, if it exists.
    '''

    conf_subdir = os.path.join(test_name, daemon_name) if daemon_name else test_name
    conf_dir = os.path.join(MY_DIR, conf_subdir)

    tmp_subdir = "l3overlay-%s-%s-" % (test_name, daemon_name) if daemon_name else "l3overlay-%s-" % test_name
    tmp_dir = tempfile.mkdtemp(prefix=tmp_subdir)

    log_dir = os.path.join(LOG_DIR, os.path.basename(tmp_dir))

    args = {
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

    return args


def global_conf_cleanup(args):
    '''
    Clean up global configuration runtime state.
    '''

    util.directory_remove(args["lib_dir"])
    util.directory_remove(os.path.dirname(args["pid"]))
