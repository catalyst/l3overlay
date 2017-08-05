#
# IPsec overlay network manager (l3overlay)
# tests/__init__.py - l3overlay unit test suite constants, pythonpath setup and main routine
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


'''
l3overlay unit test suite constants, PYTHONPATH setup and main routine.
'''


import os
import sys
import unittest


# Constants used here and elsewhere in the test suite.
_FILE_DIR = os.path.abspath(os.path.dirname(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(_FILE_DIR, "..", ".."))
SRC_DIR = os.path.join(PROJECT_DIR, "src")
TEST_DIR = os.path.join(PROJECT_DIR, "tests")
TMP_DIR = os.path.join(PROJECT_DIR, ".tests")


# Add the l3overlay source tree to the PYTHONPATH. Without
# this, the l3overlay module cannot be imported, or will be
# imported from the system library store.
sys.path.insert(0, SRC_DIR)


# Launch the test suite main routine.
if __name__ == "__main__":
    unittest.TextTestRunner().run(unittest.defaultTestLoader.discover(TEST_DIR))
