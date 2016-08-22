#
# IPsec overlay network manager (l3overlay)
# l3overlay/overlay/process/bgp.py - BGP process manager
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
import re
import signal
import subprocess
import socket

from l3overlay import util

from l3overlay.overlay.interface.bgp import BGP
from l3overlay.overlay.interface.dummy import Dummy
from l3overlay.overlay.interface.overlay_link import OverlayLink
from l3overlay.overlay.interface.tunnel import Tunnel
from l3overlay.overlay.interface.tuntap import Tuntap
from l3overlay.overlay.interface.veth import VETH
from l3overlay.overlay.interface.vlan import VLAN

from l3overlay.util.exception.l3overlayerror import L3overlayError

from l3overlay.util.worker import Worker


RECV_MAX = 1024


class UnexpectedResponseError(L3overlayError):
    def __init__(self, action, data):
        super().__init__("unexpected response from BIRD when %s:\n%s" % (action, data))


class Process(Worker):
    '''
    BGP process manager.
    '''

    def __init__(self, daemon, overlay):
        '''
        Set internal fields for the BGP process.
        '''

        super().__init__()

        self.dry_run = daemon.dry_run

        self.log_level = daemon.log_level

        self.template_dir = daemon.template_dir

        self.logger = overlay.logger
        self.name = overlay.name
        self.netns = overlay.netns

        self.description = "BGP process for overlay '%s'" % self.name

        self.asn = overlay.asn
        self.linknet_pool = overlay.linknet_pool

        self.mesh_tunnels = tuple(overlay.mesh_tunnels)
        self.interfaces = tuple(overlay.interfaces)

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

        self.bird = util.command_path("bird") if not self.dry_run else None
        self.bird6 = util.command_path("bird6") if not self.dry_run else None


    def bird_config_add(self, bird_config, key, value):
        '''
        Add a value to a list stored at the given key in
        the given BIRD configuration dictionary.
        '''

        if key in bird_config:
            if not isinstance(bird_config[key], list):
                bird_config[key] = [bird_config[key]]
            if isinstance(value, list):
                bird_config[key].extend(value)
            else:
                bird_config[key].append(value)
        else:
            bird_config[key] = [value]


    def start(self):
        '''
        Start the BGP process.
        '''

        self.set_starting()

        self.logger.info("starting BGP process")

        self.logger.debug("creating BIRD control socket directory")
        if not self.dry_run:
            util.directory_create(self.bird_ctl_dir)

        self.logger.debug("creating BIRD configuration directory")
        if not self.dry_run:
            util.directory_create(self.bird_conf_dir)

        self.logger.debug("creating BIRD logging directory")
        if not self.dry_run:
            util.directory_create(self.bird_log_dir)

        self.logger.debug("creating BIRD PID file directory")
        if not self.dry_run:
            util.directory_create(self.bird_pid_dir)

        self.logger.debug("configuring BIRD")

        bird_config = {}
        bird6_config = {}

        if util.ip_network_is_v6(self.linknet_pool):
            bird6_config["mesh_tunnels"] = self.mesh_tunnels
        else:
            bird_config["mesh_tunnels"] = self.mesh_tunnels

        for interface in self.interfaces:
            bc = None
            if interface.is_ipv6():
                bc = bird6_config
            else:
                bc = bird_config

            if isinstance(interface, BGP):
                self.bird_config_add(bc, "bgps", interface)
            elif isinstance(interface, Dummy):
                self.bird_config_add(bc, "dummies", interface)
            elif isinstance(interface, OverlayLink):
                self.bird_config_add(bc, "overlay_links", interface)
            elif isinstance(interface, Tunnel):
                self.bird_config_add(bc, "tunnels", interface)
            elif isinstance(interface, Tuntap):
                self.bird_config_add(bc, "tuntaps", interface)
            elif isinstance(interface, VETH):
                self.bird_config_add(bc, "veths", interface)
            elif isinstance(interface, VLAN):
                self.bird_config_add(bc, "vlans", interface)

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

        if not self.dry_run:
            with open(bird_conf, "w") as f:
                f.write(self.bird_conf_template.render(bird_config))

        if util.pid_exists(pid_file=bird_pid):
            # Note that socket.error.errno == errno.ECONNREFUSED
            # is not being ignored here. If we got this far, we have
            # a valid PID file, therefore we should have a valid CTL
            # file.
            self.logger.debug("connecting to the BIRD control socket '%s'" % bird_ctl)

            sock = None
            data = None

            if self.dry_run:
                data = "0001 BIRD 1.4.0 ready.\n"
            else:
                sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                sock.connect(bird_ctl)

                data = sock.recv(RECV_MAX).decode("UTF-8")

            if not re.match("0001 BIRD [0-9.]* ready.\n", data):
                raise UnexpectedResponseError("connecting", data)

            self.logger.debug("reloading BIRD configuration")

            if self.dry_run:
                data = "0002-Reading configuration from %s\n0003 Reconfigured" % bird_conf
            else:
                sock.send(bytes("configure \"%s\"\n" % bird_conf, 'UTF-8'))
                data = sock.recv(RECV_MAX).decode("UTF-8")

            if ("0002-Reading configuration from %s" % bird_conf not in data or
                        ("0003 Reconfigured" not in data and
                                "0004 Reconfiguration in progress" not in data)):
                raise UnexpectedResponseError("reloading config", data)

            if not self.dry_run:
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

        self.set_stopping()

        self.logger.info("stopping BGP process")

        if not self.dry_run:
            pid = util.pid_get(pid_file=self.bird_pid)
            pid6 = util.pid_get(pid_file=self.bird6_pid)

            if pid:
                os.kill(pid, signal.SIGTERM)
            if pid6:
                os.kill(pid6, signal.SIGTERM)

        self.logger.debug("removing BIRD control socket directory")
        if not self.dry_run:
            util.directory_remove(self.bird_ctl_dir)

        self.logger.debug("removing BIRD configuration directory")
        if not self.dry_run:
            util.directory_remove(self.bird_conf_dir)

        self.logger.debug("removing BIRD logging directory")
        if not self.dry_run:
            util.directory_remove(self.bird_log_dir)

        self.logger.debug("removing BIRD PID file directory")
        if not self.dry_run:
            util.directory_remove(self.bird_pid_dir)

        self.logger.info("finished stopping BGP process")

        self.set_stopped()

Worker.register(Process)


def create(daemon, overlay):
    '''
    Create a BGP process object.
    '''

    return Process(daemon, overlay)
