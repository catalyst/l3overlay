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

# Install locations for the executable and data files.
PREFIX     = /usr/local
SBIN_DIR   = $(PREFIX)/sbin

# Prefix the data file locations (/etc/l3overlay/...) with this filepath,
# if enabled.
ifndef NO_DATA_ROOT
DATA_ROOT = $(PREFIX)
endif

# Used to install l3overlayd to a non-standard Python installation
# (for example, a virtualenv).
ifdef INSTALL_PREFIX
override INSTALL_PREFIX := --prefix=$(INSTALL_PREFIX)
endif

##############################

# At this point, l3overlayd only supports Python >= 3.4.
PYTHON  = python3

RM      = rm -f
RMDIR   = rm -rf

##############################

SETUP_PY = setup.py

##############################

# Enable this to build and install the Upstart configuration.
# Can be defined in the command line.
# WITH_UPSTART = 1

##############################

all:
	@echo "Targets:"
	@echo "  sdist - build Python source distribution"
	@echo "  bdist_wheel - build Python binary wheel distribution"
	@echo "  install - build and install to local system"
	@echo "  uninstall - uninstall from local system"
	@echo "  clean - clean build files"
	@echo "See 'Makefile' for more details."

sdist:
	$(PYTHON) $(SETUP_PY) sdist

bdist_wheel:
	$(PYTHON) $(SETUP_PY) bdist_wheel

install:
	@echo $(SBIN_DIR) > .sbin_dir
	@echo $(DATA_ROOT) > .data_root
	@echo $(WITH_UPSTART) > .with_upstart
	$(PYTHON) $(SETUP_PY) install --install-scripts=$(SBIN_DIR) $(INSTALL_PREFIX)

uninstall:
	$(PYTHON) -m pip uninstall -y l3overlay

clean:
	$(RM) .sbin_dir
	$(RM) .data_root
	$(RM) .with_upstart
	$(RM) upstart/l3overlay.conf
	$(RMDIR) build
	$(RMDIR) dist
	$(RMDIR) l3overlay.egg-info

.PHONY: all sdist bdist_wheel install uninstall clean
