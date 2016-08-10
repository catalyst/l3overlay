#
# IPsec overlay network manager (l3overlay)
# l3overlay/network/interface/gre.py - gre/gretap interface class and functions
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


IF_TYPES = ["gre", "gretap"]


class GRE(Interface):
    '''
    GRE tunnel interface class. Subclass of the Interface class, adding
    GRE tunnel-specific functions.
    '''

    def __init__(self, logger, ipdb, interface, name, kind):
        '''
        '''

        super().__init__(logger, ipdb, interface, name)

        self.kind = kind
        self.description = "%s interface" % self.kind


def get(logger, ipdb, name):
    '''
    Return a gre/gretap interface object for the given interface name.
    '''

    logger.debug("getting runtime state for %s interface '%s'" % (str.join("/", IF_TYPES), name))

    if name in ipdb.by_name.keys():
        interface = ipdb.interfaces[name]

        if interface.kind not in IF_TYPES:
            raise RuntimeError("interface of type '%s', expected '%s': %s" % (interface.kind, str.join("/", IF_TYPES), name))

        return GRE(logger, ipdb, interface, name, interface.kind)
    else:
        raise RuntimeError("unable to find %s interface in IPDB: %s" % (str.join("/", IF_TYPES), name))


def create(logger, ipdb, name,
        local, remote, kind="gre", ttl=16, key=None, ikey=None, okey=None, iflags=32, oflags=32):
    '''
    Create a gre/gretap interface object, using a given interface name.
    '''

    logger.debug("creating %s interface '%s'" % (kind, name))

    if name in ipdb.by_name.keys():
        interface = ipdb.interfaces[name]

        if (interface.kind not in IF_TYPES or
                interface.gre_local != str(local) or
                interface.gre_remote != str(remote) or
                interface.gre_ttl != ttl or
                interface.gre_ikey != ikey or
                interface.gre_okey != okey or
                interface.gre_iflags != iflags or
                interface.gre_oflags != oflags):
            Interface(None, ipdb, interface, name).remove()
        else:
            return GRE(logger, ipdb, interface, name, interface.kind)

    if key is not None:
        ikey = key
        okey = key

    interface = ipdb.create(
        ifname=name,
        kind=kind,
        gre_local=str(local),
        gre_remote=str(remote),
        gre_ttl=ttl,
        gre_ikey=ikey,
        gre_okey=okey,
        gre_iflags=iflags,
        gre_oflags=oflags,
    )
    ipdb.commit()

    return GRE(logger, ipdb, interface, name, kind)
