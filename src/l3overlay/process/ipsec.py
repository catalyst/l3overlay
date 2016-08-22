#
# IPsec overlay network manager (l3overlay)
# l3overlay/ipsec/process/ipsec.py - IPsec process manager
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


import subprocess

from l3overlay import util

from l3overlay.util.exception.l3overlayerror import L3overlayError

from l3overlay.util.worker import Worker


class UnexpectedReturnCodeError(L3overlayError):
    def __init__(self, command, code):
        super().__init__("unexpected '%s' return code: %i" % (command, code))


class Process(Worker):
    '''
    IPsec process manager.
    '''

    description = "ipsec process"


    def __init__(self, daemon):
        '''
        Set internal fields for the IPsec process.
        '''

        super().__init__()

        self.dry_run = daemon.dry_run

        self.logger = daemon.logger

        self.use_ipsec = daemon.use_ipsec
        self.ipsec_manage = daemon.ipsec_manage
        self.ipsec_psk = daemon.ipsec_psk

        self.template_dir = daemon.template_dir

        self.ipsec_conf = daemon.ipsec_conf
        self.ipsec_secrets = daemon.ipsec_secrets

        self.ipsec_conf_template = util.template_read(self.template_dir, "ipsec.conf")
        self.ipsec_secrets_template = util.template_read(self.template_dir, "ipsec.secrets")

        # Create a dictionary which maps the name of the IPsec
        # connection to a tuple containing the local and remote addresses.
        self.mesh_conns = dict(zip(
            ["%s-%s" % (m[0], m[1]) for m in daemon.mesh_links],
            daemon.mesh_links,
        ))

        self.ipsec = util.command_path("ipsec") if not self.dry_run else util.command_path("true")


    def start(self):
        '''
        Start the IPsec process.
        '''

        if not self.use_ipsec:
            return

        self.set_starting()

        self.logger.info("starting IPsec process")

        self.logger.debug("creating IPsec configuration file '%s'" % self.ipsec_conf)
        if not self.dry_run:
            with open(self.ipsec_conf, "w") as f:
                f.write(self.ipsec_conf_template.render(
                    file=self.ipsec_conf,
                    mesh_conns=self.mesh_conns,
                ))

        self.logger.debug("creating IPsec secrets file '%s'" % self.ipsec_secrets)
        addresses = set()
        for local, remote in self.mesh_conns.values():
            addresses.add(local)
            addresses.add(remote)
        if not self.dry_run:
            with open(self.ipsec_secrets, "w") as f:
                f.write(self.ipsec_secrets_template.render(
                    file=self.ipsec_secrets,
                    addresses=addresses,
                    secret=self.ipsec_psk,
                ))

        self.logger.debug("checking IPsec status")
        status = subprocess.call(
            [self.ipsec, "status"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        if status == 0:
            self.logger.debug("reloading IPsec secrets")
            subprocess.check_output([self.ipsec, "rereadsecrets"], stderr=subprocess.STDOUT)

            self.logger.debug("reloading IPsec configuration")
            subprocess.check_output([self.ipsec, "reload"], stderr=subprocess.STDOUT)

        elif status == 3:
            self.logger.debug("starting IPsec")
            subprocess.check_output([self.ipsec, "start"], stderr=subprocess.STDOUT)

        else:
            raise UnexpectedReturnCodeError("%s status" % self.ipsec, status)

        self.logger.info("finished starting IPsec process")

        self.set_started()


    def stop(self):
        '''
        Stop the IPsec process.
        '''

        if not self.use_ipsec:
            return

        self.set_stopping()

        self.logger.info("stopping IPsec process")

        self.logger.debug("removing IPsec configuration file '%s'" % self.ipsec_conf)
        if not self.dry_run:
            util.file_remove(self.ipsec_conf)

        self.logger.debug("removing IPsec secrets file '%s'" % self.ipsec_secrets)
        if not self.dry_run:
            util.file_remove(self.ipsec_secrets)

        if self.ipsec_manage:
            # When we manage IPsec, it is safe to stop it completely.
            self.logger.debug("stopping IPsec")
            if not self.dry_run:
                subprocess.check_output([ipsec, "stop"], stderr=subprocess.STDOUT)

        else:
            # When we don't, reload the configuration without the tunnels
            # configured, and shut down all of the tunnels.
            self.logger.debug("reloading IPsec secrets")
            if not self.dry_run:
                subprocess.check_output([self.ipsec, "rereadsecrets"], stderr=subprocess.STDOUT)

            self.logger.debug("reloading IPsec configuration")
            if not self.dry_run:
                subprocess.check_output([self.ipsec, "reload"], stderr=subprocess.STDOUT)

            for conn in self.mesh_conns:
                self.logger.debug("shutting down IPsec tunnel '%s'" % conn)
                if not self.dry_run:
                    subprocess.check_output(
                        [self.ipsec, "down", conn],
                        stderr=subprocess.STDOUT,
                    )

        self.logger.info("finished stopping IPsec process")

        self.set_stopped()

Worker.register(Process)


def create(daemon):
    '''
    Create a IPsec process object.
    '''

    return Process(daemon)
