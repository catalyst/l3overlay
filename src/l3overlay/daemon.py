#
# IPsec overlay network manager (l3overlay)
# l3overlay/daemon.py - daemon thread class
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


import os
import pyroute2
import stat
import sys

from l3overlay import ipsec as ipsec_process
from l3overlay import overlay
from l3overlay import util

from l3overlay.util import logger

from l3overlay.util.worker import Worker

from l3overlay.overlay.interface.overlay_link import OverlayLink
from l3overlay.overlay.interface.veth import VETH


class Daemon(Worker):
    '''
    Daemon class for overlay management.
    '''

    def __init__(self, args):
        '''
        Set up daemon internal fields and runtime state.
        '''

        # Superclass state.
        super().__init__()

        # Arguments.
        self.args = args

        # Internal fields which don't require the global configuration
        # to set up.
        self._interface_names = []
        self._gre_keys = {}
        self.mesh_links = set()

        self.root_ipdb = pyroute2.IPDB()

        # Load the global configuration file.
        self.global_conf = self.args.global_conf
        self.global_config = util.config(self.global_conf)["global"]

        # Get the logging parameters and start a logger, so output
        # can be logged as soon as possible.
        self.log = self.value_get("log", os.path.join(util.path_root(), "var", "log", "l3overlay.log"))
        self.log_level = util.enum_get(
            self.value_get("log-level", "INFO"),
            ["NOSET", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        )
        self.logger = logger.create(self.log, self.log_level, "l3overlay")
        self.logger.start()

        # Log exceptions for the rest of the initialisation process.
        try:
            # Get (general) global configuration.
            self.use_ipsec = util.boolean_get(self.value_get("use-ipsec", "False"))
            self.ipsec_manage = util.boolean_get(self.value_get("ipsec-manage", "True"))

            psk = self.value_get("ipsec-psk")
            self.ipsec_psk = util.hex_get_string(psk, min=6, max=64) if psk else None

            # Get required directory paths.
            self.lib_dir = self.value_get("lib-dir", os.path.join(util.path_root(), "var", "lib", "l3overlay"))
            self.overlay_dir = os.path.join(self.lib_dir, "overlays")


            self.fwbuilder_script_dir = self.value_get("fwbuilder-script-dir", util.path_search("fwbuilder_scripts"))
            self.template_dir = self.value_get("template-dir", util.path_search("templates"))

            # Get required file paths.
            self.pid = self.value_get("pid", os.path.join(util.path_root(), "var", "run", "l3overlayd.pid"))

            self.ipsec_conf = self.value_get("ipsec-conf", os.path.join(util.path_root(), "etc", "ipsec", "l3overlay.conf"))
            self.ipsec_secrets = self.value_get("ipsec-secrets", os.path.join(util.path_root(), "etc", "ipsec.secrets" if self.ipsec_manage else "ipsec.l3overlay.secrets"))

            # Create a list of all the overlay configuration file paths.
            self.overlay_conf_dir = None
            self.overlay_confs = []

            if self.args.overlay_conf:
                self.overlay_confs = self.args.overlay_conf
            else:
                self.overlay_conf_dir = self.value_get("overlay-conf-dir", util.path_search("overlays"))
                for overlay_conf_file in os.listdir(self.overlay_conf_dir):
                    overlay_conf = os.path.join(self.overlay_conf_dir, overlay_conf_file)
                    if os.path.isfile(overlay_conf):
                        self.overlay_confs.append(overlay_conf)

            # Create the application state for each overlay. and sort
            # the list of overlays into the correct execution order.
            self.overlays = []

            for overlay_conf in self.overlay_confs:
                self.overlays.append(overlay.read(self, overlay_conf))

            self.overlays_sorted()

            # Create the IPsec process object, which configures
            # and manages IPsec tunnel daemon.
            self.ipsec_process = ipsec_process.create(self)

        except Exception as e:
            self.logger.exception(e)
            sys.exit(1)


    #
    ## Daemon 'start' methods.
    #


    def value_get(self, key, default=None):
        '''
        Get a key, and check the argument list and global configuration,
        in that order, for a corresponding value.

        If one is not found, return default.
        '''

        arg_key = key.lower().replace("-", "_")
        config_key = key.lower().replace("_", "-")

        if arg_key in self.args.__dict__:
            return self.args.__dict__[arg_key]
        elif config_key in self.global_config:
            return self.global_config[config_key]
        else:
            return default


    def overlays_sorted(self):
        '''
        Resolve inter-overlay dependencies, and place a sorted list
        of overlays, where there would be no dependency issues upon
        starting them, in place of the existing list.
        '''

        sorted_overlays = []

        for overlay in self.overlays:
            self._overlays_sorted(sorted_overlays, overlay)

        self.overlays = sorted_overlays
            

    def _overlays_sorted(self, sorted_overlays, overlay):
        '''
        Recursive helper method to overlays_sorted.
        '''

        for interface in overlay.interfaces:
            if isinstance(interface, VETH) and interface.inner_namespace in self.overlays:
                self._overlays_sorted(sorted_overlays, self.overlays[interface.inner_namespace])
            elif isinstance(interface, OverlayLink):
                self._overlays_sorted(sorted_overlays, self.overlays[interface.inner_overlay_name])

        sorted_overlays.append(overlay)


    def start(self):
        '''
        Start the daemon.
        '''

        if self.is_starting() or self.is_started():
            raise RuntimeError("daemon started twice")

        self.set_starting()

        self.logger.debug("creating lib dir '%s'" % self.lib_dir)
        util.directory_create(self.lib_dir)

        for overlay in self.overlays:
            overlay.start()

        self.ipsec_process = ipsec.create(self)
        self.ipsec_process.start()

        self.set_started()


    #
    ## Daemon 'stop' methods.
    #


    def stop(self):
        '''
        Stop the daemon.
        '''

        if not self.is_started():
            raise RuntimeError("daemon not yet started")

        if self.is_stopped() or self.is_stopped():
            raise RuntimeError("daemon stopped twice")

        self.set_stopping()

        self.ipsec_process.stop()
        self.ipsec_process.remove()

        for overlay in self.overlays:
            overlay.stop()
            overlay.remove()

        self.logger.debug("removing lib dir '%s'" % self.lib_dir)
        util.directory_remove(self.lib_dir)

        self.set_stopped()


    #
    ## Daemon 'remove' methods.
    #


    def remove(self):
        '''
        Remove the daemon runtime state.
        '''

        self.logger.stop()


    #
    ## Overlay helper methods.
    #


    def interface_name(self, name, suffix=None, limit=15):
        '''
        Returns a valid, unique (to this daemon daemon) interface name
        based on the given base name string
        '''

        ifname_num = 0

        while True:
            digits = len(str(ifname_num))

            if suffix:
                ifname_base = "%s%s" % (
                    re.sub("[^A-Za-z0-9]", "", name)[:limit - len(suffix) - digits],
                    suffix,
                )
            else:
                ifname_base = re.sub("[^A-Za-z0-9]", "", name)[:limit - digits]

            ifname = "%s%i" % (ifname_base, ifname_num)

            if ifname not in self._interface_names:
                break

            ifname_num += 1

        self._interface_names.append(ifname)
        return ifname


    def gre_key(self, local, remote):
        '''
        Return a unique (to this daemon) key value for the given
        (local, remote) link.
        '''

        link = (local, remote)

        if link not in self._gre_keys:
            self._gre_keys[link] = len(self._gre_keys)

        return self._gre_keys[link]

Worker.register(Daemon)


def create(args):
    '''
    Create a daemon object.
    '''

    return Daemon(args)
