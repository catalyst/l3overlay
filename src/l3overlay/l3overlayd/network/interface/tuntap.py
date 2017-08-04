#
# IPsec overlay network manager (l3overlay)
# l3overlay/l3overlayd/network/interface/tuntap.py - tun/tap interface class and functions
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
tun/tap interface class and functions.
'''


from l3overlay.l3overlayd.network import interface

from l3overlay.l3overlayd.network.interface.base import Interface

from l3overlay.l3overlayd.network.interface.exception import NotFoundError


IF_TYPES = ["tun", "tap"]


class Tuntap(Interface):
    '''
    TUN/TAP interface class. Subclass of the Interface class, adding
    TUN/TAP interface-specific functions.
    '''

    # pylint: disable=too-many-arguments
    def __init__(self, logger, name, inter, netns, root_ipdb, mode):
        '''
        '''

        super().__init__(logger, name, inter, netns, root_ipdb)

        self.description = "%s interface" % mode


# pylint: disable=too-many-arguments
def get(dry_run, logger, name, mode, netns=None, root_ipdb=None):
    '''
    Tries to find a tun/tap interface with the given name in the
    chosen namespace and returns it.
    '''

    description = "%s interface" % mode

    interface.log_get(logger, name, description, netns, root_ipdb)

    if dry_run:
        return Tuntap(logger, name, None, netns, root_ipdb, mode)

    ipdb = interface.ipdb_get(name, description, netns, root_ipdb)
    existing_if = interface.interface_get(name, ipdb, mode)

    if existing_if:
        return Tuntap(logger, name, existing_if, netns, root_ipdb, mode)
    else:
        raise NotFoundError(name, mode, netns, root_ipdb)


# pylint: disable=too-many-arguments
def create(dry_run, logger, name, mode,
           uid=0, gid=0, ifr=None,
           netns=None, root_ipdb=None):
    '''
    Create a tun/tap interface object, using a given interface name.
    '''

    description = "%s interface" % mode

    interface.log_create(logger, name, description, netns, root_ipdb)

    if dry_run:
        return Tuntap(logger, name, None, netns, root_ipdb, mode)

    ipdb = interface.ipdb_get(name, description, netns, root_ipdb)
    existing_if = interface.interface_get(name, ipdb)

    if existing_if:
        if (existing_if.kind != mode or
                existing_if.uid != uid or
                existing_if.gid != gid or
                existing_if.ifr != ifr):
            Interface(None, name, existing_if, netns, root_ipdb).remove()
        else:
            return Tuntap(logger, name, existing_if, netns, root_ipdb, mode)

    new_if = ipdb.create(
        ifname=name,
        kind="tuntap",
        mode=mode,
        uid=uid,
        gid=gid,
        ifr=ifr,
    )
    ipdb.commit()

    return Tuntap(logger, name, new_if, netns, root_ipdb, mode)
