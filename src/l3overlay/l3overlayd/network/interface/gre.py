#
# IPsec overlay network manager (l3overlay)
# l3overlay/l3overlayd/network/interface/gre.py - gre/gretap interface class and functions
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
GRE/GRETAP interface class and functions.
'''


from l3overlay.l3overlayd.network import interface

from l3overlay.l3overlayd.network.interface.base import Interface

from l3overlay.l3overlayd.network.interface.exception import NotFoundError


IF_TYPES = ["gre", "gretap"]


class GRE(Interface):
    '''
    GRE tunnel interface class. Subclass of the Interface class, adding
    GRE tunnel-specific functions.
    '''

    # pylint: disable=too-many-arguments
    def __init__(self, logger, name, inter, netns, root_ipdb, kind):
        '''
        '''

        super().__init__(logger, name, inter, netns, root_ipdb)

        self.description = "%s interface" % kind



# pylint: disable=too-many-arguments
def get(dry_run, logger, name, kind, netns=None, root_ipdb=None):
    '''
    Tries to find a gre/gretap interface with the given name in the
    chosen namespace and returns it.
    '''

    description = "%s interface" % kind

    interface.log_get(logger, name, description, netns, root_ipdb)

    if dry_run:
        return GRE(logger, name, None, netns, root_ipdb, kind)

    ipdb = interface.ipdb_get(name, description, netns, root_ipdb)
    existing_if = interface.interface_get(name, ipdb, kind)

    if existing_if:
        return GRE(logger, name, existing_if, netns, root_ipdb, kind)
    else:
        raise NotFoundError(name, kind, netns, root_ipdb)


def create(dry_run, logger, name, kind,
           # for other parameters, look in pyroute2/netlink/rtnl/ifinfmsg.py
           local, remote, link=None, iflags=32, oflags=32, key=None, ikey=None, okey=None, ttl=16,
           netns=None, root_ipdb=None):
    '''
    Create a gre/gretap interface object, using a given interface name.
    '''

    # pylint: disable=too-many-locals

    description = "%s interface" % kind

    interface.log_create(logger, name, description, netns, root_ipdb)

    if dry_run:
        return GRE(logger, name, None, netns, root_ipdb, kind)

    ipdb = interface.ipdb_get(name, description, netns, root_ipdb)
    existing_if = interface.interface_get(name, ipdb)

    if key is not None:
        ikey = key
        okey = key

    if existing_if:
        # pylint: disable=too-many-boolean-expressions
        if (existing_if.kind != kind or
                existing_if.gre_local != str(local) or
                existing_if.gre_remote != str(remote) or
                existing_if.gre_link != link or
                existing_if.gre_iflags != iflags or
                existing_if.gre_oflags != oflags or
                existing_if.gre_ikey != ikey or
                existing_if.gre_okey != okey or
                existing_if.gre_ttl != ttl):
            logger.debug("removing interface '%s'" % name)
            Interface(None, name, existing_if, netns, root_ipdb).remove()
        else:
            return GRE(logger, name, existing_if, netns, root_ipdb, kind)

    new_if = ipdb.create(
        ifname=name,
        kind=kind,
        gre_local=str(local),
        gre_remote=str(remote),
        gre_link=link,
        gre_iflags=iflags,
        gre_oflags=oflags,
        gre_ikey=ikey,
        gre_okey=okey,
        gre_ttl=ttl,
    )
    ipdb.commit()

    return GRE(logger, name, new_if, netns, root_ipdb, kind)
