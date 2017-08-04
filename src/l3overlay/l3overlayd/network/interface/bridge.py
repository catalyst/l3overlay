#
# IPsec overlay network manager (l3overlay)
# l3overlay/l3overlayd/network/interface/bridge.py - bridge interface class and functions
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
Bridge interface class and functions.
'''


import time

from l3overlay.l3overlayd.network import interface

from l3overlay.l3overlayd.network.interface.base import Interface

from l3overlay.l3overlayd.network.interface.exception import NotFoundError


IF_TYPE = "bridge"
IF_DESCRIPTION = "%s interface" % IF_TYPE


class Bridge(Interface):
    '''
    Bridge interface class. Subclass of the Interface class, adding
    bridge-specific functions.
    '''

    description = IF_DESCRIPTION


    def add_port(self, added_if):
        '''
        Add the given interface to the list of ports for this bridge.
        '''

        self._check_state()

        if self.logger:
            self.logger.debug("adding port for %s '%s' to %s '%s'" %
                              (added_if.description, added_if.name, self.description, self.name))

        if self.interface:

            # GRE interfaces are a layer 3 interface. GRETAP interfaces are fine, though.
            if "kind" in added_if.interface and added_if.interface["kind"] == "gre":
                raise RuntimeError("unable to add gre interface '%s' to bridge interface '%s'" %
                                   (added_if.name, self.name))

            if added_if.interface.index not in self.interface.ports:
                self.interface.add_port(added_if.interface).commit()

                # FIXME: get rid of this workaround of pyroute2 issue #280
                # once it is fixed.
                #
                # https://github.com/svinota/pyroute2/issues/280
                if self.interface.mtu > added_if.interface.mtu:
                    waited = 0.0
                    while self.interface.mtu != added_if.interface.mtu and waited < 10.0:
                        waited += 0.001
                        time.sleep(0.001)
                    assert self.interface.mtu == added_if.interface.mtu


def get(dry_run, logger, name, netns=None, root_ipdb=None):
    '''
    Tries to find a bridge interface with the given name in the
    chosen namespace and returns it.
    '''

    interface.log_get(logger, name, IF_DESCRIPTION, netns, root_ipdb)

    if dry_run:
        return Bridge(logger, name, None, netns, root_ipdb)

    ipdb = interface.ipdb_get(name, IF_DESCRIPTION, netns, root_ipdb)
    existing_if = interface.interface_get(name, ipdb, IF_TYPE)

    if existing_if:
        return Bridge(logger, name, existing_if, netns, root_ipdb)
    else:
        raise NotFoundError(name, IF_DESCRIPTION, netns, root_ipdb)


def create(dry_run, logger, name, netns=None, root_ipdb=None):
    '''
    Create a bridge interface object, using a given interface name.
    '''

    interface.log_create(logger, name, IF_DESCRIPTION, netns, root_ipdb)

    if dry_run:
        return Bridge(logger, name, None, netns, root_ipdb)

    ipdb = interface.ipdb_get(name, IF_DESCRIPTION, netns, root_ipdb)
    existing_if = interface.interface_get(name, ipdb)

    # Always remove any existing interfaces with the given name.
    # Even if it is already a bridge, it could have ports attached
    # to it already. Ideally, this function should be idempotent, but
    # it's not really possible for bridges.
    if existing_if:
        Interface(None, name, existing_if, netns, root_ipdb).remove()

    new_if = ipdb.create(ifname=name, kind=IF_TYPE)
    ipdb.commit()

    return Bridge(logger, name, new_if, netns, root_ipdb)
