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

import pyroute2.netns

import pyroute2.netns.process.proxy

from l3overlay.util.worker import Worker


class NetNS(Worker):
    '''
    Wrapper around pyroute2 network interface, to provide
    convenient functions.
    '''

    def __init__(self, logger, name):
        '''
        '''

        super().__init__()

        self.logger = logger
        self.name = name

        self.netns = None
        self.ipdb = None


    def start(self):
        '''
        Start the network namespace object, and create the network
        namespace if it doesn't exist.
        '''

        if self.is_starting() or self.is_started():
            raise RuntimeError("Network namespace '%s' started twice" % self.name)

        self.set_starting()

        self.logger.debug("starting network namespace '%s'" % self.name)

        if self.name not in pyroute2.netns.listnetns():
            try:
                pyroute2.netns.create(self.name)
            except FileExistsError:
                # Network namespace already exists
                pass
            except:
                raise RuntimeError("unable to create network namespace: %s" % self.name)

        self.netns = pyroute2.NetNS(self.name)
        self.ipdb = pyroute2.IPDB(nl=self.netns)

        if not self.netns:
            raise RuntimeError("not netns")

        if not self.ipdb:
            raise RuntimeError("not ipdb")

        self.set_started()


    def stop(self):
        '''
        Stop the network namespace object.
        '''

        if not self.is_started():
            raise RuntimeError("network namespace '%s' not yet started" % self.name)

        if self.is_stopped() or self.is_stopped():
            raise RuntimeError("network namespace '%s' stopped twice" % self.name)

        self.set_stopping()

        self.logger.debug("stopping network namespace '%s'" % self.name)
        self.ipdb.release()
        self.netns.close()

        self.set_stopped()


    def remove(self):
        '''
        Remove a network namespace from the system.
        '''

        if self.is_started():
            raise RuntimeError("network namespace '%s' still running, stop before removing" % self.name)

        if self.is_removing() or self.is_removed():
            raise RuntimeError("cannot remove NetNS a second time: %s" % self.name)

        self.set_removing()

        self.logger.debug("removing network namespace '%s'" % self.name)
        pyroute2.netns.remove(self.name)

        self.set_removed()


    def Popen(self, *argv, **kwarg):
        '''
        Start a process in this network namespace using the Popen interface.
        '''

        if not self.is_started():
            raise RuntimeError("network namespace '%s' not yet started" % self.name)

        return pyroute2.netns.process.proxy.NSPopen(self.name, *argv, **kwarg)

Worker.register(NetNS)


def get(logger, name):
    '''
    Get the network namespace runtime state for the given name, creating it
    if it doesn't exist.
    '''

    return NetNS(logger, name)
