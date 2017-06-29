#
# IPsec overlay network manager (l3overlay)
# l3overlay/overlay/active_interface/base.py - active interface base class
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


from l3overlay.overlay.interface import Interface


class ActiveInterface(Interface):
    '''
    Used to configure an active interface.
    Solely intented to be used for interface cleanup purposes.
    '''

    def __init__(self, logger, name,
            interface_name, use_rootns):
        '''
        Set up active interface internal fields.
        '''

        super().__init__(logger, name)

        self.interface_name = interface_name
        self.use_rootns = use_rootns


    def setup(self, daemon, overlay):
        '''
        Set up static bgp runtime state.
        '''

        self.set_settingup()
        super().setup(daemon, overlay)
        self.set_setup()


    def start(self):
        '''
        Starts with the BGP process.
        '''

        self.set_starting()
        self.set_started()


    def stop(self):
        '''
        Stops with the BGP process.
        '''

        self.set_stopping()
        interface.get(
            self.dry_run,
            self.logger,
            self.interface_name,
            self.netns_name if self.netns_name else None,
            self.root_netns if not self.netns_name else None,
        ).remove()
        self.set_stopped()

Interface.register(ActiveInterface)
