#
# IPsec overlay network manager (l3overlay)
# l3overlay/network/interface/veth.py - veth pair interface class and functions
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


IF_TYPE = "veth"


class VETH(Interface):
    '''
    veth pair interface class. Subclass of the Interface class, adding
    veth-specific functions.
    '''

    description = "%s interface" % IF_TYPE


def get(dry_run, logger, ipdb, name):
    '''
    Return a veth interface object for the given interface name.
    '''

    logger.debug("getting runtime state for %s interface '%s'" % (IF_TYPE, name))

    if dry_run:
        return VETH(logger, ipdb, name)

    if name in ipdb.by_name.keys():
        interface = ipdb.interfaces[name]

        if interface.kind != IF_TYPE:
            raise UnexpectedTypeError(name, interface.kind, IF_TYPE)

        return VETH(logger, ipdb, name)
    else:
        raise NotFoundError(name, IF_TYPE, True)


def create(dry_run, logger, ipdb, name, peer_name):
    '''
    Create a veth pair interface object, using a given interface name.
    '''

    logger.debug("creating %s pair '%s' and '%s'" % (IF_TYPE, name, peer_name))

    if dry_run:
        return VETH(logger, None, name)

    if name in ipdb.by_name.keys():
        interface = ipdb.interfaces[name]
        if interface.kind != IF_TYPE or interface.peer != peer_name:
            Interface(None, ipdb, name).remove()
    else:
        ipdb.create(ifname=name, kind="veth", peer=peer_name)
        ipdb.commit()

    return VETH(logger, ipdb, name)
