#!/usr/bin/make -f
# -*- makefile -*-
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

##############################

PREFIX     = /usr/local
SBIN_DIR   = $(PREFIX)/sbin
CONFIG_DIR = $(PREFIX)/etc/l3overlay

##############################

TEMPLATES = bird.conf ipsec.conf ipsec.secrets

##############################

INSTALL = install
MKDIR   = mkdir -p

LS      = ls

RM      = rm -f
RMDIR   = rm -rf

TEST    = test

##############################

all:
	@echo "To install l3overlayd, run 'make install'."

install:
	$(MKDIR) $(SBIN_DIR)
	$(MKDIR) $(CONFIG_DIR)
	$(MKDIR) $(CONFIG_DIR)/fwbuilder_scripts
	$(MKDIR) $(CONFIG_DIR)/overlays
	$(MKDIR) $(CONFIG_DIR)/templates
	
	$(INSTALL) -m 755 l3overlayd $(SBIN_DIR)/l3overlayd
	$(INSTALL) -m 600 global.conf $(CONFIG_DIR)/global.conf
	
	for template in $(TEMPLATES); \
	do \
		$(INSTALL) -m 644 templates/$$template $(CONFIG_DIR)/templates/$$template; \
	done

uninstall:
	$(RM) $(SBIN_DIR)/l3overlayd
	$(RM) $(CONFIG_DIR)/global.conf
	
	for template in $(TEMPLATES); \
	do \
		$(RM) $(CONFIG_DIR)/templates/$$template; \
	done
	
	$(TEST) -z "`$(LS) -A $(CONFIG_DIR)/fwbuilder_scripts`" && $(RMDIR) $(CONFIG_DIR)/fwbuilder_scripts
	$(TEST) -z "`$(LS) -A $(CONFIG_DIR)/overlays`" && $(RMDIR) $(CONFIG_DIR)/overlays
	$(TEST) -z "`$(LS) -A $(CONFIG_DIR)/templates`" && $(RMDIR) $(CONFIG_DIR)/templates
	$(TEST) -z "`$(LS) -A $(CONFIG_DIR)`" && $(RMDIR) $(CONFIG_DIR)

.PHONY: all install uninstall
