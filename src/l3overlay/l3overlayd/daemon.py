#
# IPsec overlay network manager (l3overlay)
# l3overlay/l3overlayd/daemon.py - daemon thread class
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
Daemon class for overlay management.
'''


import os
import re
import shutil

import pyroute2

from l3overlay import util

from l3overlay.l3overlayd import overlay

from l3overlay.l3overlayd.overlay.static_interface.overlay_link import OverlayLink
from l3overlay.l3overlayd.overlay.static_interface.veth import VETH

from l3overlay.l3overlayd.process import ipsec as ipsec_process

from l3overlay.util import logger

from l3overlay.util.exception import L3overlayError

from l3overlay.util.worker import Worker


class KeyAddedTwiceError(L3overlayError):
    '''
    Exception to raise when a GRE tunnel key has been added for use twice.
    '''
    def __init__(self, local, remote, key):
        super().__init__("key '%s' added twice for link (%s, %s)" % (key, local, remote))

class NoOverlayConfError(L3overlayError):
    '''
    Exception to raise when no overlay configuration files are found.
    '''
    def __init__(self):
        super().__init__("no overlay configuration files found")

class MeshLinkNonexistentError(L3overlayError):
    '''
    Exception to raise when trying to delete a non-existent mesh link.
    '''
    def __init__(self, local, remote):
        super().__init__("unable to delete non-existent mesh link (%s, %s)" % (local, remote))

class IPsecTunnelMismatchedPSKError(L3overlayError):
    '''
    Exception to raise when PSKs are mismatched when adding to the use count
    of an IPsec tunnel.
    '''
    def __init__(self, local, remote, expected_psk, actual_psk):
        super().__init__(
            "increasing usage count on already added IPsec tunnel (%s, %s) failed:"
            "expected PSK '%s', got '%s'" %
            (local, remote, expected_psk, actual_psk)
        )

class IPsecTunnelNonexistentError(L3overlayError):
    '''
    Exception to raise when trying to delete a non-existent IPsec tunnel.
    '''
    def __init__(self, local, remote):
        super().__init__("unable to delete non-existent IPsec tunnel (%s, %s)" % (local, remote))

class ReadError(L3overlayError):
    '''
    l3overlay read method error base class.
    '''
    pass


# pylint: disable=too-many-instance-attributes
class Daemon(Worker):
    '''
    Daemon class for overlay management.
    '''

    description = "daemon"


    # pylint: disable=too-many-arguments,too-many-locals
    def __init__(self, dry_run, logg,
                 log, log_level, use_ipsec, ipsec_manage, ipsec_psk,
                 lib_dir, overlay_dir,
                 fwbuilder_script_dir, overlay_conf_dir, template_dir,
                 pid, ipsec_conf, ipsec_secrets,
                 overlays):
        '''
        Set up daemon internal fields.
        '''

        super().__init__(use_setup=True)

        self.dry_run = dry_run
        self.logger = logg

        self.log = log
        self.log_level = log_level

        self.use_ipsec = use_ipsec
        self.ipsec_manage = ipsec_manage
        self.ipsec_psk = ipsec_psk

        self.lib_dir = lib_dir
        self.overlay_dir = overlay_dir
        self.fwbuilder_script_dir = fwbuilder_script_dir
        self.overlay_conf_dir = overlay_conf_dir
        self.template_dir = template_dir

        self.pid = pid
        self.ipsec_conf = ipsec_conf
        self.ipsec_secrets = ipsec_secrets

        self.overlays = overlays.copy()
        self.sorted_overlays = Daemon.overlays_sorted(self.overlays)

        # Initialised in setup().
        self.interface_names = None
        self.gre_keys = None
        self.mesh_links = None
        self.ipsec_tunnels = None
        self.ipsec_process = None
        self.root_ipdb = None


    @staticmethod
    def overlays_sorted(overlays):
        '''
        Resolve inter-overlay dependencies, and place a sorted iterable
        of overlays, where there would be no dependency issues upon
        starting them, in place of the existing list.
        '''

        overlay_names = sorted(overlays.keys())
        sorted_overlays = []

        while overlay_names:
            Daemon._overlays_sorted(
                overlays,
                overlay_names,
                sorted_overlays,
                overlays[overlay_names.pop(0)],
            )

        return tuple(sorted_overlays)


    @staticmethod
    def _overlays_sorted(overlays, overlay_names, sorted_overlays, ove):
        '''
        Recursive helper method to overlays_list_sorted.
        '''

        for sta in ove.static_interfaces:
            if isinstance(sta, VETH) and sta.inner_namespace in overlays:
                try:
                    overlay_names.remove(sta.inner_namespace)
                except ValueError:
                    continue
                Daemon._overlays_sorted(
                    overlays,
                    overlay_names,
                    sorted_overlays,
                    overlays[sta.inner_namespace],
                )

            elif isinstance(sta, OverlayLink):
                try:
                    overlay_names.remove(sta.inner_overlay_name)
                except ValueError:
                    continue
                Daemon._overlays_sorted(
                    overlays,
                    overlay_names,
                    sorted_overlays,
                    overlays[sta.inner_overlay_name],
                )

        sorted_overlays.append(ove)


    def setup(self):
        '''
        Set up daemon runtime state.
        '''

        try:
            self.set_settingup()

            self.interface_names = set()

            self.gre_keys = dict()

            self.mesh_links = dict()
            self.ipsec_tunnels = dict()

            # pylint: disable=no-member
            self.root_ipdb = pyroute2.IPDB() if not self.dry_run else None
        except Exception as exc:
            if self.logger.is_running():
                self.logger.exception(exc)
            raise

        for ove in self.sorted_overlays:
            try:
                ove.setup(self)
            except Exception as exc:
                if ove.logger.is_running():
                    ove.logger.exception(exc)
                raise

        try:
            self.ipsec_process = ipsec_process.create(self)

            self.set_setup()
        except Exception as exc:
            if self.logger.is_running():
                self.logger.exception(exc)
            raise


    def start(self):
        '''
        Start the daemon.
        '''

        try:
            self.set_starting()

            self.cleanup()
            self.create_lib_dir()

        except Exception as exc:
            if self.logger.is_running():
                self.logger.exception(exc)
            raise

        for ove in self.sorted_overlays:
            try:
                ove.start()

            except Exception as exc:
                if ove.logger.is_running():
                    ove.logger.exception(exc)
                raise

        try:
            self.ipsec_process.start()
            self.set_started()

        except Exception as exc:
            if self.logger.is_running():
                self.logger.exception(exc)
            raise


    def cleanup(self):
        '''
        Find and clean up any leftover unused state from previous l3overlay instances.
        '''

        if not self.dry_run:
            overlays_dir = os.path.join(self.lib_dir, "overlays")
            if os.path.isdir(overlays_dir):
                overlay_names = os.listdir(overlays_dir)
                if overlay_names:
                    self.logger.info("cleaning up existing lib dir '%s'" % self.lib_dir)
                    for overlay_name in overlay_names:
                        self.logger.info("cleaning up overlay '%s'" % overlay_name)

                        overlay_conf = os.path.join(overlays_dir, overlay_name, "overlay.conf")

                        if not os.path.isfile(overlay_conf):
                            self.logger.warning(
                                "unable to find running config for overlay '%s', "
                                "skipping cleanup" % overlay_name
                            )
                            continue

                        ove = overlay.read(self.log, self.log_level, conf=overlay_conf)

                        ove.setup(self)
                        ove.start()

                        ove.stop()
                        ove.remove()

                        self.logger.info("finished cleaning up overlay '%s'" % overlay_name)

                    self.logger.debug("removing lib dir '%s'" % self.lib_dir)
                    shutil.rmtree(self.lib_dir)

                    self.logger.info("finished cleaning up existing lib dir '%s'" % self.lib_dir)

            elif os.path.exists(self.lib_dir):
                self.logger.debug("removing file at lib dir path '%s'" % self.lib_dir)
                os.remove(self.lib_dir)


    def create_lib_dir(self):
        '''
        Create the runtime data (lib) directory.
        '''

        self.logger.debug("creating lib dir '%s'" % self.lib_dir)
        if not self.dry_run:
            util.directory_create(self.lib_dir)


    def stop(self):
        '''
        Stop the daemon.
        '''

        try:
            self.set_stopping()
            self.ipsec_process.stop()
            self.ipsec_process.remove()
        except Exception as exc:
            if self.logger.is_running():
                self.logger.exception(exc)
            raise

        for ove in reversed(self.sorted_overlays):
            try:
                ove.stop()
            except Exception as exc:
                if ove.logger.is_running():
                    ove.logger.exception(exc)
                raise

            try:
                ove.remove()
            except Exception as exc:
                if self.logger.is_running():
                    self.logger.exception(exc)
                raise

        try:
            self.logger.debug("removing lib dir '%s'" % self.lib_dir)
            if not self.dry_run:
                util.directory_remove(self.lib_dir)
            self.set_stopped()
        except Exception as exc:
            if self.logger.is_running():
                self.logger.exception(exc)
            raise


    def remove(self):
        '''
        Remove the daemon runtime state.
        '''

        try:
            self.set_removing()
            if not self.dry_run:
                self.logger.debug("releasing root IPDB")
                self.root_ipdb.release()
            self.logger.stop()
            self.set_removed()

        except Exception as exc:
            if self.logger.is_running():
                self.logger.exception(exc)
            raise


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

            if ifname not in self.interface_names:
                break

            ifname_num += 1

        self.interface_names.add(ifname)
        return ifname


    def gre_key_add(self, local, remote, key):
        '''
        Add a unique (to this daemon) key value for the given
        (local, remote) link.
        '''

        link = (local, remote)

        if link not in self.gre_keys:
            self.gre_keys[link] = set()

        if key in self.gre_keys[link]:
            raise KeyAddedTwiceError(local, remote, key)
        else:
            self.gre_keys[link].add(key)


    def gre_key_remove(self, local, remote, key):
        '''
        Remove a unique (to this daemon) key value for the given
        (local, remote) link.
        '''

        link = (local, remote)

        if link not in self.gre_keys:
            return

        if key in self.gre_keys[link]:
            self.gre_keys[link].remove(key)


    def mesh_link_add(self, local, remote):
        '''
        Add a link to the mesh tunnel database, to be read
        by the IPsec process.
        '''

        link = (local, remote)

        if link not in self.mesh_links:
            self.mesh_links[link] = 0

        self.mesh_links[link] += 1


    def mesh_link_remove(self, local, remote):
        '''
        Remove a link from the mesh tunnel database.
        '''

        link = (local, remote)

        if link in self.mesh_links:
            if self.mesh_links[link] <= 1:
                del self.mesh_links[link]
            else:
                self.mesh_links[link] -= 1
        else:
            raise MeshLinkNonexistentError(local, remote)


    def ipsec_tunnel_add(self, local, remote, ipsec_psk=None):
        '''
        Add a link to the IPsec tunnel database, to be read
        by the IPsec process.
        '''

        link = (local, remote)

        if link not in self.ipsec_tunnels:
            self.ipsec_tunnels[link] = {
                "ipsec-psk": ipsec_psk,
                "num": 0,
            }

        if self.ipsec_tunnels[link]["ipsec-psk"] == ipsec_psk:
            self.ipsec_tunnels[link]["num"] += 1
        else:
            raise IPsecTunnelMismatchedPSKError(
                local,
                remote,
                self.ipsec_tunnels[link]["ipsec-psk"],
                ipsec_psk,
            )


    def ipsec_tunnel_remove(self, local, remote):
        '''
        Remove a link from the IPsec tunnel database.
        '''

        link = (local, remote)

        if link in self.ipsec_tunnels:
            if self.ipsec_tunnels[link]["num"] <= 1:
                del self.ipsec_tunnels[link]
            else:
                self.ipsec_tunnels[link]["num"] -= 1
        else:
            raise IPsecTunnelNonexistentError(local, remote)

# pylint: disable=no-member
Worker.register(Daemon)


class ValueReader(object):
    '''
    Helper class for the read() method.
    '''

    def __init__(self, args, conf, config):
        '''
        Set up value reader internal state.
        '''

        self.args = args

        self.conf = conf
        self.config = config

        if not self.args:
            raise ReadError("args is undefined")


    def get(self, key, check_args=True, args_optional=False, default=None):
        '''
        Get a key, and check the argument list and global configuration,
        in that order, for a corresponding value.

        If one is not found, return default.
        '''

        arg_key = key.lower().replace("-", "_")
        config_key = key.lower().replace("_", "-")

        in_args = arg_key in self.args if args_optional else check_args

        if in_args and self.args[arg_key] is not None:
            return self.args[arg_key]
        elif self.config and config_key in self.config and self.config[config_key] is not None:
            return self.config[config_key]

        return default


    def boolean_get(self, key, check_args=True, args_optional=False, default=False):
        '''
        Get a key, and check the argument list and global configuration,
        in that order, for a corresponding value, which should be type boolean.

        If one is not found, return default.
        '''

        arg_key = key.lower().replace("-", "_")
        no_arg_key = "no_%s" % arg_key
        config_key = key.lower().replace("_", "-")

        in_args = arg_key in self.args if args_optional else check_args

        if in_args:
            if no_arg_key not in self.args and arg_key not in self.args:
                raise ReadError("%s and %s not defined in args for boolean argument '%s'" %
                                (arg_key, no_arg_key, key))
            if no_arg_key in self.args and arg_key not in self.args:
                raise ReadError("%s not defined in args for boolean argument '%s'" %
                                (arg_key, key))
            if arg_key in self.args and no_arg_key not in self.args:
                raise ReadError("%s not defined in args for boolean argument '%s'" %
                                (no_arg_key, key))

        if in_args and util.boolean_get(self.args[arg_key]):
            return True
        elif in_args and not util.boolean_get(self.args[no_arg_key]):
            return False
        elif self.config and config_key in self.config and self.config[config_key] is not None:
            return util.boolean_get(self.config[config_key])

        return default


    def path_get(self, key, check_args=True, args_optional=False, default=None):
        '''
        Get a key, and check the argument list and global configuration,
        in that order, for a corresponding value.

        If one is not found, return default.

        This version is specifically for path type objects, and properly
        handles relative names.
        '''

        arg_key = key.lower().replace("-", "_")
        config_key = key.lower().replace("_", "-")

        in_args = arg_key in self.args if args_optional else check_args

        if in_args and self.args[arg_key] is not None:
            return util.path_get(self.args[arg_key], relative_dir=os.getcwd())
        elif self.config and config_key in self.config and self.config[config_key] is not None:
            return util.path_get(self.config[config_key], relative_dir=os.path.dirname(self.conf))

        return default


def read(args):
    '''
    Create a daemon object using the given argument dictionary.
    '''

    # pylint: disable=too-many-branches
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-statements

    # Load the global configuration file (if specified),
    # and create a ValueReader based on that and the given arguments.
    global_conf = args["global_conf"] if "global_conf" in args else None
    global_config = util.config(global_conf)["global"] if global_conf else None

    reader = ValueReader(args, global_conf, global_config)

    # Get enough configuration to start a logger.
    log = reader.get("log")

    log_level = util.enum_get(
        reader.get("log-level", default="INFO"),
        ["NOTSET", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    )

    # Start the logger.
    logg = logger.create(log, log_level, "l3overlay")
    logg.start()

    # Log exceptions for the rest of the initialisation process.
    try:
        if global_config:
            logg.debug("loaded global configuration file '%s'" % global_conf)

        # Get (general) global configuration.
        dry_run = reader.boolean_get("dry-run", default=False)

        use_ipsec = reader.boolean_get("use-ipsec", default=True)
        ipsec_manage = reader.boolean_get("ipsec-manage", default=True)

        _psk = reader.get("ipsec-psk", args_optional=True)
        if _psk is not None:
            ipsec_psk = util.hex_get_string(_psk, mindigits=6, maxdigits=64)
        else:
            ipsec_psk = None

        # Get required directory paths.
        lib_dir = reader.path_get(
            "lib-dir",
            default=os.path.join(util.path_root(), "var", "lib", "l3overlay"),
        )
        overlay_dir = os.path.join(lib_dir, "overlays")

        fwbuilder_script_dir = reader.path_get(
            "fwbuilder-script-dir",
            default=util.path_search("fwbuilder-scripts"),
        )
        overlay_conf_dir = reader.path_get(
            "overlay-conf-dir",
            default=util.path_search("overlays"),
        )
        template_dir = reader.path_get(
            "template-dir",
            default=util.path_search("templates"),
        )

        # Get required file paths.
        pid = reader.path_get(
            "pid",
            default=os.path.join(util.path_root(), "var", "run", "l3overlayd.pid"),
        )

        if ipsec_manage:
            ipsec_conf_default = os.path.join(util.path_root(), "etc", "ipsec.conf")
            ipsec_secrets_default = os.path.join(util.path_root(), "etc", "ipsec.secrets")
        else:
            ipsec_conf_default = os.path.join(util.path_root(), "etc", "ipsec.d", "l3overlay.conf")
            ipsec_secrets_default = os.path.join(util.path_root(), "etc", "ipsec.l3overlay.secrets")
        ipsec_conf = reader.path_get("ipsec-conf", default=ipsec_conf_default)
        ipsec_secrets = reader.path_get("ipsec-secrets", default=ipsec_secrets_default)

        # Get overlay configuration file paths.
        overlay_confs = args["overlay_conf"]

        if overlay_confs is not None:
            if isinstance(overlay_confs, str):
                overlay_confs = tuple(
                    util.path_get(overlay_confs, relative_dir=os.getcwd()),
                )
            elif isinstance(overlay_confs, (list, dict)):
                overlay_confs = tuple(
                    (util.path_get(oc, relative_dir=os.getcwd()) for oc in overlay_confs),
                )
            else:
                raise ReadError("expected string, list or dict for overlay_confs, got %s: %s" %
                                (type(overlay_confs), overlay_confs))

        elif overlay_conf_dir is not None:
            overlay_confs = tuple(
                (os.path.join(overlay_conf_dir, oc) for oc in os.listdir(overlay_conf_dir)),
            )

        else:
            raise NoOverlayConfError()

        logg.debug("Global configuration:")
        logg.debug("  dry-run = %s" % dry_run)
        logg.debug("  use-ipsec = %s" % use_ipsec)
        logg.debug("  ipsec-manage = %s" % ipsec_manage)
        logg.debug("  ipsec-psk = %s" %
                   ("<redacted, length %i>" % len(ipsec_psk) if ipsec_psk else None))
        logg.debug("  lib-dir = %s" % lib_dir)
        logg.debug("  fwbuilder-script-dir = %s" % fwbuilder_script_dir)
        logg.debug("  overlay-conf-dir = %s" % overlay_conf_dir)
        logg.debug("  template-dir = %s" % template_dir)
        logg.debug("")


        logg.debug("Overlay configuration files:")
        for overlay_conf in overlay_confs:
            logg.debug("  %s" % overlay_conf)
        logg.debug("")

        # Create the application state for each overlay.
        overlays = {}

        for overlay_conf in overlay_confs:
            ove = overlay.read(log, log_level, conf=overlay_conf)
            overlays[ove.name] = ove

        # Return a set up daemon object.
        return Daemon(
            dry_run, logg,
            log, log_level, use_ipsec, ipsec_manage, ipsec_psk,
            lib_dir, overlay_dir,
            fwbuilder_script_dir, overlay_conf_dir, template_dir,
            pid, ipsec_conf, ipsec_secrets,
            overlays,
        )

    except Exception as exc:
        logg.exception(exc)
        raise


def write(daemon, global_conf, overlay_conf_dir):
    '''
    Write a daemon's global configuration to the given file,
    and overlay configurations to the given directory.
    '''

    global_config = util.config()

    global_config["log"] = daemon.log
    global_config["log-level"] = daemon.log_level

    global_config["use-ipsec"] = str(daemon.use_ipsec).lower()
    global_config["ipsec-manage"] = str(daemon.ipsec_manage).lower()
    global_config["ipsec-psk"] = daemon.ipsec_psk

    global_config["lib-dir"] = daemon.lib_dir
    global_config["overlay-dir"] = daemon.overlay_dir

    global_config["fwbuilder-script-dir"] = daemon.fwbuilder_script_dir
    if daemon.overlay_conf_dir:
        global_config["overlay-conf-dir"] = daemon.overlay_conf_dir
    global_config["template-dir"] = daemon.template_dir

    global_config["ipsec-conf"] = daemon.ipsec_conf
    global_config["ipsec-secrets"] = daemon.ipsec_secrets

    global_config.write(global_conf)

    for ove in daemon.overlays.values():
        overlay_config = util.config()
        ove.write(overlay_config)
        overlay_config.write(os.path.join(overlay_conf_dir, "%s.conf" % ove.name))
