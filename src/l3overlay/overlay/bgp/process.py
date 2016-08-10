#
# IPsec overlay network manager (l3overlay)
# l3overlay/overlay/bgp/process.py - BGP process manager
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

from l3overlay import util

from l3overlay.util.worker import Worker


class Process(Worker):
    '''
    BGP process manager.
    '''

    def __init__(self, daemon, overlay):
        '''
        Set internal fields for the BGP process.
        '''

        self().__init__()

        self.logger = overlay.logger

        self.mesh_tunnels = tuple(overlay.mesh_tunnels)
        self.interfaces = tuple(overlay.interfaces)
        self.bgps = tuple(overlay.bgps)

        self.template_dir = daemon.template_dir

        self.bird_ctl = os.path.join(overlay.root_dir, "run", "bird", "bird.ctl")
        self.bird_conf = os.path.join(overlay.root_dir, "etc", "bird", "bird.conf")
        self.bird_log = os.path.join(overlay.root_dir, "var", "log", "bird", "bird.log")
        self.bird_pid = os.path.join(overlay.root_dir, "run", "bird", "bird.pid")

        self.bird6_ctl = os.path.join(overlay.root_dir, "run", "bird", "bird6.ctl")
        self.bird6_conf = os.path.join(overlay.root_dir, "etc", "bird", "bird6.conf")
        self.bird6_log = os.path.join(overlay.root_dir, "var", "log", "bird", "bird6.log")
        self.bird6_pid = os.path.join(overlay.root_dir, "run", "bird", "bird6.pid")

        self.bird_conf_template = util.template_read(self.template_dir, "bird.conf")

        self.bird = util.command_path("bird")
        self.bird6 = util.command_path("bird6")


    def start(self):
        '''
        Start the BGP process.
        '''

        if self.starting() or self.running():
            raise RuntimeError("BGP process started twice")

        self.set_starting()

        self.logger.info("starting BGP process")

        if self.bird_config:
          logging.debug("creating BIRD configuration directory")
          Util.directory_create(bird_config_dir)

          logging.debug("creating BIRD socket directory")
          Util.directory_create(bird_socket_dir)

          logging.debug("creating BIRD log directory")
          Util.directory_create(bird_log_dir)

        if self.bird6_config:
          logging.debug("creating BIRD6 configuration directory")
          Util.directory_create(bird6_config_dir)

          logging.debug("creating BIRD6 socket directory")
          Util.directory_create(bird6_socket_dir)

          logging.debug("creating BIRD6 log directory")
          Util.directory_create(bird6_log_dir)

        # Actual configuration time.
        logging.debug("configuring BIRD")

        # Add required parameters to the BIRD configuration.
        if self.bird_config:
            self.bird_config_add(key='overlay', value=self.name)
            self.bird_config_add(key='file', value=bird_config_file)
            self.bird_config_add(key='netns', value=self.netns_name)
            self.bird_config_add(key='asn', value=self.asn)
            self.bird_config_add(key='logging_level', value=self.logging_level)
            self.bird_config_add(key='log_file', value=bird_log_file)

        if self.bird6_config:
            self.bird6_config_add(key='overlay', value=self.name)
            self.bird6_config_add(key='file', value=bird6_config_file)
            self.bird6_config_add(key='netns', value=self.netns_name)
            self.bird6_config_add(key='asn', value=self.asn)
            self.bird6_config_add(key='logging_level', value=self.logging_level)
            self.bird6_config_add(key='log_file', value=bird6_log_file)

        # Save the BIRD configuration.
        if self.bird_config:
            logging.debug("saving bird configuration to disk")

            with open(bird_config_file, 'w') as f:
                f.write(self.bird_config_template.render(self.bird_config))

        if self.bird6_config:
            logging.debug("saving bird6 configuration to disk")

            with open(bird6_config_file, 'w') as f:
                f.write(self.bird_config_template.render(self.bird6_config))

        logging.debug("finished configuring BIRD")

        # Start the BIRD routing daemon for both IPv4 and IPv6.
        if self.bird_config:
            bird = find_executable("bird")

            if bird is None:
                raise Exception("cannot find bird executable path")

            self.start_bird_daemon(
                bird,
                bird_config_file,
                bird_socket_file,
                bird_pid_file,
            )

        if self.bird6_config:
            bird6 = find_executable("bird6")

            if bird6 is None:
                raise Exception("cannot find bird6 executable path")

            self.start_bird_daemon(
                bird6,
                bird6_config_file,
                bird6_socket_file,
                bird6_pid_file,
            )

        self.logger.info("finished starting BGP process")

        self.set_running()


    def stop(self):
        '''
        Stop the BGP process.
        '''

        if not self.use_ipsec:
            return

        if not self.running():
            raise RuntimeError("BGP process not yet started")

        if self.stopped():
            raise RuntimeError("BGP process stopped twice")

        self.set_stopping()

        self.logger.info("stopping BGP process")

        # do stuff

        self.logger.info("finished stopping BGP process")

        self.set_stopped()

Worker.register(Process)


def create(daemon, overlay):
    '''
    Create a BGP process object.
    '''

    return Process(daemon, overlay)
