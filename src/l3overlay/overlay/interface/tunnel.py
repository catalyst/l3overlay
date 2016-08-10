#
# IPsec overlay network manager (l3overlay)
# l3overlay/overlay/interface/tunnel.py - static tunnel
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

from l3overlay.network.interface import gre

from l3overlay.overlay.interface import Interface


class Tunnel(Interface):
    '''
    Used to configure a GRE/GRETAP tunnel interface.
    '''

    def __init__(self, daemon, overlay, name, config):
        '''
        Parse the static interface configuration and create
        internal fields.
        '''

        super().__init__(daemon, overlay, name)

        self.mode = util.enum_get(config["mode"], ["gre", "gretap"])
        self.local = util.ip_address_get(config["local"])
        self.remote = util.ip_address_get(config["remote"])
        self.address = util.ip_address_get(config["address"])
        self.netmask = util.netmask_get(config["netmask"], Util.ip_address_is_v6(address))

        self.tunnel_name = self.daemon.interface_name(self.name)
        self.key = self.daemon.gre_key(self.local, self.remote)


    def start(self):
        '''
        Start the static tunnel.
        '''

        self.logger.info("starting static tunnel '%s'" % self.name)

        tunnel_if = gre.create(
            self.logger,
            self.ipdb,
            self.tunnel_name,
            self.mode,
            self.local,
            self.remote,
            self.key,
        )
        tunnel_if.add_ip(self.address, self.netmask)
        tunnel_if.up()

        self.logger.info("finished starting static tunnel '%s'" % self.name)

        #        static_tunnel = {
        #            'name': name,
        #            'interface': tunnel_name,
        #        }

        #        logging.debug("adding %s to list of static tunnels" % name)
        #        self.static_tunnels.append(static_tunnel)

        #        logging.debug("adding BGP route for static tunnel %s" % name)
        #        if Util.ip_address_is_v6(address):
        #            self.bird6_config_add('tunnels', [static_tunnel])
        #        else:
        #            self.bird_config_add('tunnels', [static_tunnel])



    def stop(self):
        '''
        Stop the static tunnel.
        '''

        self.logger.info("stopping static tunnel '%s'" % self.name)

        gre.get(self.logger, self.ipdb, self.tunnel_name).remove()

        self.logger.info("finished stopping static tunnel '%s'" % self.name)


Interface.register(Tunnel)
