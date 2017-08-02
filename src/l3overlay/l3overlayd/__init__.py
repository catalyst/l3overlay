#
# IPsec overlay network manager (l3overlay)
# l3overlay/l3overlayd/__init__.py - l3overlayd main routine
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


import argparse
import os
import signal
import stat
import sys

from l3overlay import util

from l3overlay.l3overlayd import daemon


class Main(object):
    '''
    Main method state manager.
    '''

    def __init__(self):
        '''
        Set up the main method state manager internal fields.
        '''

        self.args = None
        self.daemon = None


    def sigterm(self, signum, frame):
        '''
        Shut down the daemon upon shutdown signal, and exit.
        '''

        signal.signal(signal.SIGTERM, signal.SIG_IGN)

        self.daemon.logger.info("handling SIGTERM")

        self.daemon.logger.debug("stopping daemon")
        self.daemon.stop()

        try:
            self.daemon.logger.debug("removing PID file")
            util.file_remove(self.daemon.pid)
        except Exception as e:
            if self.daemon.logger.is_started():
                self.daemon.logger.exception(e)
            raise

        self.daemon.remove()

        sys.exit(0)


    def sigint(self, signum, frame):
        '''
        Shut down the daemon upon keyboard interrupt, and exit.
        '''

        signal.signal(signal.SIGINT, signal.SIG_IGN)

        self.daemon.logger.info("handling SIGINT")

        self.daemon.logger.debug("stopping daemon")
        self.daemon.stop()

        try:
            self.daemon.logger.debug("removing PID file")
            util.file_remove(self.daemon.pid)
        except Exception as e:
            if self.daemon.logger.is_started():
                self.daemon.logger.exception(e)
            raise

        self.daemon.remove()

        sys.exit(0)


    def sighup(self, signum, frame):
        '''
        Shut down the daemon, make a new daemon to reload the configuration,
        and start the new daemon.
        '''

        signal.signal(signal.SIGHUP, signal.SIG_IGN)

        self.daemon.logger.info("handling SIGHUP")

        self.daemon.logger.debug("stopping daemon")
        self.daemon.stop()
        self.daemon.remove()

        self.daemon = daemon.read(self.args)
        self.daemon.setup()

        try:
            util.pid_create(self.daemon.pid)
        except Exception as e:
            if self.daemon.logger.is_started():
                self.daemon.logger.exception(e)
            raise

        self.daemon.logger.debug("starting daemon")
        self.daemon.start()

        self.daemon.logger.info("finished handling SIGHUP")


    @staticmethod
    def argparser():
        '''
        Return a l3overlayd ArgumentParser object.
        '''

        argparser = argparse.ArgumentParser(description="Construct one or more MPLS-like VRF networks using IPsec tunnels and network namespaces.")

        # Configuration options.
        dry_run = argparser.add_mutually_exclusive_group(required=False)
        dry_run.add_argument(
            "-dr", "--dry-run",
            action = "store_true",
            help = "test configuration and daemon without modifying the system",
        )
        dry_run.add_argument(
            "-ndr", "--no-dry-run",
            action = "store_false",
            help = "do NOT test configuration and daemon without modifying the system",
        )

        argparser.add_argument(
            "-ll", "--log-level",
            metavar = "LEVEL",
            type = str,
            default = None,
            help = "use LEVEL as the logging level parameter",
        )

        use_ipsec = argparser.add_mutually_exclusive_group(required=False)
        use_ipsec.add_argument(
            "-ui", "--use-ipsec",
            action = "store_true",
            help = "use IPsec encapsulation on the overlay mesh",
        )
        use_ipsec.add_argument(
            "-nui", "--no-use-ipsec",
            action = "store_false",
            help = "do NOT use IPsec encapsulation on the overlay mesh",
        )

        ipsec_manage = argparser.add_mutually_exclusive_group(required=False)
        ipsec_manage.add_argument(
            "-im", "--ipsec-manage",
            action = "store_true",
            help = "operate in IPsec daemon management mode",
        )
        ipsec_manage.add_argument(
            "-nim", "--no-ipsec-manage",
            action = "store_false",
            help = "do NOT operate in IPsec daemon management mode",
        )

        # No way we're having ipsec-psk as an argument, for obvious reasons.

        # Directory paths.
        argparser.add_argument(
            "-ocd", "--overlay-conf-dir",
            metavar = "DIR",
            type = str,
            default = None,
            help = "use DIR as the overlay conf search directory",
        )

        argparser.add_argument(
            "-td", "--template-dir",
            metavar = "DIR",
            type = str,
            default = None,
            help = "use DIR as the configuration template search directory",
        )

        argparser.add_argument(
            "-fsd", "--fwbuilder-script-dir",
            metavar = "DIR",
            type = str,
            default = None,
            help = "use DIR as the fwbuilder script search directory",
        )

        argparser.add_argument(
            "-Ld", "--lib-dir",
            metavar = "DIR",
            type = str,
            default = None,
            help = "use DIR as the runtime data directory",
        )

        # File paths.
        argparser.add_argument(
            "-gc", "--global-conf",
            metavar = "FILE",
            type = str,
            default = None,
            help = "use FILE as the global configuration file",
        )

        argparser.add_argument(
            "-oc", "--overlay-conf",
            metavar = "FILE",
            type = str,
            nargs = "+",
            default = None,
            help = "configure the overlay defined in FILE, disables overlay config directory searching",
        )

        argparser.add_argument(
            "-l", "--log",
            metavar = "FILE",
            type = str,
            default = None,
            help = "log output to FILE",
        )

        argparser.add_argument(
            "-p", "--pid",
            metavar = "FILE",
            type = str,
            default = None,
            help = "write the daemon PID to FILE",
        )

        argparser.add_argument(
            "-ic", "--ipsec-conf",
            metavar = "FILE",
            type = str,
            default = None,
            help = "write IPsec configuration to FILE",
        )
        argparser.add_argument(
            "-is", "--ipsec-secrets",
            metavar = "FILE",
            type = str,
            default = None,
            help = "write IPsec secrets to FILE",
        )

        return argparser


    def main(self):
        '''
        Main method.
        '''

        # Parse optional arguments, and return the final values which will be used
        # in l3overlayd configuration.
        self.args = vars(Main.argparser().parse_args())

        # Configure the umask of this process so, by default, it will securely
        # create files.
        os.umask(
            stat.S_IRGRP|stat.S_IWGRP|stat.S_IXGRP|stat.S_IROTH|stat.S_IWOTH|stat.S_IXOTH
        )

        # Create the daemon object, which tracks l3overlay state.
        # After the daemon object is created, we can log output.
        self.daemon = daemon.read(self.args)
        self.daemon.setup()

        # Time to start up the daemon!
        self.daemon.start()

        # On exceptions: log output, and quit.
        try:
            # Create the PID file for this daemon.
            if not self.args["dry_run"]:
                util.pid_create(self.daemon.pid)

            # Set up process signal handlers.
            self.daemon.logger.debug("setting up signal handlers")
            signal.signal(signal.SIGTERM, self.sigterm)
            signal.signal(signal.SIGINT, self.sigint)
            signal.signal(signal.SIGHUP, self.sighup)
        except Exception as e:
            if self.daemon.logger.is_started():
                self.daemon.logger.exception(e)
            raise

        # We're done! Time to block and wait for signals.
        while True:
            self.daemon.logger.debug("waiting for signal")
            signal.pause()


def main():
    '''
    Call the main method in the Main object.
    '''

    Main().main()
