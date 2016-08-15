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

    def __init__(self, daemon, overlay, name, config):
        '''
        Parse the static bgp configuration and create
        internal fields.
        '''

        super().__init__(daemon, overlay, name)

        self.neighbor = util.ip_address_get(config["neighbor"])
        self.local = util.ip_address_get(config["local"]) if "local" in config else None

        self.local_asn = util.integer_get(config["local-asn"]) if "local-asn" in config else overlay.asn
        self.neighbor_asn = util.integer_get(config["neighbor-asn"]) if "neighbor-asn" in config else overlay.asn

        self.bfd = util.boolean_get(config["bfd"]) if "bfd" in config else False
        self.ttl_security = util.boolean_get(config["ttl-security"]) if "ttl-security" in config else False

        self.description = config["description"] if "description" in config else None

        self.import_prefixes = [util.bird_prefix_get(v) for k, v in config.items() if k.startswith("import-prefix")]


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
