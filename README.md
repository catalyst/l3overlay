l3overlay
=========

l3overlay is a tool used to build a MPLS-like VRF network between nodes/firewalls across the Internet. It uses a combination of network namespaces, gretap tunnels (with optional IPsec encapsulation for security) to create an "overlay" over the node's Internet connection.

Prerequisites
-------------

The following software packages are required to run l3overlay:

* **Python**, version **3.4** or later
* **iproute2**
* **BIRD** routing daemon, version **1.4.0** or later
* **strongSwan** IPsec

The following Python modules must also be installed:

* **pyroute2**, version **0.3.15.post37** or later
* **jinja2**

The following configuration settings should be set in `/etc/sysctl.conf`, to enable IPv4 (and IPv6 if desired) packet forwarding:

    net.ipv4.ip_forward=1
    net.ipv6.conf.all.forwarding=1

If you intend to use the static VLAN functionality in the overlay, the following Linux kernel module should be enabled by inserting this line into `/etc/modprobe.conf`, if it is not enabled by default:

    8021q

Installation
------------

l3overlay can be installed to the default location by simply using:

    sudo make install

By default, this will install the `l3overlayd` executable into `/usr/local/sbin`, and it will make a configuration hierarchy in `/usr/local/etc/l3overlay`.

See the `Makefile` for more details on how to change the installation locations.

`l3overlayd` looks for files in the following directories, in the order shown:

1. `(current working directory)`
2. `(current working directory)/etc/l3overlay`
3. `(current working directory)/../etc/l3overlay`
4. `(executable directory)`
5. `(executable directory)/etc/l3overlay`
6. `(executable directory)/../etc/l3overlay`
7. `/etc/l3overlay`

Any configuration files or directories mentioned in this document should be placed in any of the directories mentioned above. For instance, assuming `/etc/l3overlay` is the chosen directory, the global configuration and a test overlay configuration would be placed in the following filepaths:

* `/etc/l3overlay/global.conf`
* `/etc/l3overlay/overlays/example.conf`

Example configuration
----------------------

An example configuration needed to get a working overlay set up may look something like this. More settings are available for the overlays to set up connections to be exposed to the overlay from the nodes, available in the *Global configuration* and *Overlay configuration* sections below.

### global.conf

    [global]
    logging-level=INFO
    use-ipsec=true
    ipsec-psk={psk}

### overlays/example.conf (on node example-1)

    [overlay]
    name=example
    asn=64666
    linknet-pool=198.51.100.0/24
    this-node=example-1
    node-0=example-1 192.0.2.1
    node-1=example-2 192.0.2.2
    node-2=example-3 192.0.2.3
    node-3=example-4 192.0.2.4

Global configuration
--------------------

Global configuration values for l3overlay are to be defined in `global.conf`.

This file is optional, since all of the configuration options defined here are not strictly required.

If an IPsec PSK is stored in the global configuration, the permissions should be set such that the user running `l3overlayd` is the only user with read permission to the global configuration.

### [global]

All `global.conf` configuration values come under the `[global]` section.

#### logging-level
* Type: **enum**
* Required: no
* Values: `NOSET`, `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

Specifies the logging output level that l3overlay should use. The default value is `INFO`.

#### use-ipsec
* Type: **boolean**
* Required: no

Specifies whether or not IPsec should be used to encrypt the overlay mesh tunnels. The default value is `false`.

#### ipsec-psk
* Type: **hex**, 6-64 digits
* Required: **yes**, **IF** `use-ipsec` is `true`

The hex string used as the pre-shared key (PSK) for authentication of the IPsec tunnels encapsulating the overlay. The PSK must be at least 6 digits long, and has a maximum length of 64 digits.

#### ipsec-d
* Type: **boolean**
* Required: no

If `true`, installs the IPsec configuration as `l3overlay.conf` under the `/etc/ipsec.d` directory. If `false`, installs the IPsec configuration directly as `/etc/ipsec.conf`.

The default value is `false`.

Note that if this option is set to `true`, then `l3overlayd` will **NOT** manage `/etc/ipsec.conf`, as it is assumed that the user will want to configure IPsec themselves. A suitable `/etc/ipsec.conf` **MUST** be provided, which will include the l3overlay IPsec configuration file located at `/etc/ipsec.d/l3overlay.conf`.

#### ipsec-secrets-stub
* Type: **boolean**
* Required: no

Determines whether or not to install a stub IPsec secrets file to `/etc/ipsec.secrets`, to make IPsec include the real l3overlay IPsec secrets file located at `/etc/ipsec.l3overlay.secrets`. The default value is `true`.

Overlay configuration
---------------------

Each overlay to be set up gets its own configuration file, to be located in the `overlays` directory.

### [overlay]

Configuration settings for the overlay, and the mesh tunnels which make the communication channels for the overlay.

#### name
* Type: **name**
* Required: **yes**

The name the overlay will be referred to. Also used to name the network namespace.

#### asn
* Type: **integer**
* Required: **yes**

The BGP autonomous system (AS) number the overlay will configure the mesh tunnel routing system with.

#### linknet-pool
* Type: **subnet**
* Required: **yes**

The subnet range which can be divided into `/31` subnets, and then used to address the mesh tunnels in the overlay.

#### this-node
* Type: **name**
* Required: **yes**

The name of the node to configure the overlay for. The name specified here **MUST** be located in the list of nodes, described below.

#### node-*{int}*
* Type: {**name**} {**ipv4 address**}
* Required: **yes**, at least **TWO**

The list of nodes in the mesh, with the Internet-accessible IPv4 address used to build the overlay. A working overlay should have at least two nodes specified here.

The order of the nodes (`node-0`, `node-1`, ...) does not matter significantly, unless new nodes are to be added to the list. New nodes may **ONLY** be appended to the end of the list. This is because if new nodes are added at any other position in the list, it will cause the addresses assigned to mesh tunnel links to change, and l3overlay does not handle this intelligently (it does not ensure the other sides of the tunnel links are changed as well).

#### enabled
* Type: **boolean**
* Required: no

Specifies whether or not this overlay should be configured. The default value is `true`.

#### fwbuilder-script
* Type: **filename** / **filepath**
* Required: no

The location to the fwbuilder script used to build the firewall settings inside the overlay. This can be either an absolute filepath to the script, or simply a filename relative to the `fwbuilder_scripts` directory.

### [static-vlan:*{name}*]

This section is used to statically define a IEEE 802.1Q VLAN interface, assigned to a physical interface, which will be accessible in the overlay via a veth pair.

#### id
* Type: **integer**
* Required: **yes**

The IEEE 802.1Q VLAN ID tag for the static VLAN interface.

#### physical-interface
* Type: **name**
* Required: **yes**

The physical interface assigned to the static VLAN interface.

#### address
* Type: **ipv4 address**
* Required: **yes**

The IPv4 address assigned to the static VLAN interface.

#### netmask
* Type: **subnet mask**, dotted decimal
* Required: **yes**

The subnet mask for the VLAN interface address, in dotted decimal form.

### [static-tunnel:*{name}*]

This section is used to define a layer 2/3 GRE tunnel in the overlay. It can be connected to any IPv4 address available in the overlay.

#### mode
* Type: **enum**
* Required: **yes**
* Values: `gre`, `gretap`

The mode in which the GRE tunnel will operate, layer 2 (`gretap`) or layer 3 (`gre`).

#### local
* Type: **ipv4 address**
* Required: **yes**

The local endpoint IPv4 address assigned to the GRE tunnel.

#### remote
* Type: **ipv4 address**
* Required: **yes**

The remote endpoint IPv4 address assigned to the GRE tunnel.

#### address
* Type: **ipv4 address**
* Required: **yes**

The IPv4 address assigned to the GRE tunnel interface.

#### netmask
* Type: **subnet mask**, dotted decimal
* Required: **yes**

The subnet mask for the GRE tunnel interface address, in dotted decimal form.

### [static-bgp:*{name}*]

This section is used to define a static BGP protocol in the BIRD routing daemon, used for distributing routes in the overlay. This is made to be used in conjunction with static GRE tunnels, to distribute routes across it.

#### local-asn
* Type: **integer**
* Required: **yes**

The BGP autonomous system (AS) number used to identify the AS the local node is part of.

#### neighbor
* Type: **ipv4 address**
* Required: **yes**

The neighbor BGP node's IPv4 address.

#### neighbor-asn
* Type: **integer**
* Required: **yes**

The BGP autonomous system (AS) number used to identify the AS the neighbor node is part of.

#### description
* Type: **string**
* Required: no

An optional description of the BGP protocol, displayed with the use of `show protocol all` in the BIRD client.

#### local
* Type: **ipv4 address**
* Required: no

The local IPv4 address used to make the BGP connection with the neighbor. Optional.

#### import-prefix[-*{int}*]
* Type: **bird prefix**
* Required: no

One or more BIRD filters used to filter the routes which get imported into the BGP protocol. The default is to import all routes.

See the [BIRD filter documentation](http://bird.network.cz/?get_doc&f=bird-5.html) for more information.

### [static-veth:*{name}*]

This section is used to configure a static veth pair, with an outer interface in the root namespace, and an inner interface inside the overlay.

#### inner-address
* Type: **ipv4 address**
* Required: **yes**

The IPv4 address assigned to the inner (overlay) interface.

#### outer-address
* Type: **ipv4 address**
* Required: **yes**

The IPv4 address assigned to the outer (overlay) interface.

#### netmask
* Type: **subnet mask**, dotted decimal
* Required: **yes**

The subnet mask for both the inner and outer addresses, in dotted decimal form.
