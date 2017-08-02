#
# IPsec overlay network manager (l3overlay)
# l3overlay/l3overlayd/process/__init__.py - process manager helper classes
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


class ProcessError(Exception):
    def __init__(self, message, popen, stdout, stderr):
        super().__init__("%s\n\nCommand: %s\n\nReturn code: %i\n\nstdout:\n%s\n\nstderr:\n%s" % (
            message,
            str.join(" ", popen.args),
            popen.returncode,
            stdout.decode("UTF-8"),
            stderr.decode("UTF-8"),
        ))
