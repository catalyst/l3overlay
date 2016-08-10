#
# IPsec overlay network manager (l3overlay)
# l3overlay/util/worker.py - worker abstract base class
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


import abc


class Worker(metaclass=abc.ABCMeta):
    '''
    Abstract base class for classes which use a 'start-stop' service
    operation style. Implements the internal fields and helper methods
    for this.
    '''

    def __init__(self):
        '''
        Set up worker internal fields and runtime state.
        '''

        self._starting = False
        self._running = False

        self._stopping = False
        self._stopped = False


    def _error(self):
        '''
        Raise a RuntimeErorr due to invalid workerstate.
        '''

        raise RuntimeError('''invalid worker state (only one state value can be True at a time):
  Starting: %s
  Running: %s
  Stopping: %s
  Stopped: %s''' % (
                str(self._starting),
                str(self._running),
                str(self._stopping),
                str(self._stopped)))


    def starting(self):
        '''
        Check if the worker is in 'starting' state.
        '''

        if self._starting:
            if not self._running and not self._stopping and self._stopped:
                return True
            else:
                self._error()

        return False


    def set_starting(self):
        '''
        Set the worker to 'starting' state.
        '''

        self._starting = True
        self._running = False
        self._stopping = False
        self._stopped = False


    def running(self):
        '''
        Check if the worker is in 'running' state.
        '''

        if self._running:
            if not self._starting and not self._stopping and self._stopped:
                return True
            else:
                self._error()

        return False


    def set_running(self):
        '''
        Set the worker to 'running' state.
        '''

        self._starting = False
        self._running = True
        self._stopping = False
        self._stopped = False


    def started(self):
        '''
        Alias to running().
        '''

        return self.running()


    def set_started(self):
        '''
        Alias to set_running().
        '''

        self.set_running()


    def stopping(self):
        '''
        Check if the worker is in 'stopping' state.
        '''

        if self._stopping:
            if not self._starting and not self._running and self._stopped:
                return True
            else:
                self._error()

        return False


    def set_stopping(self):
        '''
        Set the worker to 'stopping' state.
        '''

        self._starting = False
        self._running = False
        self._stopping = True
        self._stopped = False


    def stopped(self):
        '''
        Check if the worker is in 'stopped' state.
        '''

        if self._stopped:
            if not self._starting and not self._running and self._stopping:
                return True
            else:
                self._error()

        return False


    def set_stopped(self):
        '''
        Set the worker to 'stopped' state.
        '''

        self._starting = False
        self._running = False
        self._stopping = False
        self._stopped = True


    @abc.abstractmethod
    def start(self):
        '''
        Start the worker.
        '''

        return


    @abc.sbstractmethod
    def stop(self):
        '''
        Stop the worker.
        '''

        return


    def remove(self):
        '''
        Remove the worker runtime state. Optional method.
        '''

        return

