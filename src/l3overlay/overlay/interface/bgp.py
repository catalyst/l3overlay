#
# IPsec overlay network manager (l3overlay)
# l3overlay/overlay/interface/bgp.py - static bgp
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


from l3overlay import util

from l3overlay.overlay.interface.base import Interface


class BGP(Interface):
    '''
    Used to configure a static BGP protocol.
    '''

    def __init__(self, daemon, overlay, name,
            neighbor, local, local_asn, neighbor_asn, bfd, ttl_security, import_prefixes):
        '''
        Set up static bgp internal state.
        '''

        super().__init__(daemon, overlay, name)

        self.neighbor = neighbor
        self.local = local

        self.lcoal_asn = local_asn
        self.neighbor_asn = neighbor_asn

        self.bfd = bfd
        self.ttl_security = ttl_security

        self.import_prefixes = tuple(import_prefixes)


    def is_ipv6(self):
        '''
        Returns True if this static bgp has an IPv6 address
        assigned to its neighbor address.
        '''

        return util.ip_address_is_v6(self.neighbor)


    def start(self):
        '''
        Starts with the BGP process.
        '''

        return


    def stop(self):
        '''
        Stops with the BGP process.
        '''

        return

Interface.register(BGP)


def read(daemon, overlay, name, config):
    '''
    Create a static bgp from the given configuration object.
    '''

    neighbor = util.ip_address_get(config["neighbor"])
    local = util.ip_address_get(config["local"]) if "local" in config else None

    local_asn = util.integer_get(config["local-asn"]) if "local-asn" in config else overlay.asn
    neighbor_asn = util.integer_get(config["neighbor-asn"]) if "neighbor-asn" in config else overlay.asn

    bfd = util.boolean_get(config["bfd"]) if "bfd" in config else False
    ttl_security = util.boolean_get(config["ttl-security"]) if "ttl-security" in config else False

    description = config["description"] if "description" in config else None

    import_prefixes = [util.bird_prefix_get(v) for k, v in config.items() if k.startswith("import-prefix")]

    return BGP(daemon, overlay, name,
            neighbor, local, local_asn, neighbor_asn, bfd, ttl_security, import_prefixes)


def write(bgp, config):
    '''
    Write the static bgp to the given configuration object.
    '''

    config["neighbor"] = str(bgp.neighbor)
    if bgp.local:
        config["local"] = str(bgp.local)

    if bgp.local_asn:
        config["local-asn"] = str(bgp.local_asn)
    if bgp.neighbor_asn:
        config["neighbor-asn"] = str(bgp.neighbor_asn)

    if bgp.bfd:
        config["bfd"] = str(bgp.bfd).lower()
    if bgp.ttl_security:
        config["ttl-security"] = str(bgp.ttl_security).lower()

    if bgp.description:
        config["description"] = bgp.description

    if bgp.import_prefixes:
        for i, import_prefix in enumerate(bgp.import_prefixes):
            config["import-prefix-%i" % (i+1)] = import_prefix
