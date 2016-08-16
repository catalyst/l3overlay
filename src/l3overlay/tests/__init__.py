#
# IPsec overlay network manager (l3overlay)
# l3overlay/tests/__init__.py - test base class and functions
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


import concurrencytest
import os
import unittest

from l3overlay import util

from l3overlay.daemon import Daemon

import mininet.net

import mininet.node

import mininet.nodelib

import mininet.topo


class L3overlayTopo(mininet.topo.Topo):
    '''
    l3overlay topology object for mininet.
    '''

    def build(self, n_routers, n_end_devices):
        '''
        Build the l3overlay topology object.

        * 1 switch
        * (n_routers) routers in an l3overlay mesh
        * (n_routers * n_end_devices) end devices, (n_end_devices) per router
        '''

        pid = os.getpid()

        switch = self.addSwitch("p%xs" % pid, cls=mininet.nodelib.LinuxBridge)
        routers = []
        end_devices = {}

        for i in range(n_routers):
            router = self.addHost("p%xr%i" % (pid, i))
            self.addLink(router, switch)
            routers.append(router)

        for i, router in enumerate(routers):
            end_devices[router.name] = []
            for j in range(n_end_devices):
                end_device = self.addHost("p%xr%ie%i" % (pid, i, j))
                self.addLink(end_device, router)
                end_devices[router.name].append(end_device)


class L3overlayTest(unittest.TestCase):
    '''
    '''

    def daemon(self, os, use_ipsec=True):
        '''
        '''

        d = # daemon number

        daemon_dir =

        log = os.path.join(daemon_dir, "l3overlay.log")
        logger = util.logger(log, "l3overlay-%i" % d)

        lib_dir = os.path.join(daemon_dir, "lib")

        fwbuilder_script_dir = os.path.join(daemon_dir, "fwbuilder-scripts")
        overlay_dir = os.path.join(daemon_dir, "overlays")
        template_dir = os.path.join(daemon_dir, "templates")

        pid_dir = os.path.join(daemon_dir, "run")
        pid = os.path.join(pid_dir, "l3overlayd.pid")

        ipsec_conf =
        ipsec_secrets =

        overlays = {o.name:o for o in os}

        return Daemon(
            logger,   # logger
            log,      # log
            "DEBUG",  # log_level

            use_ipsec, # use_ipsec
            True,      # ipsec_manage

            lib_dir,                           # lib_dir
            os.path.join(lib_dir, "overlays"), # overlay_dir

            fwbuilder_script_dir, # fwbuilder_script_dir
            overlay_conf_dir,     # overlay_conf_dir
            template_dir,         # template_dir

            pid,            # pid
            ipsec_conf,     # ipsec_conf
            ipsec_secrets,  # ipsec_secrets

            overlays, # overlays
        )
            

    def setUp(self):
        '''
        '''

        pass


    def tearDown(self):
        '''
        '''

        pass
