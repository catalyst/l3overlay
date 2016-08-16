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
import signal
import stat
import sys

import l3overlay.daemon


args = None
l3overlay_daemon = None


def sigterm(signum, frame):
    '''
    Shut down the daemon upon shutdown signal, and exit.
    '''

    global l3overlay_daemon

    signal.signal(signal.SIGTERM, signal.SIG_IGN)

    l3overlay_daemon.logger.info("handling SIGINT")

    l3overlay_daemon.logger.debug("stopping daemon")
    l3overlay_daemon.stop()

    l3overlay_daemon.logger.debug("removing PID file")
    util.file_remove(l3overlay_daemon.pid)

    l3overlay_daemon.remove()

    sys.exit(0)


def sigint(signum, frame):
    '''
    Shut down the daemon upon keyboard interrupt, and exit.
    '''

    global l3overlay_daemon

    signal.signal(signal.SIGINT, signal.SIG_IGN)

    l3overlay_daemon.logger.info("handling SIGINT")

    l3overlay_daemon.logger.debug("stopping daemon")
    l3overlay_daemon.stop()

    l3overlay_daemon.logger.debug("removing PID file")
    util.file_remove(l3overlay_daemon.pid)

    l3overlay_daemon.remove()

    sys.exit(0)


def sighup(signum, frame):
    '''
    Shut down the daemon, make a new daemon to reload the configuration,
    and start the new daemon.
    '''

    global args
    global l3overlay_daemon

    signal.signal(signal.SIGHUP, signal.SIG_IGN)

    l3overlay_daemon.logger.info("handling SIGHUP")

    l3overlay_daemon.logger.debug("stopping daemon")
    l3overlay_daemon.stop()
    l3overlay_daemon.remove()

    l3overlay_daemon = l3overlay.daemon.read(args)
    l3overlay_daemon.setup()

    util.pid_create(l3overlay_daemon.pid)

    l3overlay_daemon.logger.debug("starting daemon")
    l3overlay_daemon.start()

    l3overlay_daemon.logger.info("finished handling SIGHUP")


def main():
    global args
    global l3overlay_daemon

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
    l3overlay_daemon = l3overlay.daemon.read(args)
    l3overlay_daemon.setup()

    # On exceptions: log output, and quit.
    try:
        # Time to start up the daemon!
        l3overlay_daemon.start()

        # Create the PID file for this daemon.
        util.pid_create(l3overlay_daemon.pid)

        # Set up process signal handlers.
        l3overlay_daemon.logger.debug("setting up signal handlers")
        signal.signal(signal.SIGTERM, sigterm)
        signal.signal(signal.SIGINT, sigint)
        signal.signal(signal.SIGHUP, sighup)

        # We're done! Time to block and wait for signals.
        while True:
            l3overlay_daemon.logger.debug("waiting for signal")
            signal.pause()

    except Exception as e:
        if l3overlay_daemon.logger.is_started():
            l3overlay_daemon.logger.exception(e)
            sys.exit(1)
        else:
            raise
