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
import copy
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

from l3overlay.util.exception import L3overlayError

from l3overlay.util.worker import Worker


class LinknetPoolOverflowError(L3overlayError):
    def __init__(self, overlay, node_link):
        super().__init__(
            "overflowed linknet pool '%s' with node link %s in %s '%s'" %
                    (str(overlay.linknet_pool), str(node_link), overlay.description, overlay.name))

class NoOverlayConfigError(L3overlayError):
    def __init__(self):
        super().__init__("no overlay configuration specified")

class NoNodeListError(L3overlayError):
    def __init__(self, name):
        super().__init__(
            "node list missing from overlay '%s'" % name)

class MissingThisNodeError(L3overlayError):
    def __init__(self, name, this_node):
        super().__init__(
            "this node '%s' is missing from node list of overlay '%s'" % (this_node, name))

class UnsupportedSectionTypeError(L3overlayError):
    def __init__(self, name, section):
        super().__init__(
            "supported section type '%s' in overlay '%s'" % (section, name))


class Overlay(Worker):
    '''
    Overlay management class.
    '''

    def __init__(self, logger, name,
                enabled, asn, linknet_pool, fwbuilder_script_file, nodes, this_node,
                interfaces):
        '''
        Set up the overlay internal fields.
        '''

        super().__init__(use_setup=True)

        self.logger = logger
        self.name = name
        self.description = "overlay '%s'" % self.name

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

        if not self.enabled:
            return

        self.set_settingup()

        # Set arguments.
        self.daemon = daemon

        # Configure fields which use the daemon object.
        self.dry_run = self.daemon.dry_run

        if self.fwbuilder_script_file:
            if os.path.isabs(self.fwbuilder_script_file):
                self.fwbuilder_script = self.fwbuilder_script_file
            else:
                self.fwbuilder_script = os.path.join(
                    self.daemon.fwbuilder_script_dir,
                    self.fwbuilder_script_file,
                )
        else:
            self.fwbuilder_script = None

        self.root_dir = os.path.join(self.daemon.overlay_dir, self.name)

        # Overlay network namespace.
        self.netns = netns.get(self.dry_run, self.logger, self.name)

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
                raise LinknetPoolOverflowError(self, node_link)

            self.mesh_tunnels.append(mesh_tunnel.create(
                self.logger,
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

        if not self.enabled:
            return

        self.set_starting()

        self.logger.info("starting overlay")

        # Start the network namespace object, so the overlay's
        # network namespace can be manipulated.
        self.netns.start()

        self.logger.debug("creating overlay root directory")
        if not self.dry_run:
            util.directory_create(self.root_dir)

        for mt in self.mesh_tunnels:
            mt.start()

        for interface in self.interfaces:
            interface.start()

        self.bgp_process.start()

        self.firewall_process.start()

        # Shut down the overlay's network namespace object, to
        # reduce memory consumption by the network namespace's
        # pyroute2 process.
        self.netns.stop()

        self.logger.info("finished starting overlay")

        self.set_started()


    def stop(self):
        '''
        Stop the overlay.
        '''

        if not self.enabled:
            return

        self.set_stopping()

        self.logger.info("stopping overlay")

        # Restart the overlay's network namespace object, after
        # shutting it down to conserve memory.
        self.netns.start()

        self.bgp_process.stop()

        for interface in self.interfaces:
            interface.stop()
            interface.remove()

        for mt in self.mesh_tunnels:
            mt.stop()
            mt.remove()

        # We're done with the overlay network namespace. Stop it,
        # and remove the namespace.
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

        if not self.enabled:
            return

        self.set_removing()

        self.logger.stop()

        self.set_removed()

Worker.register(Overlay)


def read(log, log_level, conf=None, config=None):
    '''
    Parse a configuration, file or dictionary, and return an overlay object.
    '''

    # If specified, read the overlay configuration file.
    if conf:
        config = util.config(conf)
    elif config:
        config = copy.deepcopy(config)
    else:
        raise NoOverlayConfigError()

    # Get the overlay configuration.
    section = config["overlay"]

    # Fetch just enough configuration to start an overlay logger.
    name = util.name_get(section["name"])

    lg = logger.create(log, log_level, "l3overlay", name)
    lg.start()

    # Global overlay configuration.
    enabled = util.boolean_get(section["enabled"]) if "enabled" in section else True
    asn = util.integer_get(section["asn"], minval=0, maxval=65535)
    linknet_pool = util.ip_network_get(section["linknet-pool"])

    fwbuilder_script_file = section["fwbuilder-script"] if "fwbuilder-script" in section else None

    # Generate the list of nodes, sorted numerically.
    nodes = []
    for key, value in section.items():
        if key.startswith("node-"):
            node = util.list_get(value, length=2, pattern="\\s")
            nodes.append((util.name_get(node[0]), util.ip_address_get(node[1])))

    if not nodes:
        raise NoNodeListError(name)

    # Get the node object for this node from the list of nodes.
    this_node = next((n for n in nodes if n[0] == util.name_get(section["this-node"])), None)

    if not this_node:
        raise MissingThisNodeError(name, util.name_get(section["this-node"]))

    # Static interfaces.
    interfaces = []

    for s, c in config.items():
        if s.startswith("static"):
            interfaces.append(interface.read(lg, s, c))
        elif s == "DEFAULT" or s == "overlay":
            continue
        else:
            raise UnsupportedSectionTypeError(name, s)

    # Return overlay object.
    return Overlay(lg, name,
        enabled, asn, linknet_pool, fwbuilder_script_file, nodes, this_node, interfaces)


def write(overlay, config):
    '''
    Write an overlay to the given configuration object.
    '''

    config["overlay"] = {}
    section = config["overlay"]

    section["enabled"] = str(overlay.enabled).lower()
    section["asn"] = str(overlay.asn)
    section["linknet-pool"] = str(overlay.linknet_pool)
    section["fwbuilder-script"] = overlay.fwbuilder_script_file

    section["this-node"] = "%s %s" % (overlay.this_node[0], str(overlay.this_node[1]))
    for i, n in enumerate(overlay.nodes):
        section["node-%i" % i] = "%s %s" % (n[0], str(n[1]))

    for i in overlay.interfaces:
        interface.write(i, config)
