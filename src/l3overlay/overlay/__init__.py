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
import os

from l3overlay import util

from l3overlay.util.worker import Worker

from l3overlay.network import netns

from l3overlay.overlay import bgp
from l3overlay.overlay import firewall
from l3overlay.overlay import interface

from l3overlay.overlay.interface.mesh_tunnel import MeshTunnel

from l3overlay.overlay.bgp import process


class Overlay(Worker):
    '''
    Abstract base class for an overlay static interface.
    '''

    def __init__(self, logger, daemon, name, config):
        '''
        Set overlay runtime state.
        '''

        super().__init__()

        # Arguments.
        self.logger = logger
        self.daemon = daemon
        self.name = name

        # Fields.
        self.root_dir = os.path.dir(self.daemon.overlay_dir, self.name)

        # Overlay network namespace.
        self.netns = netns.get(self.name)

        # Data structures.
        self.mesh_tunnels = []
        self.interfaces = []
        self.bgps = []

        # Read overlay configuration.
        for s, section in config.items():
            if s.startswith("overlay"):
                # Determine whether or not to allow this overlay to start.
                self.enabled = util.boolean_get(section["enabled"]) if "enabled" in config else True

                # Generate the list of nodes, sorted numerically.
                nodes_dict = {}

                for key in section.keys():
                    if key.startswith("node-"):
                        node = section[key].split()
                        nodes_dict[int(key[5:])] = tuple(
                            util.name_get(node[0]),
                            util.ip_address_get(node[1]),
                        )

                self.nodes = [nodes_dict[key] for key in sorted(nodes_dict.keys())]

                if len(self.nodes) != len(set(self.nodes)):
                    raise RuntimeError("node list contains duplicates")

                # Get the node dictionary for this node from the list of nodes.
                self.this_node = next(((node for node in self.nodes if node[0] == util.name_get(section["this-node"])), None)

                if not self.this_node:
                    raise RuntimeError("this node '%s' is missing from node list" % util.name_get(section["this-node"]))

                # Used to configure the overlay's BGP AS number. 
                self.asn = util.integer_get(section["asn"])

                # Used for determining the available point-to-point subnets for the mesh tunnels.
                self.linknet_pool = util.ip_network_get(section["linknet-pool"])

                # Get the (absolute or relative) path to the fwbuilder script to
                # configure the firewall in this overlay.
                if "fwbuilder-script" in section:
                    self.fwbuilder_script = section["fwbuilder-script"] if os.path.isabs(section["fwbuilder-script"] else os.path.join(self.daemon.fwbuilder_script_dir, section["fwbuilder-script"])
                else:
                    self.fwbuilder_script = None

                # Create the mesh tunnel interfaces.
                for i, node_link in enumerate(self._node_links()):
                    # Check if this link requires a tunnel on this host. If not,
                    # continue.
                    if link[0] != self.this_node[0]:
                        continue

                    # Mesh tunnel interface name, made from the BGP AS number
                    # of this overlay and the node pair number.
                    name = "m%il%i" % (self.asn, math.floor(index / 2))

                    node_local = link[0]
                    node_remote = link[1]

                    physical_local = self.this_node[1]
                    physical_remote = None
                    for node, address in self.nodes:
                        if node == node_remote:
                            physical_remote = address
                            break

                    virtual_local = linknet_pool_address_base + i
                    virtual_remote = util.ip_address_remote(netns_veth_address_local)

                    if (virtual_local > self.linknet_pool.broadcast_address or
                            virtual_remote > self.linknet_pool.broadcast_address):
                        raise RuntimeError("overflowed linknet pool %s with node link %s" % (str(self.linknet_pool), str(node_link)))

                    self.mesh_tunnels.append(MeshTunnel(
                        daemon,
                        overlay,
                        name,
                        node_local,
                        node_remote,
                        physical_local,
                        physical_remote,
                        virtual_local,
                        virtual_remote,
                    ))

            # Read static BGP protocols.
            elif s.startswith("static-bgp"):
                self.bgps.append(bgp.read(self.daemon, self, section, section))

            # Read static interfaces.
            elif s.startswith("static"):
                self.interfaces.append(interface.read(self.daemon, self, section, section))

            # Handle unexpected sections.
            else:
                raise RuntimeError("unsupported section type '%s'" % section)

        # Create the overlay's BGP and firewall process objects,
        # once the data structures are complete.
        self.bgp_process = bgp.create(self.daemon, self)
        self.firewall_process = firewall.create(self)


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

        if self.starting() or self.running():
            raise RuntimeError("overlay '%s' started twice" % self.name)

        self.set_starting()

        self.logger.info("starting overlay")

        self.netns.start()

        self.logger.debug("creating overlay root directory")
        util.directory_create(self.root_dir)

        for mesh_tunnel in self.mesh_tunnels:
            mesh_tunnel.start()

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

        if not self.running():
            raise RuntimeError("overlay '%s' not yet started" % self.name)

        if self.stopped():
            raise RuntimeError("overlay '%s' stopped twice" % self.name)

        self.set_stopping()

        self.logger.info("stopping overlay")

        self.bgp_process.stop()

        for interface in self.interfaces:
            interface.close()
            interface.remove()

        for mesh_tunnel in self.mesh_tunnel:
            mesh_tunnel.close()
            mesh_tunnel.remove()

        self.netns.stop()
        self.netns.remove()

        self.logger.debug("removing overlay root directory")
        util.directory_remove(self.root_dir)

        self.logger.info("finished stopping overlay")

        self.set_stopped()

Worker.register(Overlay)


def read(daemon, conf):
    '''
    Parse a configuration file, and return an overlay object.
    '''

    config = util.config(conf)

    name = util.name_get(config["overlay"]["name"])
    logger = util.logger(self.log, "l3overlay", name)

    return Overlay(logger, daemon, name, config)
