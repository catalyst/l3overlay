#
# IPsec overlay network manager (l3overlay)
# l3overlay/l3overlayd/network/interface/veth.py - veth pair interface class and functions
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


from l3overlay.l3overlayd.network import interface

from l3overlay.l3overlayd.network.interface.base import Interface

from l3overlay.l3overlayd.network.interface.exception import NotFoundError


IF_TYPE = "veth"
IF_DESCRIPTION = "%s interface" % IF_TYPE


class VETH(Interface):
    '''
    veth pair interface class. Subclass of the Interface class, adding
    veth-specific functions.
    '''

    description = IF_DESCRIPTION


    def __init__(self, logger, name, interface, netns, root_ipdb, peer):
        '''
        '''

        super().__init__(logger, name, interface, netns, root_ipdb)

        self.peer = peer


    def peer_get(self, peer_netns=None, peer_root_ipdb=None):
        '''
        Get the peer interface for this veth interface, if it is in the
        same namespace. Return None if this is not the case.
        '''

        if self.interface:
            if self.peer in self.ipdb.by_name.keys():
                if self.logger:
                    self.logger.debug("getting %s '%s' peer '%s' in %s" % (
                        self.description,
                        self.name,
                        self.peer,
                        self.netns.description if self.netns else "root namespace",
                    ))
                return VETH(
                    self.logger,
                    self.peer,
                    self.ipdb.interfaces[self.peer],
                    self.netns,
                    self.root_ipdb,
                    self.name,
                )

            elif peer_netns and self.peer in peer_netns.ipdb.by_name.keys():
                if self.logger:
                    self.logger.debug("getting %s '%s' peer '%s' in remote %s" % (
                        self.description,
                        self.name,
                        self.peer,
                        self.netns.description,
                    ))
                return VETH(
                    self.logger,
                    self.peer,
                    peer_netns.ipdb.interfaces[self.peer],
                    peer_netns,
                    None,
                    self.name,
                )

            elif peer_root_ipdb and self.peer in peer_root_ipdb.by_name.keys():
                if self.logger:
                    self.logger.debug("getting %s '%s' peer '%s' in remote root namespace'" % (
                        self.description,
                        self.name,
                        self.peer,
                    ))
                return VETH(
                    self.logger,
                    self.peer,
                    peer_root_ipdb.interfaces[self.peer],
                    None,
                    peer_root_ipdb,
                    self.name,
                )

        # dry-run = true
        else:
            if self.logger:
                self.logger.debug("getting %s '%s' peer '%s' in %s" % (
                    self.description,
                    self.name,
                    self.peer,
                    self.netns.description if self.netns else "root namespace",
                ))
            return VETH(
                self.logger,
                self.peer,
                None,
                self.netns,
                self.root_ipdb,
                self.name,
            )


def get(dry_run, logger, name, peer, netns=None, root_ipdb=None):
    '''
    Tries to find a veth interface with the given name in the
    chosen namespace and returns it.
    '''

    interface._log_get(logger, name, IF_DESCRIPTION, netns, root_ipdb)

    if dry_run:
        return VETH(logger, name, None, netns, root_ipdb, peer)

    ipdb = interface._ipdb_get(name, IF_DESCRIPTION, netns, root_ipdb)
    existing_if = interface._interface_get(name, ipdb, IF_TYPE)

    if existing_if:
        return VETH(logger, name, existing_if, netns, root_ipdb, peer)
    else:
        raise NotFoundError(name, IF_DESCRIPTION, netns, root_ipdb)


def create(dry_run, logger, name, peer, netns=None, root_ipdb=None):
    '''
    Create a veth interface object, using a given interface name.
    '''

    interface._log_create(logger, name, IF_DESCRIPTION, netns, root_ipdb)

    if dry_run:
        return VETH(logger, name, None, netns, root_ipdb, peer)

    ipdb = interface._ipdb_get(name, IF_DESCRIPTION, netns, root_ipdb)
    existing_if = interface._interface_get(name, ipdb)

    if existing_if:
        if existing_if.kind != IF_TYPE or existing_if.peer != peer:
            Interface(None, name, existing_if, netns, root_ipdb).remove()
        else:
            return VETH(logger, name, existing_if, netns, root_ipdb, peer)

    new_if = ipdb.create(ifname=name, kind=IF_TYPE, peer=peer)
    ipdb.commit()

    return VETH(logger, name, new_if, netns, root_ipdb, peer)
