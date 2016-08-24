#
# IPsec overlay network manager (l3overlay)
# tests/test_l3overlayd.py - unit tests for executing l3overlayd
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
import subprocess
import tests
import time

from l3overlay import util


DAEMON_WAIT_TIMEOUT = 5
DAEMON_TERMINATE_TIMEOUT = 10


class L3overlaydTest(tests.L3overlayTest):
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

        command = [util.command_path("python3"), "-c", "import l3overlay; l3overlay.main()"]

        for key, value in self.global_conf.items():
            arg = "--%s" % key.replace("_", "-")
            if value == True or value.lower() == "true":
                command.append(arg)
            elif not isinstance(value, bool):
                command.extend([arg, value])

        with subprocess.Popen(
            command,
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE,
        ) as process:
            try:
                stdout_data, stderr_data = process.communicate(timeout=DAEMON_WAIT_TIMEOUT)
                raise RuntimeError(
                    "daemon terminated, timeout expected, return code %i\n\nstdout:\n%s\n\nstderr:\n%s" %
                        (process.returncode, stdout_data.decode("UTF-8"), stderr_data.decode("UTF-8")))
            except subprocess.TimeoutExpired:
                pass

            time.sleep(DAEMON_WAIT_TIMEOUT)

            process.terminate()

            try:
                process.communicate(timeout=DAEMON_TERMINATE_TIMEOUT)
            except subprocess.TimeoutExpired as e:
                process.kill()
                stdout_data, stderr_data = process.communicate()
                raise RuntimeError("daemon did not terminate when expected, output:\n%s" %
                        stdout_data.decode("UTF-8"))


if __name__ == "__main__":
    tests.main()
