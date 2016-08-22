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

from l3overlay.util.exception.l3overlayerror import L3overlayError


STATES = ("settingup", "setup", "starting", "started", "stopping", "stopped", "removing", "removed")


class InvalidSetupStateError(L3overlayError):
    pass

class InvalidWorkerStateError(L3overlayError):
    pass


class SetupTwiceError(L3overlayError):
    pass

class NotYetSettingupError(L3overlayError):
    pass

class NotYetSetupError(L3overlayError):
    pass


class StartedTwiceError(L3overlayError):
    pass

class NotYetStartingError(L3overlayError):
    pass

class NotYetStartedError(L3overlayError):
    pass


class StoppedTwiceError(L3overlayError):
    pass

class NotYetStoppingError(L3overlayError):
    pass

class NotYetStoppedError(L3overlayError):
    pass


class RemovedTwiceError(L3overlayError):
    pass

class NotYetRemovingError(L3overlayError):
    pass

class NotYetRemovedError(L3overlayError):
    pass


class Worker(metaclass=abc.ABCMeta):
    '''
    Abstract base class for classes which use a 'start-stop' service
    operation style. Implements the internal fields and helper methods
    for this.
    '''

    description = "worker"


    def __init__(self, use_setup = False, use_remove = False):
        '''
        Set up worker internal fields.
        '''

        self.use_setup = use_setup
        self.use_remove = use_remove

        self._states = dict.fromkeys(
            STATES,
            False,
        )


    def _assert_state(self):
        '''
        Check that the worker state is valid.
        '''

        for state, value in self._states.items():
            if state not in STATES:
                raise InvalidWorkerStateError(
                    "invalid worker state type '%s' for %s, expected one of %s" %
                            (state, self.description, STATES))
            if not isinstance(value, bool):
                raise InvalidWorkerStateError(
                    "invalid worker state value '%s' in state type '%s' for %s, expected boolean" %
                            (value, state, self.description))


    def is_settingup(self):
        '''
        Check if the worker is currently setting up.
        '''

        self._assert_state()
        return self._states["settingup"]


    def set_settingup(self):
        '''
        Set the worker as setting up.
        '''

        self._assert_state()

        if self.is_settingup() or self.is_setup():
            raise SetupTwiceError("%s setup twice" % self.description)

        self._states["settingup"] = True


    def is_setup(self):
        '''
        Check if the worker has been set up.
        '''

        self._assert_state()
        return self._states["setup"]


    def set_setup(self):
        '''
        Set the worker as set up.
        '''

        self._assert_state()

        if self.is_setup():
            raise SetupTwiceError("%s setup twice" % self.description)

        if not self.is_settingup():
            raise NotYetSettingupError("%s not yet set to setting up" % self.description)

        self._states["settingup"] = False
        self._states["setup"] = True


    def is_starting(self):
        '''
        Check if the worker is in the 'starting' state.
        '''

        self._assert_state()
        return self._states["starting"]


    def set_starting(self):
        '''
        Set the worker to 'starting' state.
        '''

        self._assert_state()

        if self.is_starting() or self.is_started():
            raise StartedTwiceError("%s started twice" % self.description)

        if self.use_setup and not self.is_setup():
            raise NotYetSetupError("%s not yet set up" % self.description)

        self._states["starting"] = True


    def is_started(self):
        '''
        Check if the worker is in the 'started' state.
        '''

        self._assert_state()
        return self._states["started"]


    def set_started(self):
        '''
        Set the worker to 'started' state.
        '''

        self._assert_state()

        if self.is_started():
            raise StartedTwiceError("%s started twice" % self.description)

        if self.use_setup and not self.is_setup():
            raise NotYetSetupError("%s not yet set up" % self.description)

        if not self.is_starting():
            raise NotYetStartingError("%s not yet set to starting" % self.description)

        self._states["starting"] = False
        self._states["started"] = True


    def is_running(self):
        '''
        Check if the worker is in the 'started' state. Alias to is_started().
        '''

        return self.is_started()


    def set_running(self):
        '''
        Set the worker to 'started' state. Alias to set_started().
        '''

        self.set_started()


    def is_stopping(self):
        '''
        Check if the worker is in the 'stopping' state.
        '''

        self._assert_state()
        return self._states["stopping"]


    def set_stopping(self):
        '''
        Set the worker to 'stopping' state.
        '''

        self._assert_state()

        if self.is_stopping() or self.is_stopped():
            raise StoppedTwiceError("%s stopped twice" % self.description)

        if not self.is_started():
            raise NotYetStartedError("%s not yet started" % self.description)

        self._states["stopping"] = True


    def is_stopped(self):
        '''
        Check if the worker is in the 'stopped' state.
        '''

        self._assert_state()
        return self._states["stopped"]


    def set_stopped(self):
        '''
        Set the worker to 'stopped' state.
        '''

        self._assert_state()

        if self.is_stopped():
            raise StoppedTwiceError("%s stopped twice" % self.description)

        if not self.is_started():
            raise NotYetStartedError("%s not yet started" % self.description)

        if not self.is_stopping():
            raise NotYetStoppingError("%s not yet set to stopping" % self.description)

        self._states["stopping"] = False
        self._states["stopped"] = True

        self._states["started"] = False


    def is_removing(self):
        '''
        Check if the worker is in the 'removing' state.
        '''

        self._assert_state()
        return self._states["removing"]


    def set_removing(self):
        '''
        Set the worker to 'removing' state.
        '''

        self._assert_state()

        if self.is_removing() or self.is_removed():
            raise RemovedTwiceError("%s removed twice" % self.description)

        if self.is_started():
            raise NotYetStoppedError("%s not yet stopped" % self.description)

        self._states["removing"] = True


    def is_removed(self):
        '''
        Check if the worker is in the 'removed' state.
        '''

        self._assert_state()
        return self._states["removed"]


    def set_removed(self):
        '''
        Set the worker to 'removed' state.
        '''

        self._assert_state()

        if self.is_removed():
            raise RemovedTwiceError("%s removed twice" % self.description)

        if self.is_started():
            raise NotYetStoppedError("%s not yet stopped" % self.description)

        if not self.is_removing():
            raise NotYetRemovingError("%s not yet set to removing" % self.description)

        self._states["removing"] = False
        self._states["removed"] = True

        self._states["setup"] = False


    def setup(self):
        '''
        Set up worker runtime state.
        '''

        pass


    @abc.abstractmethod
    def start(self):
        '''
        Start the worker.
        '''

        pass


    @abc.abstractmethod
    def stop(self):
        '''
        Stop the worker.
        '''

        pass


    def remove(self):
        '''
        Remove the worker runtime state. Optional abstract method.
        '''

        pass

