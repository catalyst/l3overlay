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
import subprocess

import pyroute2.netns

import pyroute2.netns.process.proxy

from l3overlay import util

from l3overlay.util.worker import Worker


class NetNS(Worker):
    '''
    Wrapper around pyroute2 network interface, to provide
    convenient functions.
    '''

    def __init__(self, dry_run, logger, name):
        '''
        Set up network namespace internal fields.
        '''

        super().__init__()

        self.dry_run = dry_run

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

        if not self.dry_run:
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

        if not self.dry_run:
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

        if not self.dry_run:
            pyroute2.netns.remove(self.name)

        self.set_removed()


    def Popen(self, *argv, **kwarg):
        '''
        Start a process in this network namespace using the Popen interface.
        '''

        if not self.is_started():
            raise RuntimeError("network namespace '%s' not yet started" % self.name)

        if self.dry_run:
            # Create a dummy NSPopen object with a
            # stub release() method, to be API compatible
            # with the real deal.
            class NSPopen(subprocess.Popen):
                def release(self):
                    pass

            return NSPopen(
                [util.command_path("true")],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            return pyroute2.netns.process.proxy.NSPopen(self.name, *argv, **kwarg)

Worker.register(NetNS)


def get(dry_run, logger, name):
    '''
    Get the network namespace runtime state for the given name, creating it
    if it doesn't exist.
    '''

    return NetNS(dry_run, logger, name)
