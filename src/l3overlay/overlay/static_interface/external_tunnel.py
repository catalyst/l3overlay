#
# IPsec overlay network manager (l3overlay)
# l3overlay/overlay/static_interface/external_tunnel.py - static external tunnel
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

from l3overlay.network.interface import bridge
from l3overlay.network.interface import gre
from l3overlay.network.interface import veth

from l3overlay.overlay import active_interface

from l3overlay.overlay.interface import ReadError

from l3overlay.overlay.static_interface.base import StaticInterface

from l3overlay.util.exception import L3overlayError


class NonUniqueTunnelError(L3overlayError):
    def __init__(self, tunnel):
        super().__init__("more than one tunnel without key value for address pair (%s, %s)" %
                (tunnel.local, tunnel.remote))

class KeyNumUnavailableError(L3overlayError):
    def __init__(self, tunnel, key):
        super().__init__("more than one tunnel using key value %s for address pair (%s, %s)" %
                (key, tunnel.local, tunnel.remote))


class ExternalTunnel(StaticInterface):
    '''
    Used to configure a GRE/GRETAP external (root namespace) tunnel interface.
    '''

    def __init__(self, logger, name,
                local, remote, address, netmask,
                key, ikey, okey,
                use_ipsec, ipsec_psk):
        '''
        Set up static external tunnel internal fields.
        '''

        super().__init__(logger, name)

        self.local = local
        self.remote = remote
        self.address = address
        self.netmask = netmask

        self.key = key
        self.ikey = ikey
        self.okey = okey

        self.use_ipsec = use_ipsec
        self.ipsec_psk = ipsec_psk


    def setup(self, daemon, overlay):
        '''
        Set up static external tunnel runtime state.
        '''

        super().setup(daemon, overlay)

        key = self.key if self.key else self.ikey

        if key:
            self.daemon.gre_key_add(self.local, self.remote, key)
        if self.use_ipsec:
            self.daemon.ipsec_tunnel_add(self.local, self.remote, self.ipsec_psk)

        self.tunnel_name = self.daemon.interface_name(self.name, limit=13)
        self.bridge_name = "%sbr" % self.tunnel_name
        self.root_veth_name = "%sv0" % self.tunnel_name
        self.netns_veth_name = "%sv1" % self.tunnel_name


    def start(self):
        '''
        Start the static external tunnel.
        '''

        self.logger.info("starting static external tunnel '%s'" % self.name)

        tunnel_if = gre.create(
            self.dry_run,
            self.logger,
            self.tunnel_name,
            "gretap",
            self.local,
            self.remote,
            key=self.key,
            ikey=self.ikey,
            okey=self.okey,
            root_ipdb=self.root_ipdb,
        )

        root_veth_if = veth.create(
            self.dry_run,
            self.logger,
            self.root_veth_name,
            self.netns_veth_name,
            root_ipdb=self.root_ipdb,
        )

        netns_veth_if = root_veth_if.peer_get(peer_netns=self.netns)
        netns_veth_if.netns_set(self.netns)

        bridge_if = bridge.create(
            self.dry_run,
            self.logger,
            self.bridge_name,
            root_ipdb=self.root_ipdb,
        )
        bridge_if.add_port(tunnel_if)
        bridge_if.add_port(root_veth_if)

        netns_veth_if.add_ip(self.address, self.netmask)

        tunnel_if.up()
        root_veth_if.up()
        netns_veth_if.up()
        bridge_if.up()

        self.logger.info("finished starting static external tunnel '%s'" % self.name)


    def stop(self):
        '''
        Stop the static external tunnel.
        '''

        self.logger.info("stopping static external tunnel '%s'" % self.name)

        bridge.get(self.dry_run, self.logger, self.bridge_name, root_ipdb=self.root_ipdb).remove()
        veth.get(
            self.dry_run,
            self.logger,
            self.root_veth_name,
            self.netns_veth_name,
            root_ipdb=self.root_ipdb,
        ).remove()
        gre.get(self.dry_run, self.logger, self.tunnel_name, "gretap", root_ipdb=self.root_ipdb).remove()

        self.logger.info("finished stopping static external tunnel '%s'" % self.name)


    def remove(self):
        '''
        Remove the static external tunnel.
        '''

        if self.use_ipsec:
            self.daemon.gre_key_remove(self.local, self.remote, self.key if self.key else self.ikey)
            self.daemon.ipsec_tunnel_remove(self.local, self.remote)


    def is_ipv6(self):
        '''
        Returns True if this static external tunnel has an IPv6 address
        assigned to it.
        '''

        return util.ip_address_is_v6(self.address)


    def active_interfaces(self):
        '''
        Return an iterable of ActiveInterface objects representing the
        physical interfaces this static interface uses.
        '''

        return (
            active_interface.create(self.logger, self.bridge_name, None),
            active_interface.create(self.logger, self.root_veth_name, None),
            active_interface.create(self.logger, self.tunnel_name, None),
        )

StaticInterface.register(ExternalTunnel)


def read(logger, name, config):
    '''
    Create a static external tunnel from the given configuration object.
    '''

    local = util.ip_address_get(config["local"])
    remote = util.ip_address_get(config["remote"])
    address = util.ip_address_get(config["address"])
    netmask = util.netmask_get(config["netmask"], util.ip_address_is_v6(address))

    key = util.integer_get(config["key"], minval=0) if "key" in config else None
    ikey = util.integer_get(config["ikey"], minval=0) if "ikey" in config else None
    okey = util.integer_get(config["okey"], minval=0) if "okey" in config else None

    use_ipsec = util.boolean_get(config["use-ipsec"]) if "use-ipsec" in config else False
    ipsec_psk = util.hex_get_string(config["ipsec-psk"], min=6, max=64) if "ipsec-psk" in config else None

    if key is None and ikey is not None and okey is None:
        raise ReadError("ikey defined but okey undefined in overlay '%s'" % name)

    if key is None and ikey is None and okey is not None:
        raise ReadError("okey defined but ikey undefined in overlay '%s'" % name)

    return ExternalTunnel(
        logger, name,
        local, remote, address, netmask,
        key, ikey, okey,
        use_ipsec, ipsec_psk,
    )


def write(external_tunnel, config):
    '''
    Write the static external tunnel to the given configuration object.
    '''

    config["local"] = str(external_tunnel.local)
    config["remote"] = str(external_tunnel.remote)
    config["address"] = str(external_tunnel.address)
    config["netmask"] = str(external_tunnel.netmask)

    if external_tunnel.key:
        config["key"] = str(external_tunnel.key)
    if external_tunnel.ikey:
        config["ikey"] = str(external_tunnel.ikey)
    if external_tunnel.okey:
        config["okey"] = str(external_tunnel.okey)

    config["use-ipsec"] = str(external_tunnel.use_ipsec).lower()
    if external_tunnel.ipsec_psk:
        config["ipsec-psk"] = external_tunnel.ipsec_psk
