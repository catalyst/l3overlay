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
override INSTALL_PREFIX = --prefix=$(INSTALL_PREFIX)
endif

##############################

SETUP_PY = setup.py

##############################

# At this point, l3overlayd only supports Python >= 3.4.
PYTHON  = python3

RM      = rm -f
RMDIR   = rm -rf

##############################

all: bdist_wheel
	@echo "To install l3overlay, run 'make install'."

sdist:
	$(PYTHON) $(SETUP_PY) sdist

bdist_wheel:
	$(PYTHON) $(SETUP_PY) bdist_wheel

install:
	@echo $(DATA_ROOT) > .data_root
	$(PYTHON) $(SETUP_PY) install --install-scripts=$(SBIN_DIR) $(INSTALL_PREFIX)

clean:
	$(RM) .data_root
	$(RMDIR) build
	$(RMDIR) dist
	$(RMDIR) l3overlay.egg-info

.PHONY: all sdist bdist_wheel install clean
