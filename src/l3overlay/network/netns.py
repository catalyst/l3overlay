#
# IPsec overlay network manager (l3overlay)
# l3overlay/network/netns.py - network namespace functions
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


import pyroute2

from pyroute2 import IPDB
from pyroute2 import netns
from pyroute2 import NetNS


class NetNS():
    '''
    Wrapper around pyroute2 network interface, to provide
    convenient functions.
    '''

    def __init__(self, netns, ipdb, name):
        '''
        '''

        self.netns = netns
        self.ipdb = ipdb
        self.name = name

        self._closed = False
        self._removed = False


    def close(self):
        '''
        Close the network namespace runtime state.
        '''

        if self._removed:
            raise RuntimeError("cannot close NetNS after it has been removed: %s" % self.name)

        if self._closed:
            raise RuntimeError("cannot close NetNS a second time: %s" % self.name)

        self.ipdb.release()
        self.netns.close()

        self._closed = True


    def remove(self):
        '''
        Remove a network namespace from the system.
        '''

        if self._removed:
            raise RuntimeError("cannot remove NetNS a second time: %s" % self.name)

        self.close()
        pyroute2.netns.remove(name)

        self._removed = True


def get(name, create=False):
    '''
    Check if a network namespace exists, and return a tuple containing its
    NetNS and IPDB objects. If optional parameter create is true, create the
    network namespacfe if it doesn't exist, otherwise, raise a RuntimeError if
    it doesn't exist.
    '''

    if name not in pyroute2.netns.listnetns():
        if create:
            try:
                pyroute2.netns.create(name)
            except FileExistsError:
                # Network namespace already exists
                pass
            except:
                raise RuntimeError("unable to create network namespace: %s" % name)
        else:
            raise RuntimeError("no existing network namespace: %s" % name)

    netns = pyroute2.NetNS(name)
    ipdb = pyroute2.IPDB(nl=netns)

    return NetNS(netns, ipdb, name)


def create(name):
    '''
    Get the network namespace runtime state for the given name, creating it
    if it doesn't exist.
    '''

    return get(name, create=True)
