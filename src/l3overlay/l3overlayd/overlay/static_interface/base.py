#
# IPsec overlay network manager (l3overlay)
# l3overlay/l3overlayd/overlay/interface/static_interface/base.py - static interface base class
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


import abc

from l3overlay.l3overlayd.overlay.interface import Interface


class StaticInterface(Interface):
    '''
    Abstract base class for an overlay static interface.
    '''


    @abc.abstractmethod
    def is_ipv6(self):
        '''
        Returns True if this static interface has an IPv6 address
        assigned to it.
        '''

        raise NotImplementedError()


    @abc.abstractmethod
    def active_interfaces(self):
        '''
        Return an iterable of ActiveInterface objects representing the
        physical interfaces this static interface uses.
        '''

        raise NotImplementedError()
