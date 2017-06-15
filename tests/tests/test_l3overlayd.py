#
# IPsec overlay network manager (l3overlay)
# tests/test_l3overlayd.py - unit tests for executing l3overlayd
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


import os
import subprocess
import time
import unittest

from l3overlay import util

from tests.base import SRC_DIR
from tests.base import BaseTest


DAEMON_WAIT_TIMEOUT = 5
DAEMON_TERMINATE_TIMEOUT = 10


class ExecutionError(Exception):
    def __init__(self, message, command, returncode, stdout, stderr):
        super().__init__(
            "%s\n\nCommand: %s\n\nReturn code: %i\n\nstdout:\n%s\n\nstderr:\n%s" %
                    (message, str.join(" ", command), returncode, stdout, stderr))


class L3overlaydTest(BaseTest.Class):
    '''
    l3overlay unit test for executing l3overlayd.
    '''

    name = "test_l3overlayd"


    #
    ##
    #


    def test_l3overlayd(self):
        '''
        Do a dry run of the l3overlay daemon with overlay configurations
        designed to test each static interface type.
        '''

        test_py = os.path.join(self.tmp_dir, "test.py")

        with open(test_py, "w") as f:
            f.write('''
import importlib.machinery
l3overlay = importlib.machinery.SourceFileLoader("l3overlay", "%s/l3overlay/__init__.py").load_module()
l3overlay.main()''' % SRC_DIR)

        command = [util.command_path("python3"), test_py]

        for key, value in self.global_conf.items():
            akey = key.replace("_", "-")
            arg = "--%s" % akey
            if value is None:
                continue
            elif isinstance(value, list) or isinstance(value, tuple):
                for v in value:
                    command.extend([arg, v])
            elif key.startswith("no_"):
                if value == False or (isinstance(value, str) and value.lower() == "false"):
                    command.append("--no-%s" % akey)
            else:
                if value == True or (isinstance(value, str) and value.lower() == "true"):
                    command.append(arg)
                else:
                    command.extend([arg, value])

        with subprocess.Popen(
            command,
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE,
        ) as process:
            try:
                stdout_data, stderr_data = process.communicate(timeout=DAEMON_WAIT_TIMEOUT)
                raise ExecutionError(
                    "l3overlayd terminated unexpectedly",
                    command,
                    process.returncode,
                    stdout_data.decode("UTF-8"),
                    stderr_data.decode("UTF-8"),
                )
            except subprocess.TimeoutExpired:
                pass

            time.sleep(DAEMON_WAIT_TIMEOUT)

            process.terminate()

            try:
                process.communicate(timeout=DAEMON_TERMINATE_TIMEOUT)
            except subprocess.TimeoutExpired as e:
                process.kill()
                stdout_data, stderr_data = process.communicate()
                raise ExecutionError(
                    "l3overlayd did not terminate when expected",
                    command,
                    process.returncode,
                    stdout_data.decode("UTF-8"),
                    stderr_data.decode("UTF-8"),
                )


if __name__ == "__main__":
    unittest.main()
