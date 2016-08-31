#
# IPsec overlay network manager (l3overlay)
# l3overlay/network/interface/tuntap.py - tun/tap interface class and functions
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


from l3overlay.network.interface import Interface
from l3overlay.network.interface import NotFoundError
from l3overlay.network.interface import UnexpectedTypeError


IF_TYPES = ["tun", "tap"]


class Tuntap(Interface):
    '''
    TUN/TAP interface class. Subclass of the Interface class, adding
    TUN/TAP interface-specific functions.
    '''

    def __init__(self, logger, ipdb, interface, name, mode):
        '''
        '''

        super().__init__(logger, ipdb, interface, name)

        self.description = "%s interface" % mode


def get(dry_run, logger, ipdb, name):
    '''
    Return a tun/tap interface object for the given interface name.
    '''

    logger.debug("getting runtime state for %s interface '%s'" % (str.join("/", IF_TYPES), name))

    if dry_run:
        return Tuntap(logger, None, None, name, "tun")

    if name in ipdb.by_name.keys():
        interface = ipdb.interfaces[name]

        if interface.kind not in IF_TYPES:
            raise UnexpectedTypeError(name, interface.kind, str.join("/", IF_TYPES))

        return Tuntap(logger, ipdb, interface, name, interface.kind)
    else:
        raise NotFoundError(name, str.join("/", IF_TYPES), True)


def create(dry_run, logger, ipdb, name,
        mode="tap", uid=0, gid=0, ifr=None):
    '''
    Create a tuntap interface object, using a given interface name.
    '''

    logger.debug("creating %s interface '%s'" % (mode, name))

    if dry_run:
        return Tuntap(logger, None, None, name, mode)

    if name in ipdb.by_name.keys():
        interface = ipdb.interfaces[name]

        if (interface.kind not in IF_TYPES or
                interface.uid != uid or
                interface.gid != gid or
                interface.ifr != ifr):
            Interface(None, ipdb, interface, name).remove()
        else:
            return Tuntap(logger, ipdb, interface, name, mode)

    interface = ipdb.create(
        ifname=name,
        kind="tuntap",
        mode=mode,
        uid=uid,
        gid=gid,
        ifr=ifr,
    )
    ipdb.commit()

    return Tuntap(logger, ipdb, interface, name, mode)
