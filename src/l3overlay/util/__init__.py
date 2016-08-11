#
# IPsec overlay network manager (l3overlay)
# l3overlay/util/__init__.py - utility functions
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


import errno
import ipaddress
import jinja2
import logging
import re
import os
import sys

import distutils.spawn


#
## Argument/parameter processing.
#


def boolean_get(value):
    '''
    Get a boolean value from a string. Raise a ValueError if the string
    is not a valid boolean.
    '''

    lower_value = value.lower()

    if lower_value != "true" and lower_value != "false":
        raise ValueError("invalid value for boolean: %s" % lower_value)

    return True if lower_value == "true" else False


def integer_get(value):
    '''
    Get an integer value from a string. Raise a ValueError if the string
    is not a valid boolean.
    '''

    return int(value)


def hex_get_string(value, min=None, max=None):
    '''
    Check that a string is a valid hexadecimal integer, optionally
    checking if it is within a minimum and maximum length. Returns the
    string if the conditions are satisfied, raises a ValueError otherwise.
    '''

    length = len(value)

    if length == 0:
        raise ValueError("empty string not a valid hexadecimal integer")

    if min is not None and length < min:
        raise ValueError("hexadecimal integer too short, minimum %i digits required: %s" % (min, value))

    if max is not None and length > max:
        raise ValueError("hexadecimal integer too long, maximum %i digits required: %s" % (max, value))

    if not re.fullmatch("[0-9A-Fa-f][0-9A-Fa-f]*", value):
        raise ValueError("given string not a valid hexadecimal integer: %s" % value)

    return value


def enum_get(value, enum):
    '''
    Check that the given value string is in the list of enumeration string
    values, and return the enumeration value the value string is
    equivalent to. Raise a ValueError if it is not in the list.
    '''

    for e in enum:
        if value.lower() == e.lower():
            return e

    raise ValueError("given value %s is not a valid enum, must be one of %s" % (value, str(enum)))


def name_get(value):
    '''
    Check that a string is a valid name, and return it. A name is a string
    that is just one word, without whitespace. Raise a ValueError if the
    string is not a valid name.
    '''

    name = value.strip()

    if len(name) == 0:
        raise ValueError("empty string not a valid name")

    if not re.fullmatch("[^\s][^\s]*", value):
        raise ValueError("given string not a valid name (contains whitespace): %s" % name)

    return name


def section_name_get(section_type, section):
    '''
    Get the unique name for a configuration section by passing in the
    section type and the raw section data.
    '''

    return name_get(re.sub("^%s:" % section_type, '', section))


def ip_network_get(value):
    '''
    Get an IP network from a string. Raises a ValueError if the string
    is not a valid IP network. Supports both IPv4 and IPv6.
    '''

    return ipaddress.ip_network(value)


def ip_network_is_v6(value):
    '''
    Returns true if the given IP network is an IPv6 network.
    Supports an integer, string, IPv4Network or IPv6Network.
    Raises a ValueError if the given value is not a valid IP network.
    '''

    if isinstance(value, ipaddress.IPv6Network):
        return True
    elif isinstance(value, ipaddress.IPv4Network):
        return False

    return isinstance(ipaddress.ip_network(value), ipaddress.IPv6Network)


def ip_address_get(value):
    '''
    Get an IP address from a string. Raises a ValueError if the string
    is not a valid IP address. Supports both IPv4 and IPv6.
    '''

    return ipaddress.ip_address(value)


def ip_address_is_v6(value):
    '''
    Returns true if the given IP address is an IPv6 address.
    Supports an integer, string, IPv4Address or IPv6Address.
    Raises a ValueError if the given value is not a valid IP address.
    '''

    if isinstance(value, ipaddress.IPv6Address):
        return True
    elif isinstance(value, ipaddress.IPv4Address):
        return False

    return isinstance(ipaddress.ip_address(value), ipaddress.IPv6Address)


def netmask_dd_to_cidr(netmask):
    '''
    Convert a netmask in dotted decimal form to the CIDR form.
    '''

    i = 0
    integer = 0
    segments = netmask.split('.')

    for index, segment in enumerate(segments):
        seg = int(segment)

        if seg > 255 or seg < 0:
            raise ValueError("invalid dotted decimal netmask %s" % netmask)

        integer += (seg << (24 - (8 * index)))

    for b in bin(integer)[2:]:
        if b == '1':
            i += 1
        else:
            break

    return i


def netmask_get(value, use_ipv6=False):
    '''
    Get a subnet mask from a string. Raises a ValueError if the string
    is not a valid subnet mask. Supports both CIDR and dotted decimal form.
    '''

    maxlen = 128 if use_ipv6 else 32

    if re.match("\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}", value):
        if use_ipv6:
            raise ValueError("dotted decimal netmask invalid when use_ipv6 is true, use CIDR instead")

        return netmask_dd_to_cidr(value)

    cidr = int(value)

    if cidr > maxlen or cidr < 0:
        raise ValueError("valid CIDR netmask %i, must be within range 0 < x < 128" % cidr)

    return cidr


def list_get(string, pattern='\s*,\s*'):
    '''
    Convert a string separated by regular expression pattern into a list.
    The default pattern separated by a comma, absorbing whitespace in between.
    '''

    return re.split(pattern, string)


#
## File system functions.
#


def path_my_dir():
    '''
    Return the directory containing this script.
    '''

    return os.path.dirname(os.path.realpath(sys.argv[0]))


def path_root():
    '''
    Return the operating system root directory. System independent.
    '''

    return os.path.abspath(os.sep)


# Define the search paths for util.path_search().
# Search for files in the following locations, in this order:
# 1. (current working directory)
# 2. (current working directory)/etc/l3overlay
# 3. (current working directory)/../etc/l3overlay
# 4. (executable directory)
# 5. (executable directory)/etc/l3overlay
# 6. (executable directory)/../etc/l3overlay
# 7. /etc/l3overlay
search_paths = [
    os.getcwd(),
    os.path.join(os.getcwd(), "etc", "l3overlay"),
    os.path.join(os.getcwd(), "..", "etc", "l3overlay"),
    path_my_dir(),
    os.path.join(path_my_dir(), "etc", "l3overlay"),
    os.path.join(path_my_dir(), "..", "etc", "l3overlay"),
    os.path.join(path_root(), "etc", "l3overlay"),
]

def path_search(filename, paths=search_paths):
    '''
    Returns the first instance of a valid filepath, made from the given 
    filename joined with each element from the list of paths. If it doesn't
    find a match, returns the final filepath combination from the list.

    Works with both files and directories, but does not distinguish them.
    '''

    for path in paths:
        filepath = os.path.join(path, filename)
        if (os.path.exists(filepath)):
            return filepath

    return filepath


def file_remove(path):
    '''
    Remove a file at a given path.
    '''

    os.remove(path)


def directory_create(path, mode=0o777, exist_ok=True):
    '''
    Make the directory tree defined in the given file path, including all
    intermediate directories. If the path already exists and is a 
    directory, does nothing.
    '''

    os.makedirs(path, mode=mode, exist_ok=exist_ok)


def directory_delete(path):
    '''
    Remove the existing directory tree, even if it contains files.
    '''

    shutil.rmtree(path)


#
## Command functions.
#


def command_path(command, not_found_ok=False):
    '''
    '''

    path = distutils.spawn.find_executable(command)

    if not not_found_ok and not path:
        raise RuntimeError("cannot find '%s' executable path" % command)

    return path


#
## PID file functions.
#


def pid_create(pid_file, mode=0o666):
    '''
    Create a PID file at the given location, but only if it is not already a PID file
    that contains a running PID.
    '''

    directory_create(os.path.dirname(pid_file))

    old_pid = pid_get(pid_file=pid_file)

    if old_pid:
        raise RuntimeError("PID file '%s' locked by process %i" % (pid_file, old_pid))

    with open(pid_file, "w") as f:
        f.write("%i\n" % os.getpid())

    os.chmod(pid_file, mode)


def pid_get(pid=None, pid_file=None):
    '''
    Checks for the existence of a PID on the running system. If true,
    returns the PID number. If false, returns None.
    Can either use a PID number directly, or take in a PID file and check
    that. If the PID file is not valid or the PID contained inside does 
    not exist, this method deletes that PID file.
    '''

    if pid and pid_file:
        raise ValueError("pid and pid_file are mutually exclusive arguments")

    if pid_file is not None:
        if os.path.exists(pid_file):
            with open(pid_file, "r") as f:
                pid_file_data = f.read().strip()

            if len(pid_file_data) > 0 and re.match("[0-9][0-9]*", pid_file_data):
                pid = int(pid_file_data)
            else:
                # Invalid PID file. Remove it.
                os.remove(pid_file)
                return None
        else:
           # PID file doesn't exist.
           return None
    elif pid is None:
        raise ValueError("must specify one of pid or pid_file")

    if pid <= 0:
        if pid_file is not None:
            raise ValueError("invalid PID: %i from file: %s" % (pid, pid_file))
        else:
            raise ValueError("invalid PID: %i" % pid)

    try:
        os.kill(pid, 0)
    except OSError as e:
        # ESRCH = No such process
        if e.errno == errno.ESRCH:
            return None
        # EPERM = Permission denied
        # A process clearly exists if we don't have access to it.
        elif e.errno == errno.EPERM:
            return pid
        # EINVAL = Invalid signal
        # Something went wrong.
        else:
            raise
    # No exception - process exists
    else:
        return pid


def pid_exists(pid=None, pid_file=None):
    '''
    Checks for the existence of a PID on the running system.
    This function is a wrapper for pid_get() for it to return a boolean
    value if the returned PID number is not required. Therefore,
    it follows the same behaviour as pid_get() with respect to
    raising exceptions and handling PID files.
    '''

    return True if pid_get(pid, pid_file) else False


#
## Logger functions.
#


def logger(log, log_level, logger_name, logger_section=None):
    '''
    Start the logging system, and return the logger to the program.
    '''

    logger = logging.getLogger(logger_name)
    logger.setLevel(log_level)

    lf = str.format(
        "%(asctime)s %(name)s: [%(levelname)s] <{0}> %(message)s",
         logger_section,
    ) if logger_section else "%(asctime)s %(name)s: [%(levelname)s] %(message)s"

    logger_formatter = logging.Formatter(lf)

    if log:
        directory_create(os.path.dirname(log))

        logger_file_handler = logging.FileHandler(log)
        logger_file_handler.setFormatter(logger_formatter)
        logger.addHandler(logger_file_handler)

    logger.debug("started logger")

    return logger


#
## Template functions.
#


def template_read(dir, file):
    '''
    '''

    return jinja2.Environment(trim_blocks=True,loader=FileSystemLoader(dir)).get_template(file)
