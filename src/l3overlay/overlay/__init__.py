#
# IPsec overlay network manager (l3overlay)
# l3overlay/overlay/__init__.py - overlay class and functions
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


import configparser
import math
import os

from l3overlay import util

from l3overlay.network import netns

from l3overlay.overlay import interface

from l3overlay.overlay.interface import bgp
from l3overlay.overlay.interface import mesh_tunnel

from l3overlay.overlay.process import bgp as bgp_process
from l3overlay.overlay.process import firewall as firewall_process

from l3overlay.util import logger

from l3overlay.util.worker import Worker


class Overlay(Worker):
    '''
    Overlay management class.
    '''

    def __init__(self, logger, name,
                enabled, asn, linknet_pool, fwbuilder_script_file, nodes, this_node,
                interfaces):
        '''
        Set overlay runtime state.
        '''

        super().__init__()

        self.logger = logger
        self.name = name

        self.enabled = enabled
        self.asn = asn
        self.linknet_pool = linknet_pool
        self.fwbuilder_script_file = fwbuilder_script_file
        self.nodes = nodes
        self.this_node = this_node

        self.interfaces = tuple(interfaces)


    def setup(self, daemon):
        '''
        Set up the overlay runtime state.
        '''

        if self.is_setup():
            raise RuntimeError("overlay '%s' setup twice" % self.name)

        # Set arguments.
        self.daemon = daemon

        # Configure fields which use the daemon object.
        self.fwbuilder_script = self.fwbuilder_script if os.path.isabs(self.fwbuilder_script_file) else os.path.join(self.daemon.fwbuilder_script_dir, self.fwbuilder_script_file)

        self.root_dir = os.path.join(self.daemon.overlay_dir, self.name)

        # Overlay network namespace.
        self.netns = netns.get(self.logger, self.name)

        # Create the mesh tunnel interfaces.
        self.mesh_tunnels = []

        for i, node_link in enumerate(self._node_links()):
            # Check if this link requires a tunnel on this host. If not,
            # continue.
            if node_link[0] != self.this_node[0]:
                continue

            # Mesh tunnel interface name, made from the BGP AS number
            # of this overlay and the node pair number.
            name = "m%il%i" % (self.asn, math.floor(i / 2))

            node_local = node_link[0]
            node_remote = node_link[1]

            physical_local = self.this_node[1]
            physical_remote = None
            for node, address in self.nodes:
                if node == node_remote:
                    physical_remote = address
                    break

            virtual_local = self.linknet_pool.network_address + i
            virtual_remote = util.ip_address_remote(virtual_local)

            if (virtual_local > self.linknet_pool.broadcast_address or
                    virtual_remote > self.linknet_pool.broadcast_address):
                raise RuntimeError("overflowed linknet pool %s with node link %s" % (str(self.linknet_pool), str(node_link)))

            self.mesh_tunnels.append(mesh_tunnel.create(
                logger,
                name,
                node_local,
                node_remote,
                physical_local,
                physical_remote,
                virtual_local,
                virtual_remote,
            ))

        # Set up each interface with this overlay as the context.
        for mt in self.mesh_tunnels:
            mt.setup(self.daemon, self)

        for i in self.interfaces:
            i.setup(self.daemon, self)

        # Create the overlay's BGP and firewall process objects,
        # once the data structures are complete.
        self.bgp_process = bgp_process.create(self.daemon, self)
        self.firewall_process = firewall_process.create(self)

        self.set_setup()


    def _node_links(self):
        '''
        Bi-directionally enumerate all of the node links in a mesh, with
        each node link's reverse immediately following it.
        '''

        # The added nodes list stores the list of nodes with their links
        # already made in the list. Iterations of the list of nodes will 
        # make links to every node on on this added nodes list before
        # adding themselves to it for the next iteration.
        #
        # Creating links this way allows new nodes to be added without
        # affecting what the links() method previously generated. In other
        # words, when new hosts get added, their links get *appended* to the
        # end of the links list.

        links = []
        added_nodes = []

        for peer_node in self.nodes:
            peer_node_name = peer_node[0]
            peer_node_address = peer_node[1]

            for node_name, node_address in added_nodes:
                link = (node_name, peer_node_name)
                if node_name is not peer_node_name and link not in links and link[::-1] not in links:
                    links.append(link)
                    links.append(link[::-1])

            added_nodes.append(peer_node)

        return links


    def start(self):
        '''
        Start the overlay.
        '''

        if self.is_starting() or self.is_started():
            raise RuntimeError("overlay '%s' started twice" % self.name)

        self.set_starting()

        self.logger.info("starting overlay")

        self.netns.start()

        self.logger.debug("creating overlay root directory")
        util.directory_create(self.root_dir)

        for mt in self.mesh_tunnels:
            mt.start()

        for interface in self.interfaces:
            interface.start()

        self.bgp_process.start()

        self.firewall_process.start()

        self.logger.info("finished starting overlay")

        self.set_started()


    def stop(self):
        '''
        Stop the overlay.
        '''

        if not self.is_started():
            raise RuntimeError("overlay '%s' not yet started" % self.name)

        if self.is_stopped() or self.is_stopped():
            raise RuntimeError("overlay '%s' stopped twice" % self.name)

        self.set_stopping()

        self.logger.info("stopping overlay")

        self.bgp_process.stop()

        for interface in self.interfaces:
            interface.stop()
            interface.remove()

        for mt in self.mesh_tunnels:
            mt.stop()
            mt.remove()

        self.netns.stop()
        self.netns.remove()

        self.logger.debug("removing overlay root directory")
        util.directory_remove(self.root_dir)

        self.logger.info("finished stopping overlay")

        self.set_stopped()


    def remove(self):
        '''
        Remove the overlay runtime state.
        '''

        self.logger.stop()

Worker.register(Overlay)


def read(log, log_level, conf):
    '''
    Parse a configuration file, and return an overlay object.
    '''

    lg = logger.create(log, log_level, "l3overlay", self.name)
    lg.start()

    try:
        config = util.config(conf)
        section = config["overlay"]

        # Global overlay configuration.
        name = util.name_get(section["name"])

        enabled = util.boolean_get(section["enabled"]) if "enabled" in section else True
        asn = util.integer_get(section["asn"])
        linknet_pool = util.ip_network_get(section["linknet-pool"])

        fwbuilder_script_file = section["fwbuilder-script"] if "fwbuilder-script" in section else None

        # Generate the list of nodes, sorted numerically.
        ns = {util.integer_get(k):v.split(" ") for k, v in section.items() if k.startswith("node-")}
        nodes = [(util.name_get(ns[k][0]), util.ip_address_get(ns[k][1])) for k in sorted(ns.keys())]

        if len(nodes) != len(set(nodes)):
            raise RuntimeError("node list contains duplicates")

        # Get the node object for this node from the list of nodes.
        this_node = next((n for n in nodes if n[0] == util.name_get(section["this-node"])), None)

        if not this_node:
            raise RuntimeError("this node '%s' is missing from node list" %
                    util.name_get(section["this-node"]))

        # Static interfaces.
        interfaces = [interface.read(lg, h, s) for h, s in config.items() if h.startswith("static")]

        # Return overlay object.
        return Overlay(lg, name,
            enabled, asn, linknet_pool, fwbuilder_script_file, nodes, this_node, interfaces)

    except Exception as e:
        lg.exception(e)
        sys.exit(1)
