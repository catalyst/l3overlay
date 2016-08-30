# -*- mode: ruby -*-
# vi: set ft=ruby :
#
# IPsec overlay network manager (l3overlay)
# Vagrantfile - settings for Vagrant test environment
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

Vagrant.configure("2") do |config|

    config.vm.box = "ubuntu/trusty64"

    config.vm.provision "shell", inline: <<-SHELL
        apt-get update
        apt-get install -y iproute2
        apt-get install -y vlan
        apt-get install -y bird
        apt-get install -y strongswan
        apt-get install -y make
        apt-get install -y git
        apt-get install -y python3-pip
        pip3 install pyroute2
        pip3 install jinja2

        make -C /vagrant test
        make -C /vagrant install PREFIX="/usr" CONFIG_DIR="/etc/l3overlay" WITH_UPSTART=1

        rm -rf /etc/l3overlay/overlays
        cp /vagrant/vagrant/global.conf /etc/l3overlay/global.conf
    SHELL

    config.vm.define "l3overlay-1" do |l3overlay1|
        l3overlay1.vm.network "private_network", ip: "192.168.50.2"

        l3overlay1.vm.provision "shell", inline: <<-SHELL
            cp -R /vagrant/vagrant/l3overlay-1/overlays /etc/l3overlay/overlays
            service l3overlay start
        SHELL
    end

    config.vm.define "l3overlay-2" do |l3overlay2|
        l3overlay2.vm.network "private_network", ip: "192.168.50.3"

        l3overlay2.vm.provision "shell", inline: <<-SHELL
            cp -R /vagrant/vagrant/l3overlay-2/overlays /etc/l3overlay/overlays
            service l3overlay start
        SHELL
    end
end
