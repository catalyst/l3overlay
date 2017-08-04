#
# IPsec overlay network manager (l3overlay)
# l3overlay/l3overlayd/network/interface/__init__.py - network interface functions
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
Network interface functions.
'''


from l3overlay.l3overlayd.network.interface.base import Interface

from l3overlay.l3overlayd.network.interface.exception import GetError
from l3overlay.l3overlayd.network.interface.exception import NotFoundError
from l3overlay.l3overlayd.network.interface.exception import UnexpectedTypeError


IF_DESCRIPTION = "interface"


def log_get(logger, name, description, netns, root_ipdb):
    '''
    Internal helper method to write appropriate logging output
    for network interface 'get' functions.
    '''

    if netns:
        logger.debug("getting runtime state for %s '%s' in %s" %
                     (description, name, netns.description))
    elif root_ipdb:
        logger.debug("getting runtime state for %s '%s' in root namespace" %
                     (description, name))


def log_create(logger, name, description, netns, root_ipdb):
    '''
    Internal helper method to write appropriate logging output
    for network interface 'create' functions.
    '''

    if netns:
        logger.debug("creating %s '%s' in %s" %
                     (description, name, netns.description))
    elif root_ipdb:
        logger.debug("creating %s '%s' in root namespace" %
                     (description, name))


def ipdb_get(name, description, netns, root_ipdb):
    '''
    Get the applicable IPDB for the given interface name,
    determined from one of netns and root_idpb.
    '''

    if netns:
        return netns.ipdb
    elif root_ipdb:
        return root_ipdb
    else:
        raise GetError("netns and root_ipdb unspecified when processing %s '%s'" %
                       (description, name))


def interface_get(name, ipdb, *types):
    '''
    Tries to find an interface with the given name in the
    chosen namespace and returns it.
    '''

    if name not in ipdb.by_name.keys():
        return None

    existing_if = ipdb.interfaces[name]

    if existing_if and types and existing_if.kind not in types:
        raise UnexpectedTypeError(name, existing_if.kind, types)

    return existing_if


def get(dry_run, logger, name, netns=None, root_ipdb=None):
    '''
    Tries to find an interface with the given name in the
    chosen namespace and returns it.
    '''

    log_get(logger, name, IF_DESCRIPTION, netns, root_ipdb)

    if dry_run:
        return Interface(logger, name, None, netns, root_ipdb)

    ipdb = ipdb_get(name, IF_DESCRIPTION, netns, root_ipdb)
    existing_if = interface_get(name, ipdb)

    if existing_if:
        return Interface(logger, name, existing_if, netns, root_ipdb)
    else:
        raise NotFoundError(name, IF_DESCRIPTION, netns, root_ipdb)
