#
# IPsec overlay network manager (l3overlay)
# l3overlay/l3overlayd/network/interface/exception.py - network interface exception classes
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
Network interface exception classes.
'''


from l3overlay.util.exception import L3overlayError


REMOVE_WAIT_MAX = 5.0


class GetError(L3overlayError):
    '''
    Interface get method exception base class.
    '''
    pass


class NotFoundError(L3overlayError):
    '''
    Exception to raise when an interface was unable to be found.
    '''
    def __init__(self, name, description="interface", netns=None, root_ipdb=None):
        if netns:
            super().__init__("unable to find %s with name '%s' in %s" % (
                description,
                name,
                netns.description,
            ))
        elif root_ipdb:
            super().__init__("unable to find %s with name '%s' in root namespace" % (
                description,
                name,
            ))
        else:
            super().__init__("unable to find %s with name '%s'" % (
                description,
                name,
            ))


class NotRemovedError(L3overlayError):
    '''
    Exception to raise when and interface was not removed when it should have been.
    '''
    def __init__(self, interface):
        if interface.netns:
            super().__init__(
                "%s '%s' in %s still exists even after waiting %i second%s for removal" % (
                    interface.description,
                    interface.name,
                    interface.netns.description,
                    REMOVE_WAIT_MAX,
                    "s" if REMOVE_WAIT_MAX != 1.0 else "",
                ))
        elif interface.root_ipdb:
            super().__init__(
                # pylint: disable=line-too-long
                "%s '%s' in root namespace still exists even after waiting %i second%s for removal" % (
                    interface.description,
                    interface.name,
                    REMOVE_WAIT_MAX,
                    "s" if REMOVE_WAIT_MAX != 1.0 else "",
                ))
        else:
            super().__init__(
                "%s '%s' still exists even after waiting %.1f second%s for removal" % (
                    interface.description,
                    interface.name,
                    REMOVE_WAIT_MAX,
                    "s" if REMOVE_WAIT_MAX != 1.0 else "",
                ))


class RemovedThenModifiedError(L3overlayError):
    '''
    Exception to raise when an interface was removed and then modified afterwards.
    '''
    def __init__(self, interface):
        if interface.netns:
            super().__init__("%s '%s' in %s removed and then modified" % (
                interface.description,
                interface.name,
                interface.netns.description,
            ))
        elif interface.root_ipdb:
            super().__init__("%s '%s' in root namespace removed and then modified " % (
                interface.description,
                interface.name
            ))
        else:
            super().__init__("%s '%s' removed and then modified" % (
                interface.description,
                interface.name
            ))


class UnexpectedTypeError(L3overlayError):
    '''
    Exception to raise when the interface found was of an unexpected type.
    '''
    def __init__(self, name, typ, *expected_types, netns=None, root_ipdb=None):
        if netns:
            super().__init__(
                "found interface with name '%s' of type '%s' in %s, expected '%s'" % (
                    name,
                    typ,
                    netns.description,
                    str.join("/", expected_types),
                ))
        elif root_ipdb:
            super().__init__(
                "found interface with name '%s' of type '%s' in root namespace, expected '%s'" % (
                    name,
                    typ,
                    str.join("/", expected_types),
                ))
        else:
            super().__init__(
                "found interface with name '%s' of type '%s', expected '%s'" % (
                    name,
                    typ,
                    str.join("/", expected_types),
                ))
