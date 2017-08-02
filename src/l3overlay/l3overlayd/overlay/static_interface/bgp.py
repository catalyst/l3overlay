#
# IPsec overlay network manager (l3overlay)
# l3overlay/l3overlayd/overlay/static_interface/bgp.py - static bgp
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


from l3overlay import util

from l3overlay.l3overlayd.overlay.static_interface.base import StaticInterface


class BGP(StaticInterface):
    '''
    Used to configure a static BGP protocol.
    '''

    def __init__(self, logger, name,
            neighbor, local, local_asn, neighbor_asn, bfd, ttl_security, description, import_prefixes):
        '''
        Set up static bgp internal fields.
        '''

        super().__init__(logger, name)

        self.neighbor = neighbor
        self.local = local

        self.local_asn = local_asn
        self.neighbor_asn = neighbor_asn

        self.bfd = bfd
        self.ttl_security = ttl_security

        self.bgp_description = description

        self.import_prefixes = tuple(import_prefixes)


    def setup(self, daemon, overlay):
        '''
        Set up static bgp runtime state.
        '''

        super().setup(daemon, overlay)

        self.local_asn = self.local_asn if self.local_asn else overlay.asn
        self.neighbor_asn = self.neighbor_asn if self.neighbor_asn else overlay.asn


    def start(self):
        '''
        Starts with the BGP process.
        '''

        pass


    def stop(self):
        '''
        Stops with the BGP process.
        '''

        pass


    def is_ipv6(self):
        '''
        Returns True if this static bgp has an IPv6 address
        assigned to its neighbor address.
        '''

        return util.ip_address_is_v6(self.neighbor)


    def active_interfaces(self):
        '''
        Return an empty iterable, because a static BGP does not
        use its own physical interfaces.
        '''

        return tuple()

StaticInterface.register(BGP)


def read(logger, name, config):
    '''
    Create a static bgp from the given configuration object.
    '''

    neighbor = util.ip_address_get(config["neighbor"])
    local = util.ip_address_get(config["local"]) if "local" in config else None

    local_asn = util.integer_get(config["local-asn"], minval=0, maxval=65535) if "local-asn" in config else None
    neighbor_asn = util.integer_get(config["neighbor-asn"], minval=0, maxval=65535) if "neighbor-asn" in config else None

    bfd = util.boolean_get(config["bfd"]) if "bfd" in config else False
    ttl_security = util.boolean_get(config["ttl-security"]) if "ttl-security" in config else False

    description = config["description"] if "description" in config else None

    import_prefixes = [util.bird_prefix_get(v) for k, v in config.items() if k.startswith("import-prefix")]

    return BGP(logger, name,
            neighbor, local, local_asn, neighbor_asn, bfd, ttl_security, description, import_prefixes)


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

    if bgp.bgp_description:
        config["description"] = bgp.bgp_description

    if bgp.import_prefixes:
        for i, import_prefix in enumerate(bgp.import_prefixes):
            config["import-prefix-%i" % (i+1)] = import_prefix
