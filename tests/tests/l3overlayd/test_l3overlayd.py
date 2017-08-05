#
# IPsec overlay network manager (l3overlay)
# tests/l3overlayd/test_l3overlayd.py - unit tests for executing l3overlayd
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
Unit tests for executing l3overlayd.
'''


import os
import subprocess
import sys
import time

from l3overlay import util

from tests.l3overlayd import L3overlaydBaseTest


DAEMON_WAIT_TIMEOUT = 5
DAEMON_TERMINATE_TIMEOUT = 10


class ExecutionError(Exception):
    '''
    Exception to raise when l3overlayd encounters an error during execution.
    '''
    # pylint: disable=too-many-arguments
    def __init__(self, message, command, returncode, stdout, stderr):
        super().__init__("%s\n\nCommand: %s\n\nReturn code: %i\n\nstdout:\n%s\n\nstderr:\n%s" %
                         (message, str.join(" ", command), returncode, stdout, stderr))


class L3overlaydTest(L3overlaydBaseTest):
    '''
    l3overlay unit test for executing l3overlayd.
    '''

    name = "test_l3overlayd"
    conf_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), name)


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

        pass


    def object_get(self, conf=None):
        '''
        Create an object instance, use assertIsInstance to ensure
        it is of the correct type, and return it.
        '''

        pass


    def value_get(self, *args, obj=None, internal_key=None):
        '''
        Get a value from the given object, using the supplied
        key-value pair (and internal key if used).
        '''

        pass


    #
    ##
    #


    def test_l3overlayd(self):
        '''
        Do a dry run of the l3overlay daemon with overlay configurations
        designed to test each static interface type.
        '''

        test_py = os.path.join(self.tmp_dir, "test.py")

        with open(test_py, "w") as fil:
            fil.write('''#!/usr/bin/env python3
import l3overlay.l3overlayd.main as l3overlayd
l3overlayd.main()''')

        command = [util.command_path("python3"), test_py]

        for key, value in self.global_conf.items():
            akey = key.replace("_", "-")
            arg = "--%s" % akey
            if value is None:
                continue
            elif isinstance(value, (list, tuple)):
                for val in value:
                    command.extend([arg, val])
            elif key.startswith("no_"):
                if value is False or (isinstance(value, str) and value.lower() == "false"):
                    command.append("--no-%s" % akey)
            else:
                if value is True or (isinstance(value, str) and value.lower() == "true"):
                    command.append(arg)
                else:
                    command.extend([arg, value])

        env = os.environ.copy()
        env["PYTHONPATH"] = ":".join(sys.path)

        with subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
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
            except subprocess.TimeoutExpired:
                process.kill()
                stdout_data, stderr_data = process.communicate()
                raise ExecutionError(
                    "l3overlayd did not terminate when expected",
                    command,
                    process.returncode,
                    stdout_data.decode("UTF-8"),
                    stderr_data.decode("UTF-8"),
                )
