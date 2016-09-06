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


import configparser
import errno
import ipaddress
import jinja2
import logging
import re
import os
import random
import shutil
import signal
import string
import sys

import distutils.spawn

from l3overlay.util.exception.l3overlayerror import L3overlayError


#
## Argument/parameter processing.
#


class GetError(L3overlayError):
    pass


def boolean_get(value):
    '''
    Get a boolean value from a string. Raise a GetError if the string
    is not a valid boolean.
    '''

    if isinstance(value, bool):
        return value
    elif isinstance(value, int):
        return True if value > 0 else False
    elif isinstance(value, str):
        lower_value = value.lower()

        if lower_value != "true" and lower_value != "false":
            raise GetError("value '%s' not a valid boolean" % lower_value)

        return True if lower_value == "true" else False
    else:
        raise GetError("value '%s' not a valid boolean" % value)


def integer_get(value, minval=None, maxval=None):
    '''
    Get an integer value from a string. Raise a GetError if the string
    is not a valid boolean.
    '''

    try:
        integer = int(value)

        if minval is not None and integer < minval:
            raise GetError("integer value %s too low, minimum value %i required" % (integer, minval))

        if maxval is not None and integer > maxval:
            raise GetError("integer value %s too high, maximum value %i required" % (integer, maxval))

        return integer

    except ValueError:
        raise GetError("value '%s' is not a valid integer" % value)


def hex_get_string(value, min=None, max=None):
    '''
    Check that a string is a valid hexadecimal integer, optionally
    checking if it is within a minimum and maximum length. Returns the
    string if the conditions are satisfied, raises a GetError otherwise.
    '''

    if isinstance(value, int):
        return hex(value)

    elif isinstance(value, str):
        if value.startswith("0x"):
            value = value[2:]

        length = len(value)

        if not length:
            raise GetError("empty string not a valid hex integer")

        if min is not None and length < min:
            raise GetError("hex integer '%s' too short, minimum %i digits required" % (value, min))

        if max is not None and length > max:
            raise GetError("hex integer '%s' too long, maximum %i digits required" % (value, max))

        for v in value:
            if v not in string.hexdigits:
                raise GetError("string '%s' not a valid hexadecimal integer")

        return "0x%s" % value

    else:
        raise GetError("value '%s' not a valid hex integer" % value)


def enum_get(value, enum):
    '''
    Check that the given value string is in the list of enumeration string
    values, and return the enumeration value the value string is
    equivalent to. Raise a GetError if it is not in the list.
    '''

    if not isinstance(value, str):
        raise GetError("value '%s' is not an enumerable string" % str(value))

    for e in enum:
        if value.lower() == e.lower():
            return e

    raise GetError("value '%s' not in enumeration list, must be one of %s" %
            (value, str.join("/", enum)))


def name_get(value):
    '''
    Check that a string is a valid name, and return it. A name is a string
    that is just one word, without whitespace. Raise a GetError if the
    string is not a valid name.
    '''

    if not isinstance(value, str):
        raise GetError("non-string value '%s' not a valid name" % value)

    if len(value) == 0:
        raise GetError("empty string not a valid name")

    name = value.strip()

    if not re.fullmatch("[^\s][^\s]*", name):
        raise GetError("given string not a valid name (contains whitespace): %s" % name)

    return name


def path_get(value):
    '''
    Check that the given value is a fully qualified file system path, raising
    GetError if it isn't.
    '''

    if not isinstance(value, str):
        raise GetError("non-string value '%s' not a valid file system path" % str(value))

    if not os.path.isabs(value):
        raise GetError("value '%s' not a fully qualified file system path" % value)

    return value


def section_header(type, name):
    '''
    Build a section header from the given type and name.
    '''

    return "%s:%s" % (type, name)


def section_split(section):
    '''
    Get the section type and name from the given section header.
    Returns a two-element tuple containing each part of section.
    If no section name is found, that element is None.
    '''

    parts = section.split(":")
    if len(parts) < 2:
        return (name_get(parts[0]), None)
    else:
        return (name_get(parts[0]), name_get(parts[1]))


def section_type_get(section):
    '''
    Get the section type from the given section header.
    '''

    return section_split(section)[0]


def section_name_get(section):
    '''
    Get the section name from the given section header.
    '''

    return section_split(section)[1]


def ip_network_get(value):
    '''
    Get an IP network from a string. Raises a GetError if the string
    is not a valid IP network. Supports both IPv4 and IPv6.
    '''

    if isinstance(value, ipaddress.IPv4Address) or isinstance(value, ipaddress.IPv6Address):
        raise GetError(
            "%s not allowed to be converted to IP network" % type(value).__name__,
        )

    try:
        return ipaddress.ip_network(value)
    except ValueError:
        raise GetError("value '%s' is not a valid IPv4/IPv6 address" % value)


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
    Get an IP address from a string. Raises a GetError if the string
    is not a valid IP address. Supports both IPv4 and IPv6.
    '''

    if isinstance(value, ipaddress.IPv4Network) or isinstance(value, ipaddress.IPv6Network):
        raise GetError(
            "%s not allowed to be converted to IP address, use class attributes" % type(value).__name__,
        )

    try:
        return ipaddress.ip_address(value)
    except ValueError:
        raise GetError("value '%s' is not a valid IPv4/IPv6 address" % value)


def ip_address_remote(local):
    '''
    For a given local_address (either an integer, IPv4Address or
    IPv6Address), return the other end of a two-node linknet
    (/31 for IPv4, /127 for IPv6).
    '''

    return ipaddress.ip_address(int(local) ^ 1)


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
            raise GetError("invalid dotted decimal netmask %s" % netmask)

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

    if isinstance(value, str) and re.match("\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}", value):
        if use_ipv6:
            raise GetError("dotted decimal netmask invalid when use_ipv6 is true, use CIDR instead")

        return netmask_dd_to_cidr(value)

    try:
        cidr = int(value)

        if cidr > maxlen or cidr < 0:
            raise GetError("CIDR netmask %i out of given range 0 < x < %i" % (cidr, maxlen))

        return cidr
    except ValueError:
        raise GetError("value '%s' not a valid netmask" % value)


def bird_prefix_get(value):
    '''
    Check that a string is a BIRD prefix, and return it. Raise a
    ValueError if the string is not a valid BIRD prefix.
    This method allows the use of prefix patterns that are allowed to be
    used in sets of prefixes in BIRD filters.
    Check the BIRD documentation here for more information on BIRD
    prefixes:
    http://bird.network.cz/?get_doc&f=bird-5.html#ss5.2
    '''

    netmask_pattern = "-?[0-9][0-9]*"
    netmask_range_pattern = "^\{[0-9][0-9]*,[0-9][0-9]*\}$"
    netmask_operator_pattern = "^[+-]$"

    prefix = re.split("/", value)

    address = None
    netmask = None

    # Get the IP address and convert it to an IP address object using
    # ip_address_get, to ensure it is a real IP address.
    try:
        address = ip_address_get(prefix[0])
    except GetError:
        raise GetError("invalid BIRD prefix '%s', invalid address segment" % value)

    # Check for a valid netmask in the netmask segment.
    try:
        netmask = netmask_get(re.match(netmask_pattern, prefix[1]).group(), ip_address_is_v6(address))
    except GetError:
        raise GetError("invalid BIRD prefix '%s', invalid netmask segment" % value)

    # The interesting part about BIRD prefixes, syntatically, is in the
    # netmask segment, which can not just be CIDR numbers, but can also be
    # special expressions, depending on the range of subnets required.
    #
    # This expression can take the following forms:
    # 10.192.0.0/16+ - match all subprefixes of 10.192.0.0/16
    # 10.192.0.0/16- - match all superprefixes of 10.192.0.0/16
    # 10.192.0.0/16{20,24} - match all subprefixes of 10.192.0.0/16 which
    #                        have a prefix length of between 20 to 24.
    #
    # This part checks that the syntax for those expressions is correct.
    expr = prefix[1][len(str(netmask)):]

    if expr:
        if re.match(netmask_range_pattern, expr):
            netmasks = re.findall(netmask_pattern, expr)

            for n in netmasks:
                try:
                    netmask_get(n, ip_address_is_v6(address))
                except Get:
                    raise GetError("invalid BIRD prefix '%s', invalid netmask %i in expression segment" % (value, n))
        elif not re.match(netmask_operator_pattern, expr):
            raise GetError("invalid BIRD prefix '%s', invalid expression segment" % value)

    # All checks have passed. Return the value unmodified.
    return value


def list_get(s, length=None, pattern="\\s*,\\s*"):
    '''
    Convert a string separated by regular expression pattern into a list.
    The default pattern separated by a comma, absorbing whitespace in between.
    '''

    if not isinstance(s, str):
        raise GetError("non-string value '%s' is not a valid separated string" % s)

    l = re.split(pattern, s)

    if length and length != len(l):
        raise GetError("list length %s does not match required length %s" % (len(l), length))

    return l


#
## Random functions.
#


def random_string(length, alpha=True, num=False):
    '''
    Return a randomly generated string, containing either
    letters, numbers, or both.
    '''

    set = []

    if alpha:
        set.append(string.ascii_letters)

    if num:
        set.append(string.digits)

    set = str.join("", set)

    return str.join("", (random.choice(set) for __ in range(length)))


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


def directory_remove(path, nonexist_ok=True):
    '''
    Remove the existing directory tree, even if it contains files.
    '''

    if not nonexist_ok or os.path.exists(path):
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

    if old_pid and old_pid != os.getpid():
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


def pid_kill(pid=None, pid_file=None, signal=signal.SIGTERM, timeout=10):
    '''
    Sends a signal to the process of the given PID or PID file, and waits
    for it to terminate.
    '''

    p = pid_get(pid, pid_file)

    if pid:
        t = 0.0
        os.kill(p, signal)
        while t < timeout and pid_exists(pid=p):
            time.sleep(1)
            t += 0.1
        if pid_exists(pid=p):
            raise RuntimeError("unable to terminate PID %s using signal '%s'" % (p, signal))


#
## Configuration functions.
#


def config(conf=None):
    '''
    Parse a given configuration file, and return its configuration object.
    '''

    config = configparser.ConfigParser()

    if conf:
        if not os.path.isfile(conf):
            raise FileNotFoundError(conf)
        config.read(conf)

    return config


#
## Template functions.
#


def template_read(dir, file):
    '''
    '''

    return jinja2.Environment(trim_blocks=True, loader=jinja2.FileSystemLoader(dir)).get_template(file)
