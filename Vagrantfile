# -*- mode: ruby -*-
# vi: set ft=ruby :
#
# IPsec overlay network manager (l3overlay)
# Vagrantfile - settings for Vagrant test environment
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

Vagrant.configure("2") do |config|

    config.vm.box = "ubuntu/xenial64"

    config.vm.provision "file", source: "vagrant/setup-l3overlay", destination: "/tmp"

    config.vm.provision "shell", inline: <<-SHELL
        apt-get update
        apt-get install -y dos2unix

        echo 'net.ipv4.ip_forward=1' > /etc/sysctl.conf
        echo 'net.ipv6.conf.all.forwarding=1' >> /etc/sysctl.conf

        sysctl -p /etc/sysctl.conf

        echo '#!/bin/sh' > /usr/local/bin/setup-l3overlay
        echo 'test ! -d /vagrant || cp /vagrant/vagrant/setup-l3overlay /tmp/setup-l3overlay || exit $?' >> /usr/local/bin/setup-l3overlay
        echo 'dos2unix /tmp/setup-l3overlay || exit $?' >> /usr/local/bin/setup-l3overlay
        echo 'chmod +x /tmp/setup-l3overlay || exit $?' >> /usr/local/bin/setup-l3overlay
        echo '/tmp/setup-l3overlay $@ || exit $?' >> /usr/local/bin/setup-l3overlay
        chmod +x /usr/local/bin/setup-l3overlay
    SHELL

    config.vm.define "l3overlay-1" do |l3overlay_1|
        l3overlay_1.vm.network "private_network", ip: "192.168.50.2"
        l3overlay_1.vm.network "private_network", ip: "192.168.50.4"
        l3overlay_1.vm.provision "shell", inline: "setup-l3overlay l3overlay-1"
    end

    config.vm.define "l3overlay-2" do |l3overlay_2|
        l3overlay_2.vm.network "private_network", ip: "192.168.50.3"
        l3overlay_2.vm.network "private_network", ip: "192.168.50.5"
        l3overlay_2.vm.provision "shell", inline: "setup-l3overlay l3overlay-2"
    end
end
