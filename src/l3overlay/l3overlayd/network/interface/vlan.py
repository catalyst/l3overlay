#
# IPsec overlay network manager (l3overlay)
# l3overlay/l3overlayd/network/interface/vlan.py - vlan interface class and functions
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
VLAN interface class and functions.
'''


from l3overlay.l3overlayd.network import interface

from l3overlay.l3overlayd.network.interface.base import Interface

from l3overlay.l3overlayd.network.interface.exception import NotFoundError


IF_TYPE = "vlan"
IF_DESCRIPTION = "%s interface" % IF_TYPE


class VLAN(Interface):
    '''
    VLAN interface class. Subclass of the Interface class, adding
    VLAN-specific functions.
    '''

    description = IF_DESCRIPTION


def get(dry_run, logger, name, netns=None, root_ipdb=None):
    '''
    Tries to find a vlan interface with the given name in the
    chosen namespace and returns it.
    '''

    interface.log_get(logger, name, IF_DESCRIPTION, netns, root_ipdb)

    if dry_run:
        return VLAN(logger, name, None, netns, root_ipdb)

    ipdb = interface.ipdb_get(name, IF_DESCRIPTION, netns, root_ipdb)
    existing_if = interface.interface_get(name, ipdb, IF_TYPE)

    if existing_if:
        return VLAN(logger, name, existing_if, netns, root_ipdb)
    else:
        raise NotFoundError(name, IF_DESCRIPTION, netns, root_ipdb)


# pylint: disable=too-many-arguments
def create(dry_run, logger, name, link, vlan_id, netns=None, root_ipdb=None):
    '''
    Create a vlan interface object, using a given interface name.
    '''

    interface.log_create(logger, name, IF_DESCRIPTION, netns, root_ipdb)

    if dry_run:
        return VLAN(logger, name, None, netns, root_ipdb)

    ipdb = interface.ipdb_get(name, IF_DESCRIPTION, netns, root_ipdb)
    existing_if = interface.interface_get(name, ipdb)

    if existing_if:
        if (existing_if.kind != IF_TYPE or
                ipdb.by_index[existing_if.link] != link or
                existing_if.vlan_id != vlan_id):
            Interface(None, name, existing_if, netns, root_ipdb).remove()
        else:
            return VLAN(logger, name, existing_if, netns, root_ipdb)

    new_if = ipdb.create(ifname=name, kind=IF_TYPE, link=link.interface, vlan_id=vlan_id)
    ipdb.commit()

    return VLAN(logger, name, new_if, netns, root_ipdb)
