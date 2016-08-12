#
# IPsec overlay network manager (l3overlay)
# l3overlay/overlay/bgp/__init__.py - BGP process manager
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
import re
import signal
import subprocess
import socket

from l3overlay import util

from l3overlay.util.worker import Worker


RECV_MAX = 1024


class Process(Worker):
    '''
    BGP process manager.
    '''

    def __init__(self, daemon, overlay):
        '''
        Set internal fields for the BGP process.
        '''

        super().__init__()

        self.log_level = daemon.log_level

        self.template_dir = daemon.template_dir

        self.logger = overlay.logger
        self.name = overlay.name
        self.netns = overlay.netns

        self.asn = overlay.asn
        self.linknet_pool = overlay.linknet_pool

        self.mesh_tunnels = tuple(overlay.mesh_tunnels)
        self.interfaces = tuple(overlay.interfaces)
        self.bgps = tuple(overlay.bgps)

        self.bird_ctl_dir = os.path.join(overlay.root_dir, "run", "bird")
        self.bird_conf_dir = os.path.join(overlay.root_dir, "etc", "bird")
        self.bird_log_dir = os.path.join(overlay.root_dir, "var", "log", "bird")
        self.bird_pid_dir = os.path.join(overlay.root_dir, "run", "bird")

        self.bird_ctl = os.path.join(self.bird_ctl_dir, "bird.ctl")
        self.bird_conf = os.path.join(self.bird_conf_dir, "bird.conf")
        self.bird_log = os.path.join(self.bird_log_dir, "bird.log")
        self.bird_pid = os.path.join(self.bird_pid_dir, "bird.pid")

        self.bird6_ctl = os.path.join(self.bird_ctl_dir, "bird6.ctl")
        self.bird6_conf = os.path.join(self.bird_conf_dir, "bird6.conf")
        self.bird6_log = os.path.join(self.bird_log_dir, "bird6.log")
        self.bird6_pid = os.path.join(self.bird_pid_dir, "bird6.pid")

        self.bird_conf_template = util.template_read(self.template_dir, "bird.conf")

        self.bird = util.command_path("bird")
        self.bird6 = util.command_path("bird6")


    def start(self):
        '''
        Start the BGP process.
        '''

        if self.is_starting() or self.is_started():
            raise RuntimeError("BGP process for overlay '%s' started twice" % self.name)

        self.set_starting()

        self.logger.info("starting BGP process")

        self.logger.debug("creating BIRD control socket directory")
        util.directory_create(self.bird_ctl_dir)

        self.logger.debug("creating BIRD configuration directory")
        util.directory_create(self.bird_conf_dir)

        self.logger.debug("creating BIRD logging directory")
        util.directory_create(self.bird_log_dir)

        self.logger.debug("creating BIRD PID file directory")
        util.directory_create(self.bird_pid_dir)

        self.logger.debug("configuring BIRD")

        bird_config = {}
        bird6_config = {}

        if util.ip_network_is_v6(self.linknet_pool):
            bird6_config["mesh_tunnels"] = self.mesh_tunnels
        else:
            bird_config["mesh_tunnels"] = self.mesh_tunnels

        for interface in self.interfaces:
            if interface.is_ipv6():
                if "interfaces" not in bird6_config:
                    bird6_config["interfaces"] = []
                bird6_config["interfaces"].append(interface)
            else:
                if "interfaces" not in bird_config:
                    bird_config["interfaces"] = []
                bird_config["interfaces"].append(interface)

        if bird_config:
            self._start_bird_daemon(
                self.bird,
                self.bird_conf,
                bird_config,
                self.bird_log,
                self.bird_ctl,
                self.bird_pid,
            )

        if bird6_config:
            self._start_bird_daemon(
                self.bird6,
                self.bird6_conf,
                bird6_config,
                self.bird6_log,
                self.bird6_ctl,
                self.bird6_pid,
            )

        self.logger.info("finished starting BGP process")

        self.set_started()


    def _start_bird_daemon(self, bird, bird_conf, bird_config, bird_log, bird_ctl, bird_pid):
        '''
        Start (or reload) a BIRD daemon using the given parameters.
        '''

        self.logger.debug("creating BIRD configuration file '%s'" % bird_conf)

        bird_config["conf"] = bird_conf
        bird_config["log"] = bird_log
        bird_config["log_level"] = self.log_level
        bird_config["overlay"] = self.name
        bird_config["asn"] = self.asn

        with open(bird_conf, "w") as f:
            f.write(self.bird_conf_template.render(bird_config))

        if util.pid_exists(pid_file=bird_pid):
            # Note that socket.error.errno == errno.ECONNREFUSED
            # is not being ignored here. If we got this far, we have
            # a valid PID file, therefore we should have a valid CTL
            # file.
            self.logger.debug("connecting to the BIRD control socket '%s'" % bird_ctl)
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.connect(bird_ctl)

            data = sock.recv(RECV_MAX).decode("UTF-8")
            if not re.match("0001 BIRD [0-9.]* ready.\n", data):
                raise RuntimeError(
                        "unexpected response from BIRD when connecting:\n%s" % data)

            self.logger.debug("reloading BIRD configuration")
            sock.send(bytes("configure \"%s\"\n" % bird_conf, 'UTF-8'))

            data = sock.recv(RECV_MAX).decode("UTF-8")
            if ("0002-Reading configuration from %s" % bird_conf not in data or
                        ("0003 Reconfigured" not in data and
                                "0004 Reconfiguration in progress" not in data)):
                raise RuntimeError(
                        "unexpected response from BIRD when reloading config:\n%s" % data)

            sock.close()

        else:
            self.logger.debug("starting BIRD using executable '%s'" % bird)

            bird = self.netns.Popen([
                bird,
                    "-c", self.bird_conf,
                    "-s", self.bird_ctl,
                    "-P", self.bird_pid,
            ], stderr=subprocess.STDOUT)

            bird.wait()
            bird.release()


    def stop(self):
        '''
        Stop the BGP process.
        '''

        if not self.is_started():
            raise RuntimeError("BGP process for overlay '%s' not yet started" % self.name)

        if self.is_stopped() or self.is_stopped():
            raise RuntimeError("BGP process for overlay '%s' stopped twice" % self.name)

        self.set_stopping()

        self.logger.info("stopping BGP process")

        pid = util.pid_get(pid_file=self.bird_pid)
        pid6 = util.pid_get(pid_file=self.bird6_pid)

        if pid:
            os.kill(pid, signal.SIGTERM)
        if pid6:
            os.kill(pid6, signal.SIGTERM)

        self.logger.debug("removing BIRD control socket directory")
        util.directory_remove(self.bird_ctl_dir)

        self.logger.debug("removing BIRD configuration directory")
        util.directory_remove(self.bird_conf_dir)

        self.logger.debug("removing BIRD logging directory")
        util.directory_remove(self.bird_log_dir)

        self.logger.debug("removing BIRD PID file directory")
        util.directory_remove(self.bird_pid_dir)

        self.logger.info("finished stopping BGP process")

        self.set_stopped()

Worker.register(Process)


def create(daemon, overlay):
    '''
    Create a BGP process object.
    '''

    return Process(daemon, overlay)
