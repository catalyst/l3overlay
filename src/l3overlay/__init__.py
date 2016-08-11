#
# IPsec overlay network manager (l3overlay)
# l3overlay/__init__.py - main function
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


import argparse
import os
import stat


def main():

    # Parse optional arguments, and return the final values which will be used
    # in l3overlayd configuration.
    argparser = argparse.ArgumentParser(description="Construct one or more MPLS-like VRF networks using IPsec tunnels and network namespaces.")

    argparser.add_argument(
        '-gc', '--global-conf',
        metavar='FILE',
        type=str,
        default=None,
        help="use FILE as the global configuration file",
    )

    argparser.add_argument(
        '-ocd', '--overlay-conf-dir',
        metavar='DIR',
        type=str,
        default=None,
        help="use DIR as the overlay conf search directory",
    )

    argparser.add_argument(
        '-oc', '--overlay-conf',
        metavar='FILE',
        type=str,
        nargs='+',
        default=None,
        help="configure the overlay defined in FILE, disables overlay config directory searching",
    )

    argparser.add_argument(
        '-td', '--template-dir',
        metavar='DIR',
        type=str,
        default=None,
        help="use DIR as the configuration template search directory",
    )

    argparser.add_argument(
        '-fsd', '--fwbuilder-script-dir',
        metavar='DIR',
        type=str,
        default=None,
        help="use DIR as the fwbuilder script search directory",
    )

    argparser.add_argument(
        '-Ld', '--lib-dir',
        metavar='DIR',
        type=str,
        default=None,
        help="use DIR as the runtime data directory",
    )

    argparser.add_argument(
        '-lf', '--log-file',
        metavar='FILE',
        type=str,
        default=None,
        help="log output to FILE",
    )

    argparser.add_argument(
        '-pf', '--pid-file',
        metavar='FILE',
        type=str,
        default=None,
        help="use FILE as the PID lock file",
    )

    args = argparser.parse_args()


    # Configure the umask of this process so, by default, it will securely
    # create files.
    os.umask(
        stat.S_IRGRP|stat.S_IWGRP|stat.S_IXGRP|stat.S_IROTH|stat.S_IWOTH|stat.S_IXOTH
    )


    # Create the daemon object, which tracks l3overlay state.
    # After the daemon object is created, we can log output.
    daemon = Daemon(args)

    # Set up process signal handlers.
    def sigterm(signum, frame):
        '''
        Shut down the daemon, and exit.
        '''

        signal.signal(signal.SIGTERM, signal.SIG_IGN)

        daemon.logger.info("handling SIGINT")

        daemon.logger.debug("stopping daemon")
        daemon.stop()

        daemon.logger.debug("removing PID file")
        util.file_remove(daemon.pid)

        logger.info("exiting")
        sys.exit(0)

    def sigint(signum, frame):
        '''
        Alias to sigterm.
        '''

        signal.signal(signal.SIGINT, signal.SIG_IGN)

        daemon.logger.info("handling SIGINT")

        daemon.logger.debug("stopping daemon")
        daemon.stop()

        daemon.logger.debug("removing PID file")
        util.file_remove(daemon.pid)

        logger.info("exiting")
        sys.exit(0)

    def sighup(signum, frame):
        '''
        Shut down the daemon, make a new daemon to reload the configuration,
        and start the new daemon.
        '''

        signal.signal(signal.SIGHUP, signal.SIG_IGN)

        daemon.logger.info("handling SIGHUP")

        daemon.logger.debug("stopping daemon")
        daemon.stop()

        daemon = Daemon(args)
        logger = daemon.logger

        daemon.logger.debug("starting daemon")
        daemon.start()

        daemon.logger.info("finished handling SIGHUP")

    daemon.logger.debug("setting up signal handlers")
    signal.signal(signal.SIGTERM, sigterm)
    signal.signal(signal.SIGINT, sigint)
    signal.signal(signal.SIGHUP, sighup)


    # We're done! Time to block and wait for signals.
    while True:
        daemon.logger.debug("waiting for signal")
        signal.pause()
