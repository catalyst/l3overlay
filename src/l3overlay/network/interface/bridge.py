#
# IPsec overlay network manager (l3overlay)
# l3overlay/network/interface/bridge.py - bridge interface class and functions
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


IF_TYPE = "bridge"


class Bridge(Interface):
    '''
    Bridge interface class. Subclass of the Interface class, adding
    bridge-specific functions.
    '''

    description = "%s interface" % IF_TYPE


    def add_port(self, added_if):
        '''
        Add the given interface to the list of ports for this bridge.
        '''

        self._check_state()

        if self.logger:
            self.logger.debug("adding port for %s '%s' to %s '%s'" %
                    (added_if.description, added_if.name, self.description, self.name))

        if self.interface and added_if.interface.index not in self.interface.ports:
            self.interface.add_port(added_if.interface).commit()


def get(dry_run, logger, ipdb, name):
    '''
    Return a bridge interface object for the given interface name.
    '''

    logger.debug("getting runtime state for %s interface '%s'" % (IF_TYPE, name))

    if dry_run:
        return Bridge(logger, ipdb, None, name)

    if name in ipdb.by_name.keys():
        interface = ipdb.interfaces[name]

        if interface.kind != IF_TYPE:
            raise UnexpectedTypeError(name, interface.kind, IF_TYPE)

        return Bridge(logger, ipdb, interface, name)
    else:
        raise NotFoundError(name, IF_TYPE, True)


def create(dry_run, logger, ipdb, name):
    '''
    Create a bridge interface object, using a given interface name.
    '''

    logger.debug("creating %s interface '%s'" % (IF_TYPE, name))

    if dry_run:
        return Bridge(logger, ipdb, None, name)

    # Remove any existing interfaces with the given name. It could have
    # ports attached to it already.
    if name in ipdb.by_name.keys():
        Interface(None, ipdb, ipdb.interfaces[name], name).remove()

    interface = ipdb.create(ifname=name, kind=IF_TYPE)
    ipdb.commit()

    return Bridge(logger, ipdb, interface, name)
