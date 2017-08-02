#
# IPsec overlay network manager (l3overlay)
# l3overlay/l3overlayd/overlay/process/bgp.py - BGP process manager
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
import re
import signal
import subprocess
import socket

from l3overlay import util

from l3overlay.l3overlayd.overlay.static_interface.bgp import BGP
from l3overlay.l3overlayd.overlay.static_interface.dummy import Dummy
from l3overlay.l3overlayd.overlay.static_interface.overlay_link import OverlayLink
from l3overlay.l3overlayd.overlay.static_interface.tunnel import Tunnel
from l3overlay.l3overlayd.overlay.static_interface.tuntap import Tuntap
from l3overlay.l3overlayd.overlay.static_interface.veth import VETH
from l3overlay.l3overlayd.overlay.static_interface.vlan import VLAN

from l3overlay.l3overlayd.process import ProcessError

from l3overlay.util.exception import L3overlayError

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

        super().__init__(use_setup=True)

        self.daemon = daemon

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
        self.static_interfaces = tuple(overlay.static_interfaces)

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

        self.bird = util.command_path("bird") if not self.dry_run else "/usr/sbin/bird"
        self.bird6 = util.command_path("bird6") if not self.dry_run else "/usr/sbin/bird6"

        self.bird_config = {}
        self.bird6_config = {}


    @staticmethod
    def _bird_config_add(bird_config, key, value):
        '''
        Add a value to the given BIRD config dict.
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


    def bird_config_add(self, key, value):
        '''
        Add a value to this BGP process's BIRD config.
        '''

        Process._bird_config_add(self.bird_config, key, value)


    def bird6_config_add(self, key, value):
        '''
        Add a value to this BGP process's BIRD6 config.
        '''

        Process._bird_config_add(self.bird_config, key, value)


    def setup(self):
        '''
        Setup the BGP process.
        '''

        self.set_settingup()

        self.logger.info("setting BGP process")

        self.logger.debug("configuring BIRD")

        if util.ip_network_is_v6(self.linknet_pool):
            self.bird6_config["mesh_tunnels"] = self.mesh_tunnels
        else:
            self.bird_config["mesh_tunnels"] = self.mesh_tunnels

        for si in self.static_interfaces:
            bc_add = None
            if si.is_ipv6():
                bc_add = self.bird_config_add
            else:
                bc_add = self.bird6_config_add

            if isinstance(si, BGP):
                bc_add("bgps", si)
            elif isinstance(si, Dummy):
                bc_add("dummies", si)
            elif isinstance(si, Tunnel):
                bc_add("tunnels", si)
            elif isinstance(si, Tuntap):
                bc_add("tuntaps", si)
            elif isinstance(si, VETH):
                bc_add("veths", si)
            elif isinstance(si, VLAN):
                bc_add("vlans", si)
            elif isinstance(si, OverlayLink):
                bc_add("overlay_links", si)
                # Add the corresponding BGP configuration for
                # the overlay link to the inner overlay's BGP process.
                inner_overlay = self.daemon.overlays[si.inner_overlay_name]
                if si.is_ipv6():
                    inner_overlay.bgp_process.bird_config_add("overlay_links", si)
                else:
                    inner_overlay.bgp_process.bird6_config_add("overlay_links", si)

        self.logger.info("finished setting up BGP process")

        self.set_setup()


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

        if self.bird_config:
            self.bird_config["router_id"] = str(self.mesh_tunnels[0].virtual_local)
            self._start_bird_daemon(
                self.bird,
                self.bird_conf,
                self.bird_config,
                self.bird_log,
                self.bird_ctl,
                self.bird_pid,
            )

        if self.bird6_config:
            self.bird6_config["router_id"] = "192.0.2.1"
            self._start_bird_daemon(
                self.bird6,
                self.bird6_conf,
                self.bird6_config,
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
            bird_command = [
                bird,
                "-c", bird_conf,
                "-s", bird_ctl,
                "-P", bird_pid,
            ]

            self.logger.debug("starting BIRD using command '%s'" %
                    str.join(" ", bird_command))

            bird_process = self.netns.Popen(
                bird_command,
                stdout = subprocess.PIPE,
                stderr = subprocess.PIPE,
            )

            try:
                stdout, stderr = bird_process.communicate()

                if bird_process.returncode != 0:
                    raise ProcessError(
                        "'%s' encountered an error on execution" % bird,
                        bird_process,
                        stdout,
                        stderr,
                    )

                if stdout:
                    self.logger.debug("stdout:\n%s" % (stdout.decode("UTF-8")))

                if stderr:
                    self.logger.debug("stderr:\n%s" % (stderr.decode("UTF-8")))

            finally:
                bird_process.release()


    def stop(self):
        '''
        Stop the BGP process.
        '''

        self.set_stopping()

        self.logger.info("stopping BGP process")

        if not self.dry_run:
            util.pid_kill(pid_file=self.bird_pid)
            util.pid_kill(pid_file=self.bird6_pid)

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
