#
# IPsec overlay network manager (l3overlay)
# l3overlay/network/interface/__init__.py - network interface base class and functions
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


import time

from l3overlay.util.exception.l3overlayerror import L3overlayError


REMOVE_WAIT_MAX = 1.0
REMOVE_WAIT_PERIOD = 0.001


class RemovedThenModifiedError(L3overlayError):
    def __init__(self, interface):
        super().__init__("%s '%s' removed and then modified" %
                (interface.description, interface.name))

class NotRemovedError(L3overlayError):
    def __init__(self, interface):
        super().__init__(
            "%s '%s' still exists even after waiting %s second%s for removal" %
                    (
                        interface.description,
                        interface.name,
                        REMOVE_WAIT_MAX,
                        "s" if REMOVE_WAIT_MAX != 1.0 else "",
                    ))

class NotFoundError(L3overlayError):
    def __init__(self, name, kind = None, netns = False):
        super().__init__("unable to find %s with name '%s' in %s namespace" %
                (
                    name,
                    kind if kind else "interface",
                    "network" if netns else "root",
                ))

class UnexpectedTypeError(L3overlayError):
    def __init__(self, name, kind, expected_kind):
        super().__init__(
            "found interface with name '%s' of kind '%s', expected '%s'" %
                    (name, kind, expected_kind))

class Interface(object):
    '''
    '''

    description = "interface"


    def __init__(self, logger, ipdb, interface, name):
        '''
        Set up network interface internal fields and runtime state.
        '''

        self.logger = logger

        self.ipdb = ipdb
        self.interface = interface
        self.name = name

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


    def netns_set(netns):
        '''
        Move the interface into a chosen network namespace.
        '''


        self._check_state()

        if self.logger:
            self.logger.debug("moving %s '%s' to network namespace '%s'" % (self.description, self.name, netns.name))

        if self.interface and self.name not in netns.ipdb.by_name.keys():
            self.interface.net_ns_fd = netns.name
            self.ipdb.commit()

        self.ipdb = netns.ipdb


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


def get(dry_run, logger, ipdb, name):
    '''
    Tries to find an interface with the given name in the chosen IPDB
    and returns it. Throws a RuntimeError if it can't find it.
    '''

    logger.debug("getting runtime state for interface '%s'" % name)

    if dry_run:
        return Interface(logger, ipdb, None, name)

    if name in ipdb.by_name.keys():
        return Interface(logger, ipdb, ipdb.interfaces[name], name)
    else:
        raise NotFoundError(name)


def netns_set(dry_run, logger, ipdb, name, netns):
    '''
    Moves an interface into a chosen network namespace. Returns the
    interface object from the network namespace.
    '''

    logger.debug("moving interface '%s' to network namespace '%s'" % (name, netns.name))

    if dry_run:
        return Interface(logger, netns.ipdb, None, name)

    if name not in netns.ipdb.by_name.keys():
        ipdb.interfaces[name].net_ns_fd = netns.name
        ipdb.commit()

    return Interface(logger, netns.ipdb, netns.ipdb.interfaces[name], name)
