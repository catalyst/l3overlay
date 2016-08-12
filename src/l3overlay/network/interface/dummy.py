#
# IPsec overlay network manager (l3overlay)
# l3overlay/network/interface/dummy.py - dummy interface class and functions
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


from l3overlay.network.interface import Interface


IF_TYPE = "dummy"


class Dummy(Interface):
    '''
    Dummy interface class. Subclass of the Interface class, simply for
    subclass identification purposes.
    '''

    description = "%s interface" % IF_TYPE


def get(logger, ipdb, name):
    '''
    Return a dummy interface object for the given interface name.
    '''

    logger.debug("getting runtime state for %s interface '%s'" % (IF_TYPE, name))

    if name in ipdb.by_name.keys():
        return Dummy(logger, ipdb, ipdb.interfaces[name], name)
    else:
        raise RuntimeError("unable to find %s interface in IPDB: %s" % (IF_TYPE, name))


def create(logger, ipdb, name):
    '''
    Create a dummy interface object, using a given interface name.
    '''

    logger.debug("creating %s interface '%s'" % (IF_TYPE, name))

    interface = ipdb.interfaces[name] if name in ipdb.interfaces else None

    if not interface:
        interface = ipdb.create(ifname=name, kind=IF_TYPE)
        ipdb.commit()

    return Dummy(logger, ipdb, interface, name)
