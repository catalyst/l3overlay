#
# IPsec overlay network manager (l3overlay)
# l3overlay/l3overlayd/overlay/active_interface/base.py - active interface base class
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
from l3overlay.l3overlayd.network import netns

from l3overlay.l3overlayd.overlay.interface import Interface


class ActiveInterface(Interface):
    '''
    Used to configure an active interface.
    Solely intented to be used for interface cleanup purposes.
    '''

    def __init__(self, logger, name,
            interface_name, netns_name):
        '''
        Set up active interface internal fields.
        '''

        super().__init__(logger, name)

        self.interface_name = interface_name
        self.netns_name = netns_name


    def setup(self, daemon, overlay):
        '''
        Set up static bgp runtime state.
        '''

        super().setup(daemon, overlay)


    def start(self):
        '''
        Starts with the BGP process.
        '''

        pass


    def stop(self):
        '''
        Stops with the BGP process.
        '''

        self.logger.info("stopping active interface '%s'" % self.name)

        # Keep ns undefined in the case of using the root namespace.
        if not self.netns_name:
            ns = None
        # If the given namespace of the active interface is the overlay namespace,
        # use the overlay namespace directly.
        elif self.netns_name == self.netns.name:
            ns = self.netns
        # Start a NetNS object for the specific network namespace specified,
        # if it is not the overlay namespace.
        elif self.netns_name != self.netns.name:
            ns = netns.get(self.dry_run, self.logger, self.netns_name)
            ns.start()

        # Remove the interface, IF it can be found in the appropriate namespace.
        if ((ns and self.interface_name in ns.ipdb.by_name.keys()) or
                (not ns and self.interface_name in self.root_ipdb.by_name.keys())):
            interface.get(
                self.dry_run,
                self.logger,
                self.interface_name,
                ns,
                self.root_ipdb if not self.netns_name else None,
            ).remove()

        # Shutdown the runtime data for the specific network namespace, if it is
        # not the overlay namespace.
        if self.netns_name and self.netns_name != self.netns.name:
            ns.stop()

        self.logger.info("finished stopping active interface '%s'" % self.name)

Interface.register(ActiveInterface)
