#
# IPsec overlay network manager (l3overlay)
# l3overlay/l3overlayd/overlay/static_interface/tunnel.py - static tunnel
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

from l3overlay.l3overlayd.network.interface import gre

from l3overlay.l3overlayd.overlay import active_interface

from l3overlay.l3overlayd.overlay.interface import ReadError

from l3overlay.l3overlayd.overlay.static_interface.base import StaticInterface

from l3overlay.util.exception import L3overlayError


class NonUniqueTunnelError(L3overlayError):
    def __init__(self, tunnel):
        super().__init__("more than one tunnel without key value for address pair (%s, %s)" %
                (tunnel.local, tunnel.remote))

class KeyNumUnavailableError(L3overlayError):
    def __init__(self, tunnel, key):
        super().__init__("more than one tunnel using key value %s for address pair (%s, %s)" %
                (key, tunnel.local, tunnel.remote))


class Tunnel(StaticInterface):
    '''
    Used to configure a GRE/GRETAP tunnel interface.
    '''

    def __init__(self, logger, name,
                mode, local, remote, address, netmask,
                key, ikey, okey):
        '''
        Set up static tunnel internal fields.
        '''

        super().__init__(logger, name)

        self.mode = mode
        self.local = local
        self.remote = remote
        self.address = address
        self.netmask = netmask

        self.key = key
        self.ikey = ikey
        self.okey = okey


    def setup(self, daemon, overlay):
        '''
        Set up static tunnel runtime state.
        '''

        super().setup(daemon, overlay)

        key = self.key if self.key else self.ikey

        if key:
            self.daemon.gre_key_add(self.local, self.remote, key)

        self.tunnel_name = self.daemon.interface_name(self.name)


    def start(self):
        '''
        Start the static tunnel.
        '''

        self.logger.info("starting static tunnel '%s'" % self.name)

        tunnel_if = gre.create(
            self.dry_run,
            self.logger,
            self.tunnel_name,
            self.mode,
            self.local,
            self.remote,
            key = self.key,
            ikey = self.ikey,
            okey = self.okey,
            netns = self.netns,
        )
        tunnel_if.add_ip(self.address, self.netmask)
        tunnel_if.up()

        self.logger.info("finished starting static tunnel '%s'" % self.name)


    def stop(self):
        '''
        Stop the static tunnel.
        '''

        self.logger.info("stopping static tunnel '%s'" % self.name)

        gre.get(self.dry_run, self.logger, self.tunnel_name, self.mode, netns=self.netns).remove()

        self.logger.info("finished stopping static tunnel '%s'" % self.name)


    def remove(self):
        '''
        Remove the static tunnel.
        '''

        self.daemon.gre_key_remove(self.local, self.remote, self.key if self.key else self.ikey)


    def is_ipv6(self):
        '''
        Returns True if this static tunnel has an IPv6 address
        assigned to it.
        '''

        return util.ip_address_is_v6(self.address)


    def active_interfaces(self):
        '''
        Return an iterable of ActiveInterface objects representing the
        physical interfaces this static interface uses.
        '''

        return (active_interface.create(self.logger, self.tunnel_name, self.netns.name),)

StaticInterface.register(Tunnel)


def read(logger, name, config):
    '''
    Create a static tunnel from the given configuration object.
    '''

    mode = util.enum_get(config["mode"], ["gre", "gretap"])
    local = util.ip_address_get(config["local"])
    remote = util.ip_address_get(config["remote"])
    address = util.ip_address_get(config["address"])
    netmask = util.netmask_get(config["netmask"], util.ip_address_is_v6(address))

    key = util.integer_get(config["key"], minval=0) if "key" in config else None
    ikey = util.integer_get(config["ikey"], minval=0) if "ikey" in config else None
    okey = util.integer_get(config["okey"], minval=0) if "okey" in config else None

    if key is None and ikey is not None and okey is None:
        raise ReadError("ikey defined but okey undefined in overlay '%s'" % name)

    if key is None and ikey is None and okey is not None:
        raise ReadError("okey defined but ikey undefined in overlay '%s'" % name)

    return Tunnel(
        logger, name,
        mode, local, remote, address, netmask,
        key, ikey, okey,
    )


def write(tunnel, config):
    '''
    Write the static tunnel to the given configuration object.
    '''

    config["mode"] = tunnel.mode.lower()
    config["local"] = str(tunnel.local)
    config["remote"] = str(tunnel.remote)
    config["address"] = str(tunnel.address)
    config["netmask"] = str(tunnel.netmask)

    if tunnel.key:
        config["key"] = str(tunnel.key)
    if tunnel.ikey:
        config["ikey"] = str(tunnel.ikey)
    if tunnel.okey:
        config["okey"] = str(tunnel.okey)
