#
# IPsec overlay network manager (l3overlay)
# l3overlay/daemon.py - daemon thread class
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


import os
import pyroute2
import re

from l3overlay import overlay
from l3overlay import util

from l3overlay.overlay.interface.overlay_link import OverlayLink
from l3overlay.overlay.interface.veth import VETH

from l3overlay.process import ipsec as ipsec_process

from l3overlay.util import logger
from l3overlay.util import worker

from l3overlay.util.exception import L3overlayError


class KeyAddedTwiceError(L3overlayError):
    def __init__(self, local, remote, key):
        super().__init__("key '%s' added twice for link (%s, %s)" % (key, local, remote))

class NoOverlayConfError(L3overlayError):
    def __init__(self):
        super().__init__("no overlay configuration files found")

class ReadError(L3overlayError):
    pass


class Daemon(worker.Worker):
    '''
    Daemon class for overlay management.
    '''

    description = "daemon"


    def __init__(self, dry_run, logger,
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
        self.logger = logger

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
        self.sorted_overlays = self.overlays_list_sorted()


    def overlays_list_sorted(self):
        '''
        Resolve inter-overlay dependencies, and place a sorted list
        of overlays, where there would be no dependency issues upon
        starting them, in place of the existing list.
        '''

        os = sorted(self.overlays.keys())
        sos = []

        while os:
            self._overlays_list_sorted(os, sos, self.overlays[os.pop(0)])

        return sos


    def _overlays_list_sorted(self, os, sos, o):
        '''
        Recursive helper method to overlays_list_sorted.
        '''

        for i in o.interfaces:
            if isinstance(i, VETH) and i.inner_namespace in self.overlays:
                try:
                    os.remove(i.inner_namespace)
                except ValueError:
                    continue
                self._overlays_list_sorted(os, sos, self.overlays[i.inner_namespace])

            elif isinstance(i, OverlayLink):
                try:
                    os.remove(i.inner_overlay_name)
                except ValueError:
                    continue
                self._overlays_list_sorted(os, sos, self.overlays[i.inner_overlay_name])

        sos.append(o)


    def setup(self):
        '''
        Set up daemon runtime state.
        '''

        try:
            self.set_settingup()

            self._gre_keys = {}
            self._interface_names = set()

            self.mesh_links = set()
            self.root_ipdb = pyroute2.IPDB() if not self.dry_run else None
        except Exception as e:
            if self.logger.is_running():
                self.logger.exception(e)
            raise

        for o in self.sorted_overlays:
            try:
                o.setup(self)
            except Exception as e:
                if o.logger.is_running():
                    o.logger.exception(e)
                raise

        try:
            self.ipsec_process = ipsec_process.create(self)

            self.set_setup()
        except Exception as e:
            if self.logger.is_running():
                self.logger.exception(e)
            raise


    def start(self):
        '''
        Start the daemon.
        '''

        try:
            self.set_starting()

            # There should only be one instance of l3overlay per machine,
            # so this SHOULD be okay. If it's not, well, we'll find out about it...
            if not self.dry_run and os.path.exists(self.lib_dir):
                self.logger.debug("removing existing lib dir '%s'" % self.lib_dir)
                util.directory_remove(self.lib_dir)

            self.logger.debug("creating lib dir '%s'" % self.lib_dir)
            if not self.dry_run:
                util.directory_create(self.lib_dir)
        except Exception as e:
            if self.logger.is_running():
                self.logger.exception(e)
            raise

        for o in self.sorted_overlays:
            try:
                o.start()
            except Exception as e:
                if o.logger.is_running():
                    o.logger.exception(e)
                raise

        try:
            self.ipsec_process.start()

            self.set_started()
        except Exception as e:
            if self.logger.is_running():
                self.logger.exception(e)
            raise


    def stop(self):
        '''
        Stop the daemon.
        '''

        try:
            self.set_stopping()

            self.ipsec_process.stop()
            self.ipsec_process.remove()
        except Exception as e:
            if self.logger.is_running():
                self.logger.exception(e)
            raise

        for o in reversed(self.sorted_overlays):
            try:
                o.stop()
            except Exception as e:
                if o.logger.is_running():
                    o.logger.exception(e)
                raise

            try:
                o.remove()
            except Exception as e:
                if self.logger.is_running():
                    self.logger.exception(e)
                raise

        try:
            self.logger.debug("removing lib dir '%s'" % self.lib_dir)
            util.directory_remove(self.lib_dir)

            self.set_stopped()
        except Exception as e:
            if self.logger.is_running():
                self.logger.exception(e)
            raise


    def remove(self):
        '''
        Remove the daemon runtime state.
        '''

        try:
            self.set_removing()

            self.logger.stop()

            self.set_removed()
        except Exception as e:
            if self.logger.is_running():
                self.logger.exception(e)
            raise


    def gre_key_add(self, local, remote, key):
        '''
        Add a unique (to this daemon) key value for the given
        (local, remote) link.
        '''

        link = (local, remote)

        if link not in self._gre_keys:
            self._gre_keys[link] = set()

        if key in self._gre_keys[link]:
            raise KeyUsedTwiceError(local, remote, key)
        else:
            self._gre_keys[link].add(key)


    def gre_key_remove(self, local, remote, key):
        '''
        Remove a unique (to this daemon) key value for the given
        (local, remote) link.
        '''

        link = (local, remote)

        if link not in self._gre_keys:
            return

        if key in self._gre_keys[link]:
            self._gre_keys[link].remove(key)


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

        self._interface_names.add(ifname)
        return ifname

worker.Worker.register(Daemon)


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
        else:
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

        if in_args and util.boolean_get(self.args[arg_key]) == True:
            return True
        elif in_args and util.boolean_get(self.args[no_arg_key]) == False:
            return False
        elif self.config and config_key in self.config and self.config[config_key] is not None:
            return util.boolean_get(self.config[config_key])
        else:
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
        else:
            return default


def read(args):
    '''
    Create a daemon object using the given argument dictionary.
    '''

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
    lg = logger.create(log, log_level, "l3overlay")
    lg.start()

    # Log exceptions for the rest of the initialisation process.
    try:
        if global_config:
            lg.debug("loaded global configuration file '%s'" % global_conf)

        # Get (general) global configuration.
        dry_run = reader.boolean_get("dry-run", default=False)

        use_ipsec = reader.boolean_get("use-ipsec", default=True)
        ipsec_manage = reader.boolean_get("ipsec-manage", default=True)

        _psk = reader.get("ipsec-psk", args_optional=True)
        ipsec_psk = util.hex_get_string(_psk, min=6, max=64) if _psk is not None else None

        # Get required directory paths.
        lib_dir = reader.path_get(
            "lib-dir",
            default = os.path.join(util.path_root(), "var", "lib", "l3overlay"),
        )
        overlay_dir = os.path.join(lib_dir, "overlays")

        fwbuilder_script_dir = reader.path_get(
            "fwbuilder-script-dir",
            default = util.path_search("fwbuilder-scripts"),
        )
        overlay_conf_dir = reader.path_get(
            "overlay-conf-dir",
            default = util.path_search("overlays"),
        )
        template_dir = reader.path_get(
            "template-dir",
            default = util.path_search("templates"),
        )

        # Get required file paths.
        pid = reader.path_get(
            "pid",
            default = os.path.join(util.path_root(), "var", "run", "l3overlayd.pid"),
        )

        ipsec_conf = reader.path_get(
            "ipsec-conf",
            default = os.path.join(util.path_root(), "etc", "ipsec.d", "l3overlay.conf"),
        )
        ipsec_secrets = reader.path_get(
            "ipsec-secrets",
            default = os.path.join(util.path_root(), "etc",
                    "ipsec.secrets" if ipsec_manage else "ipsec.l3overlay.secrets"),
        )

        # Get overlay configuration file paths.
        overlay_confs = args["overlay_conf"]

        if overlay_confs is not None:
            if isinstance(overlay_confs, str):
                overlay_confs = tuple(util.path_get(overlay_confs, relative_dir=os.getcwd()))
            elif isinstance(overlay_confs, list) or isinstance(overlay_confs, dict):
                overlay_confs = tuple((util.path_get(oc, relative_dir=os.getcwd()) for oc in overlay_confs))
            else:
                raise ReadError("expected string, list or dict for overlay_confs, got %s: %s" %
                        (type(overlay_confs), overlay_confs))

        elif overlay_conf_dir is not None:
            overlay_confs = tuple((os.path.join(overlay_conf_dir, oc) for oc in os.listdir(overlay_conf_dir)))

        else:
            raise NoOverlayConfError()

        lg.debug("Global configuration:")
        lg.debug("  dry-run = %s" % dry_run)
        lg.debug("  use-ipsec = %s" % use_ipsec)
        lg.debug("  ipsec-manage = %s" % ipsec_manage)
        lg.debug("  ipsec-psk = %s" %
                ("<redacted, length %i>" % len(ipsec_psk) if ipsec_psk else None))
        lg.debug("  lib-dir = %s" % lib_dir)
        lg.debug("  fwbuilder-script-dir = %s" % fwbuilder_script_dir)
        lg.debug("  overlay-conf-dir = %s" % overlay_conf_dir)
        lg.debug("  template-dir = %s" % template_dir)
        lg.debug("")


        lg.debug("Overlay configuration files:")
        for overlay_conf in overlay_confs:
            lg.debug("  %s" % overlay_conf)
        lg.debug("")

        # Create the application state for each overlay.
        overlays = {}

        for overlay_conf in overlay_confs:
            o = overlay.read(log, log_level, conf=overlay_conf)
            overlays[o.name] = o

        # Return a set up daemon object.
        return Daemon(
            dry_run, lg,
            log, log_level, use_ipsec, ipsec_manage, ipsec_psk,
            lib_dir, overlay_dir,
            fwbuilder_script_dir, overlay_conf_dir, template_dir,
            pid, ipsec_conf, ipsec_secrets,
            overlays,
        )

    except Exception as e:
        lg.exception(e)
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

    for o in daemon.overlays.values():
        overlay_config = util.config()
        o.write(overlay_config)
        overlay_config.write(os.path.join(overlay_conf_dir, "%s.conf" % o.name))
