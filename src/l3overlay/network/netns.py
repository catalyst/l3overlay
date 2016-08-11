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

from l3overlay.util import Worker


class NetNS(Worker):
    '''
    Wrapper around pyroute2 network interface, to provide
    convenient functions.
    '''

    def __init__(self, name):
        '''
        '''

        self().__init__()

        self.name = name

        self.netns = None
        self.ipdb = None


    def start(self):
        '''
        Start the network namespace object, and create the network
        namespace if it doesn't exist.
        '''

        if self.starting() or self.running():
            raise RuntimeError("Network namespace '%s' started twice" % name)

        self.set_starting()

        if name not in pyroute2.netns.listnetns():
            try:
                pyroute2.netns.create(name)
            except FileExistsError:
                # Network namespace already exists
                pass
            except:
                raise RuntimeError("unable to create network namespace: %s" % name)

        self.netns = pyroute2.NetNS(name)
        self.ipdb = pyroute2.IPDB(nl=netns)


    def close(self):
        '''
        Stop the network namespace object.
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


    def Popen(self, *argv, **kwarg):
        '''
        Start a process in this network namespace using the Popen interface.
        '''

        return pyroute.netns.process.proxy.NSPopen(self.name, *argv, **kwarg)

Worker.register(NetNS)


def get(name):
    '''
    Get the network namespace runtime state for the given name, creating it
    if it doesn't exist.
    '''

    return NetNS(name)
