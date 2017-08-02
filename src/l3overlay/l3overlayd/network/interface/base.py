#
# IPsec overlay network manager (l3overlay)
# l3overlay/l3overlayd/network/interface/base.py - network interface base class
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


import time

from l3overlay.l3overlayd.network.interface.exception import NotRemovedError
from l3overlay.l3overlayd.network.interface.exception import RemovedThenModifiedError


REMOVE_WAIT_MAX = 1.0
REMOVE_WAIT_PERIOD = 0.001


class Interface(object):
    '''
    Network interface base class.
    '''

    description = "interface"


    def __init__(self, logger, name, interface, netns, root_ipdb):
        '''
        Set up network interface internal fields and runtime state.
        '''

        self.logger = logger
        self.name = name

        self.interface = interface

        self.netns = netns
        self.root_ipdb = root_ipdb
        self.ipdb = self.netns.ipdb if self.netns else self.root_ipdb

        self.removed = False


    def _check_state(self):
        '''
        Check interface internal state.
        '''

        if self.removed:
            raise RemovedThenModifiedError(self)


    def add_ip(self, address, netmask):
        '''
        Add the given IP address (either a string, IPv4Address or IPv6Address)
        with its netmask to the chosen interface.
        '''

        self._check_state()

        if self.logger:
            self.logger.debug("assigning IP address '%s/%i' to %s '%s'" % (str(address), netmask, self.description, self.name))

        ip_tuple = (str(address), netmask)
        ip_string = "%s/%i" % ip_tuple

        if self.interface and ip_tuple not in self.interface.ipaddr:
            self.interface.add_ip(ip_string).commit()


    def set_mtu(self, mtu):
        '''
        Set the maximum transmission unit size on the chosen interface.
        '''


        self._check_state()

        if self.logger:
            self.logger.debug("setting MTU to %i on %s '%s'" % (mtu, self.description, self.name))

        if self.interface:
            self.interface.set_mtu(mtu).commit()


    def netns_set(self, netns):
        '''
        Move the interface into a chosen network namespace.
        '''

        self._check_state()

        if self.logger:
            self.logger.debug("moving %s '%s' to %s" %
                    (self.description, self.name, netns.description))

        if self.interface:
            if self.netns == netns:
                return

            if self.name in netns.ipdb.by_name.keys():
                if self.logger:
                    self.logger.debug("removing existing interface with name '%s' in %s" %
                            (self.name, netns.description))
                netns.interface_get(self.name).remove()

            self.interface.net_ns_fd = netns.name
            self.ipdb.commit()

            # Busy wait in this thread until the moved interface appears in the
            # new namespace. Apparently needed to overcome a race condition
            # between moving an interface to a new netns and the ipdb noticing
            # the change in this thread.
            # TODO: create a pyroute2 issue for this?
            if self.name not in netns.ipdb.interfaces:
                waited = 0.0
                while self.name not in netns.ipdb.interfaces and waited < 10.0:
                    waited += 0.001
                    time.sleep(0.001)
                assert self.name in netns.ipdb.interfaces

            self.root_ipdb = None

            self.netns = netns
            self.ipdb = self.netns.ipdb
            self.interface = self.ipdb.interfaces[self.name]


    def root_ipdb_set(self, root_ipdb):
        '''
        Move the interface into the root namespace, indexing using the given
        root_ipdb.
        '''

        self._check_state()

        if self.logger:
            self.logger.debug("moving %s '%s' to root namespace" % (self.description, self.name))

        if self.interface:
            if self.root_ipdb:
                return

            self.interface.net_ns_fd = None
            self.ipdb.commit()

            self.netns = None

            self.root_ipdb = root_ipdb
            self.ipdb = self.root_ipdb
            self.interface = self.ipdb.interfaces[self.name]


    def up(self):
        '''
        Bring up the given interface.
        '''

        self._check_state()

        if self.logger:
            self.logger.debug("bringing up %s '%s'" % (self.description, self.name))

        if self.interface:
            self.interface.up().commit()


    def down(self):
        '''
        Bring up the interface.
        '''

        self._check_state()

        if self.logger:
            self.logger.debug("bringing down %s '%s'" % (self.description, self.name))

        if self.interface:
            self.interface.down().commit()


    def remove(self):
        '''
        Remove the interface, and mark it so this interface can no longer be
        interacted with.
        '''

        self._check_state()

        if self.logger:
            self.logger.debug("removing %s '%s'" % (self.description, self.name))

        if self.interface:
            waited = 0.0

            self.interface.down()
            self.interface.remove().commit()

            # pyroute2 seems to take a little while to actually execute
            # an interface removal. Wait for the IPDB to register that the
            # interface no longer exists.
            # This stops waiting after a while, to prevent infinite loops.
            while waited < REMOVE_WAIT_MAX:
                if self.name not in self.ipdb.by_name.keys():
                    self.removed = True
                    break
                time.sleep(REMOVE_WAIT_PERIOD)
                waited += REMOVE_WAIT_PERIOD

            if not self.removed:
                raise NotRemovedError(self)

        else:
            self.removed = True
