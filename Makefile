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


#
# Makefile arguments
# ------------------
#
# Any of the parameters in this Makefile can be overridden on the command line.
# Some variables are designed to be used like this, to provide optional
# parameters.
#
# Use them like so:
#   $ make install <ARGUMENT>=<VALUE>
#
# Optional arguments:
#
# * NO_PREFIX - define this to disable prepending the PREFIX to the
#               configuration installation directory
#
# * INSTALL_PREFIX - configure l3overlayd to use a non-system Python
#                    installation such as a virtualenv, specified by the root
#                    directory of the installation
#
# * WITH_INIT_D - define this to build and install a /etc/init.d script for
#                 l3overlay
#
# * WITH_UPSTART - define this to build and install a Upstart configuration for
#                  l3overlay
#

##############################


#
## Name of the project.
#

NAME    = l3overlay
PKGNAME = l3overlay


##############################


#
## Build system installation locations.
#

ifndef NO_PREFIX
PREFIX = /usr/local
endif

SBIN_DIR = $(PREFIX)/sbin
CONFIG_DIR = $(PREFIX)/etc/l3overlay


##############################


#
## staff-vpn default configuration values.
#


##############################


#
##  Build system runtime files and commands.
#

CONFIG   = .config
SETUP_PY = setup.py

SRC_DIR   = src
MODULE_DIR = $(SRC_DIR)/$(PKGNAME)

TESTS_BIN_DIR = tests/tests
TESTS_SRC_DIR = tests

PYLINT = pylint

# Detect usable Python command, if not defined by the user.
ifndef PYTHON
PYTHON_MAJOR_VER = $(shell python3 -V | sed 's:^Python \([0-9][0-9]*\)\..*$$:\1:')
PYTHON_MINOR_VER = $(shell python3 -V | sed 's:^Python [0-9][0-9]*\.\([0-9][0-9]*\)\..*$$:\1:')
ifeq ($(shell test $(PYTHON_MAJOR_VER) -eq 3 -a $(PYTHON_MINOR_VER) -ge 4 && echo true), true)
PYTHON = $(shell which python3)
endif
endif

ifndef PYTHON
PYTHON = $(shell which python3.5)
endif

ifndef PYTHON
PYTHON = $(shell which python3.4)
endif

ifndef PYTHON
$(error $(NAME) only supports Python >= 3.4.0)
endif

# An alternative to this if the default doesn't work:
# PIP = $(PYTHON) -m pip
PIP = pip3

FIND = find

RM    = rm -f
RMDIR = rm -rf


##############################


#
## Build system parameters.
#

ifdef INSTALL_PREFIX
override INSTALL_PREFIX := --prefix=$(INSTALL_PREFIX)
endif

ifdef INSTALL_LIB
override INSTALL_LIB := --install-lib=$(INSTALL_LIB)
endif


##############################


all:
	@echo "Targets:"
	@echo "  lint - run pylint code quality check"
	@echo "  test - run unit tests"
	@echo "  sdist - build Python source distribution"
	@echo "  bdist_wheel - build Python binary wheel distribution"
	@echo "  install - build and install to local system"
	@echo "  uninstall - uninstall from local system"
	@echo "  clean - clean build files"
	@echo "See 'Makefile' for more details."


config:
	@echo -n > $(CONFIG)
	@echo PREFIX=$(PREFIX) >> $(CONFIG)
	@echo SBIN_DIR=$(SBIN_DIR) >> $(CONFIG)
	@echo CONFIG_DIR=$(CONFIG_DIR) >> $(CONFIG)
	@echo WITH_INIT_D=$(WITH_INIT_D) >> $(CONFIG)
	@echo WITH_UPSTART=$(WITH_UPSTART) >> $(CONFIG)


lint:
	$(PYLINT) $(MODULE_DIR)


test:
	@for t in $(shell $(FIND) $(TESTS_BIN_DIR) -maxdepth 1 -name 'test_*.py'); do \
		PYTHONPATH=$(TESTS_SRC_DIR):$(SRC_DIR) $(PYTHON) $$t || exit $$?; \
	done


sdist: config
	$(PYTHON) $(SETUP_PY) sdist


bdist_wheel: config
	$(PYTHON) $(SETUP_PY) bdist_wheel


install: config
	$(PYTHON) $(SETUP_PY) install --install-scripts=$(SBIN_DIR) $(INSTALL_PREFIX)


uninstall:
	$(PIP) uninstall -y l3overlay


clean:
	$(RM) $(CONFIG)
	$(RM) default/l3overlay
	$(RM) init.d/l3overlay
	$(RM) upstart/l3overlay.conf
	$(RMDIR) .tests
	$(RMDIR) build
	$(RMDIR) dist
	$(RMDIR) src/$(NAME).egg-info
	for d in $(shell $(FIND) -name '__pycache__'); do \
		$(RMDIR) $$d; \
	done


.PHONY: all config test sdist bdist_wheel install uninstall clean
