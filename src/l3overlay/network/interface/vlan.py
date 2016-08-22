#
# IPsec overlay network manager (l3overlay)
# l3overlay/network/interface/vlan.py - vlan interface class and functions
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


IF_TYPE = "vlan"


class VLAN(Interface):
    '''
    VLAN interface class. Subclass of the Interface class, adding
    VLAN-specific functions.
    '''

    def __init__(self, logger, ipdb, interface, name, link, id):
        '''
        Set up vlan interface internal fields.
        '''

        super().__init__(logger, ipdb, interface, name)

        self.link = link
        self.id = id

        self.description = "%s interface" % IF_TYPE


def get(dry_run, logger, ipdb, name):
    '''
    Return a vlan interface object for the given interface name.
    '''

    logger.debug("getting runtime state for %s interface '%s'" % (IF_TYPE, name))

    if dry_run:
        return VLAN(logger, ipdb, None, name, None, None)

    if name in ipdb.by_name.keys():
        interface = ipdb.interfaces[name]

        if interface.kind != IF_TYPE:
            raise UnexpectedTypeError(name, interface.kind, IF_TYPE)

        return VLAN(ipdb, interface, name, interface.peer)
    else:
        raise NotFoundError(name, IF_TYPE, True)


def create(dry_run, logger, ipdb, name, link, id):
    '''
    Create a vlan interface object, using a given interface name.
    '''

    logger.debug("creating %s interface '%s'" % (IF_TYPE, name))


    if dry_run:
        return VLAN(logger, ipdb, None, name, link, id)

    if name in ipdb.by_name.keys():
        interface = ipdb.interfaces[name]

        if (interface.kind != IF_TYPE or
                ipdb.by_index[interface.link] != link or
                interface.vlan_id != id):
            Interface(None, ipdb, interface, name).remove()
        else:
            return VLAN(logger, ipdb, interface, name, interface.link, interface.id)

    interface = ipdb.create(ifname=name, kind=IF_TYPE, link=link, vlan_id=id)
    ipdb.commit()

    return VLAN(ipdb, interface, name, link, id)
