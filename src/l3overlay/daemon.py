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
import stat
import sys

from l3overlay import util

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

        self().__init__()

        self.args = args


    #
    ## Daemon 'start' methods.
    #


    def get_value(self, key, default=None):
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
                self._overlays_sorted(self.overlays[interface.inner_namespace])
            elif isinstance(interface, OverlayLink):
                self._overlays_sorted(self.overlays[interface.inner_overlay_name])

        sorted_overlays.append(overlay)


    def start(self):
        '''
        Start the daemon.
        '''

        if self.starting() or self.running():
            raise RuntimeError("daemon started twice")

        self.set_starting()

        # Load the global configuration file.
        self.global_conf = args.global_conf
        self.global_config = util.conf(global_conf_path)["global"]

        # Get the logging parameters and start a logger, so output
        # can be logged as soon as possible.
        self.log = self.get_value("log", os.path.join(util.path_root(), "var", "log", "l3overlay.log"))
        self.log_level = util.enum_get(
            self.get_value("log-level", "INFO"),
            ["NOSET", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        )
        self.logger = util.logger(self.log, self.log_level, "l3overlay")

        # Set up the exception logger.
        try:
            # Get (general) global configuration.
            self.use_ipsec = util.boolean_get(self.value_get("use-ipsec", False))
            self.ipsec_manage = util.boolean_get(self.value_get("ipsec-manage", True))

            psk = self.value_get("ipsec-psk")
            self.ipsec_psk = util.hex_get_string(psk, min=6, max=64) if psk else None

            # Get required directory paths.
            self.lib_dir = self.get_value("lib-dir", os.path.join(util.path_root(), "var", "lib", "l3overlay"))

            self.fwbuilder_script_dir = self.get_value("fwbuilder-script-dir", util.path_search("fwbuilder_scripts"))
            self.template_dir = self.get_value("template-dir", util.path_search("templates"))

            # Get required file paths.
            self.pid = self.get_value("pid", os.path.join(util.path_root(), "var", "run", "l3overlayd.pid"))

            self.ipsec_conf = self.get_value("ipsec-conf", os.path.join(util.path_root(), "etc", "ipsec", "l3overlay.conf"))
            self.ipsec_secrets = self.get_value("ipsec-secrets", os.path.join(util.path_root(), "etc", "ipsec.secrets" if self.ipsec_manage else "ipsec.l3overlay.secrets")

            # Set up the lib dir.
            self.logger.debug("creating lib dir '%s'" % self.lib_dir)
            util.directory_create(self.lib_dir)

            # Create a list of all the overlay configuration file paths.
            self.overlay_conf_dir = None
            self.overlay_confs = []

            if self.args.overlay_conf:
                self.overlay_confs = self.args.overlay_conf
            else:
                self.overlay_conf_dir = self.get_value("overlay-conf-dir", util.path_search("overlays"))
                for overlay_conf_file in os.listdir(self.overlay_conf_dir):
                    overlay_conf = os.path.join(self.overlay_conf_dir, overlay_conf_file)
                    if os.path.isfile(overlay_conf):
                        self.overlay_confs.append(overlay_conf)

            # Create the application state for each overlay. and sort
            # the list of overlays into the correct execution order.
            self.overlays = []

            for overlay_conf in self.overlay_confs:
                config = util.config(overlay_conf)

                name = util.name_get(config["overlay"]["name"])
                logger = util.logger(self.log, "l3overlay", name)

                self.overlays.append(Overlay(logger, self, name, config))

            self.overlays_sorted()

            # Start the overlays.
            for overlay in self.overlays:
                overlay.start()

            # Start the mesh tunnels.

        except Exception as e:
            self.logger.exception(e)
            sys.exit(1)

        self.set_started()


    #
    ## Daemon 'stop' methods.
    #


    def stop(self):
        '''
        Stop the daemon.
        '''

        if not self.running():
            raise RuntimeError("daemon not yet started")

        if self.stopped():
            raise RuntimeError("daemon stopped twice")

        self.set_stopping()

        # do stuff

        self.set_stopped()


    ##################################################################################################


    def start(self):
        """
        Start this OverlayDaemon, and all of its configured overlays.
        """

        if self.shut_down == True:
            raise Exception("OverlayDaemon permanently shut down, cannot start again")

        if self.stopped == False:
            return

        self.stopped = False

        # Load the runtime configuration data.
        self.start_config()

        # Configure the logging system.
        self.start_logging()

        # This is the point where building the OverlayDaemon starts.
        logging.info("Starting daemon...")

        # Create the runtime directories.
        self.start_directories()

        # Start all of the configured overlays, respecting any inter-overlay
        # dependencies.
        for overlay_path in OverlayDaemon.overlay_paths_sorted(self.overlay_paths):
            self.overlays.append(Overlay(self, overlay_path))

        # Start the IPsec tunnels for the overlays.
        self.start_ipsec()

        logging.info("Started.")


    def start_config(self):
        """
        Load the runtime configuration for this OverlayDaemon.
        """

        # Load the global configuration file.
        if os.path.exists(self.global_conf):
            config = configparser.ConfigParser()
            config.read(self.global_conf)

            self.config_env = Environment(
                trim_blocks=True,
                loader=FileSystemLoader(template_dir),
            )
        else:
            config = {'global': {}}

        # Logging level.
        if 'logging-level' in config['global']:
            self.logging_level = Util.enum_get(
                config['global']['logging-level'],
                [ 'NOSET', 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL' ],
            )
        else: 
            self.logging_level = logging.INFO

        # Check whether or not to use IPsec.
        if 'use-ipsec' in config['global']:
            self.use_ipsec = Util.boolean_get(config['global']['use-ipsec'])
        else:
            self.use_ipsec = False

        # IPsec PSK, to be configured onto all tunnels.
        self.ipsec_psk = Util.hex_get_string(config['global']['ipsec-psk'], min=6, max=64) if self.use_ipsec == True else None

        # Determine whether or not to take over control of IPsec. Read the
        # README for more information on how this option works.
        if 'use-ipsec' in config['global']:
            self.ipsec_manage = Util.boolean_get(config['global']['ipsec-manage']) if 'ipsec-manage' in config['global'] else True
        else:
            self.ipsec_manage = False

        #
        # Find external files needed in overlay configuration.
        #

        # Used to generate the BIRD routing daemon configurations.
        self.bird_config_template = self.config_env.get_template('bird.conf')

        # Used to generate the IPsec tunnel configuration.
        self.ipsec_config_template = self.config_env.get_template('ipsec.conf')
        self.ipsec_secrets_template = self.config_env.get_template('ipsec.secrets')

        #
        # Runtime data structures and objects.
        #

        # Used by Overlay.interface_name() to store the interface names already
        # generated by itself, so it can generate a unique one in the next run.
        self.interface_names = []

        # List of mesh tunnel links that have been made, and how many times
        # they have been made (by allowing duplicates in the list).
        #
        # Used by Overlay.gre_key() to store the amount of times a specific
        # link has been used to create a GRE tunnel, so it can return a unique
        # key for the next one.
        #
        # Also used by start_ipsec() and stop_ipsec() to generate the IPsec
        # tunnels that are used to encapsulate the GRE tunnels.
        self.mesh_tunnel_links = []

        # List of overlays.
        self.overlays = []

        # IPsec directories and files.
        if self.use_ipsec == True:
            if self.ipsec_manage == True:
                self.ipsec_config_dir = os.path.join(Util.path_root(), "etc")
                self.ipsec_config_file = os.path.join(self.ipsec_config_dir, "ipsec.conf")
            else:
                self.ipsec_config_dir = os.path.join(Util.path_root(), "etc", "ipsec.d")
                self.ipsec_config_file = os.path.join(self.ipsec_config_dir, "l3overlay.conf")

            self.ipsec_secrets_dir = os.path.join(Util.path_root(), "etc")

            self.ipsec_secrets_stub_file = os.path.join(self.ipsec_secrets_dir, "ipsec.secrets")
            self.ipsec_secrets_file = os.path.join(self.ipsec_secrets_dir, "ipsec.l3overlay.secrets")

    def start_directories(self):
        """
        Create the runtime directories for this OverlayDaemon, securely, with
        the correct umask.
        """

        # Set the umask so that any files that this OverlayDaemon creates, will
        # only be readable and writable by itself.
        logging.debug("setting up file and directory handling")

        logging.debug("setting umask")
        os.umask(
            stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP |
            stat.S_IROTH | stat.S_IWOTH | stat.S_IXOTH
        )

        # Create directories.
        logging.debug("creating %s" % self.lib_dir)
        Util.directory_create(self.lib_dir)

        logging.debug("finished setting up file and directory handling")


    def start_ipsec(self):
        """
        Configure and start the strongSwan IPsec tunnel daemon, if enabled.
        """

        if self.use_ipsec == False:
            return

        logging.debug("setting up IPsec daemon management")

        # Create the IPsec config directory.
        logging.debug("creating IPsec configuration directory")
        Util.directory_create(self.ipsec_config_dir)

        # Start doing everything needed to start IPsec.
        logging.debug("configuring ipsec")

        # Save the IPsec configuration.
        logging.debug("saving ipsec configuration to disk")

        with open(self.ipsec_config_file, 'w') as f:
            f.write(self.ipsec_config_template.render(
                file=self.ipsec_config_file,
                mesh_tunnel_links=self.mesh_tunnel_links,
            ))

        # Create the directory where the IPsec secrets are stored.
        logging.debug("creating IPsec secrets directory")
        Util.directory_create(self.ipsec_secrets_dir)

        # This file includes the REAL IPsec secrets file which gets created
        # by l3overlay. Only gets created if ipsec_manage is true.
        if self.ipsec_manage == True:
            logging.debug("saving IPsec secrets stub file to disk")

            with open(self.ipsec_secrets_stub_file, 'w') as f:
                f.write("include %s\n" % self.ipsec_secrets_file)

        # Save the REAL ipsec.secrets.
        logging.debug("saving IPsec secrets file to disk")

        addresses = []

        for local, remote in self.mesh_tunnel_links:
            if local not in addresses:
                addresses.append(local)

            if remote not in addresses:
                addresses.append(remote)

        with open(self.ipsec_secrets_file, 'w') as f:
            f.write(self.ipsec_secrets_template.render(
                file=self.ipsec_secrets_file,
                addresses=addresses,
                secret=self.ipsec_psk,
            ))

        logging.debug("finished configuring ipsec")

        # Start IPsec, or, if it is already running, reload the configuration.
        try:
            ipsec = find_executable("ipsec")

            if ipsec is None:
                raise Exception("cannot find ipsec executable path")

            status = subprocess.call(
                [ipsec, "status"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            if status == 0:
                logging.debug("reloading IPsec")

                logging.debug("reloading IPsec secrets")
                subprocess.check_output(
                    [ipsec, "rereadsecrets"],
                    stderr=subprocess.STDOUT,
                )

                logging.debug("reloading IPsec configuration")
                subprocess.check_output(
                    [ipsec, "reload"],
                    stderr=subprocess.STDOUT,
                )

                logging.debug("finished reloading IPsec")
            elif status == 3:
                logging.debug("starting IPsec")

                subprocess.check_output(
                    [ipsec, "start"],
                    stderr=subprocess.STDOUT,
                )

                logging.debug("finished starting IPsec")
            else:
                raise Exception("unexpected return code for ipsec, status %i" % status)
        except subprocess.CalledProcessError as e:
            logging.error("error detected in process call:\n%s" % e.output.decode('UTF-8'))
            raise

        logging.debug("finished setting up IPsec daemon management")


    def stop(self):
        """
        Shut down all overlays in OverlayDaemon. Once an OverlayDaemon is
        stopped, it cannot be restarted.
        """

        if self.stopped == True:
            return

        self.stopped = True

        logging.info("Stopping daemon...")

        daemon.stop_ipsec()

        # Reverse the list of overlays in order to unload overlays
        # in the opposite order of loading.
        for overlay in reversed(self.overlays):
            overlay.stop()

        daemon.stop_directories()
        logging.info("Stopped.")


    def stop_directories(self):
        """
        Destroy the runtime directories.

        This should be fine, because at this point, there should be no required
        files in the runtime directories.
        """

        logging.debug("removing %s" % self.lib_dir)
        shutil.rmtree(self.lib_dir)


    def stop_ipsec(self):
        """
        Stop the strongSwan IPsec tunnel daemon, and destroy the configuration,
        if enabled.
        """

        if self.use_ipsec == False:
            return

        logging.debug("stopping IPsec daemon management")

        logging.debug("removing IPsec configuration")
        os.remove(self.ipsec_config_file)

        if self.ipsec_manage == True:
            logging.debug("removing IPsec secrets stub file")
            os.remove(self.ipsec_secrets_stub_file)

        logging.debug("removing IPsec secrets file")
        os.remove(self.ipsec_secrets_file)

        try:
            ipsec = find_executable("ipsec")

            if ipsec is None:
                raise Exception("cannot find IPsec executable path")

            if self.ipsec_manage == True:
                # When we manage IPsec, it is safe to stop it completely.
                logging.debug("stopping IPsec")

                subprocess.check_output(
                    [ipsec, "stop"],
                    stderr=subprocess.STDOUT,
                )

                logging.debug("finished stopping IPsec")
            else:
                # When we don't, reload the configuration without the tunnels
                # configured, and shut down all of the tunnels.
                logging.debug("reloading IPsec")

                logging.debug("reloading IPsec secrets")
                subprocess.check_output(
                    [ipsec, "rereadsecrets"],
                    stderr=subprocess.STDOUT,
                )

                logging.debug("reloading IPsec configuration")
                subprocess.check_output(
                    [ipsec, "reload"],
                    stderr=subprocess.STDOUT,
                )

                for local, remote in self.mesh_tunnel_links:
                    logging.debug("shutting down IPsec tunnel %s-%s" % (str(local), str(remote)))
                    subprocess.check_output(
                        [ipsec, "down", "%s-%s" % (str(local), str(remote))],
                        stderr=subprocess.STDOUT,
                    )

                logging.debug("finished reloading IPsec")
        except subprocess.CalledProcessError as e:
            logging.error("error detected in process call:\n%s" % e.output.decode('UTF-8'))
            raise

        logging.debug("finished stopping IPsec daemon management")


    def shutdown(self):
        """
        Permanently shut down this OverlayDaemon.
        Only use if the program is exiting.
        """

        if self.shut_down == True:
            return

        self.shut_down = True

        logging.info("Shutting down daemon...")

        self.stop()
        daemon.ipdb.release()

        logging.info("Shut down.")


    def ipsec_config_add(self, key, value):
        """
        Add a variable to render to the IPsec configuration template.
        """

        logging.debug("adding variable %s to IPsec configuration" % key)
        self.ipsec_config[key] = value
