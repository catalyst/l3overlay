#
# IPsec overlay network manager (l3overlay)
# l3overlay/util/worker.py - worker abstract base class
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
Worker abstract base class.
'''


import abc

from l3overlay.util.exception import L3overlayError


STATES = ("settingup", "setup", "starting", "started", "stopping", "stopped", "removing", "removed")


class InvalidWorkerStateError(L3overlayError):
    '''
    Exception raised when an invalid worker state type was found.
    '''
    def __init__(self, worker, state, states):
        super().__init__(
            "invalid worker state type '%s' for %s, expected one of %s" %
            (state, worker.description, str.join(states, "/")),
        )

class InvalidWorkerStateValueError(L3overlayError):
    '''
    Exception raised when an invalid worker state value was found.
    '''
    def __init__(self, worker, state, value):
        super().__init__(
            "invalid worker state value '%s' in state type '%s' for %s, expected True/False" %
            (value, state, worker.description),
        )


class SetupTwiceError(L3overlayError):
    '''
    Exception raised when set_settingup() has been invoked twice.
    '''
    def __init__(self, worker):
        super().__init__("%s setup twice" % worker.description)

class NotYetSettingupError(L3overlayError):
    '''
    Exception raised when set_setup() has been invoked without calling set_settingup() first.
    '''
    def __init__(self, worker):
        super().__init__("%s not yet set to setting up" % worker.description)

class NotYetSetupError(L3overlayError):
    '''
    Exception raised when set_starting() has been invoked without the worker being setup first.
    '''
    def __init__(self, worker):
        super().__init__("%s not yet set up" % worker.description)


class StartedTwiceError(L3overlayError):
    '''
    Exception raised when set_starting() has been invoked twice.
    '''
    def __init__(self, worker):
        super().__init__("%s started twice" % worker.description)

class NotYetStartingError(L3overlayError):
    '''
    Exception raised when set_started() has been invoked without calling set_starting() first.
    '''
    def __init__(self, worker):
        super().__init__("%s not yet set to starting" % worker.description)

class NotYetStartedError(L3overlayError):
    '''
    Exception raised when set_stopping() has been invoked without the worker being started first.
    '''
    def __init__(self, worker):
        super().__init__("%s not yet started" % worker.description)


class StoppedTwiceError(L3overlayError):
    '''
    Exception raised when set_stopping() has been invoked twice.
    '''
    def __init__(self, worker):
        super().__init__("%s stopped twice" % worker.description)

class NotYetStoppingError(L3overlayError):
    '''
    Exception raised when set_stopped() has been invoked without calling set_stopping() first.
    '''
    def __init__(self, worker):
        super().__init__("%s not yet set to stopping" % worker.description)

class NotYetStoppedError(L3overlayError):
    '''
    Exception raised when set_removing() has been invoked without the worker being stopped first.
    '''
    def __init__(self, worker):
        super().__init__("%s not yet stopped" % worker.description)


class RemovedTwiceError(L3overlayError):
    '''
    Exception raised when set_removing() has been invoked twice.
    '''
    def __init__(self, worker):
        super().__init__("%s removed twice" % worker.description)

class NotYetRemovingError(L3overlayError):
    '''
    Exception raised when set_removed() has been invoked without calling set_removing() first.
    '''
    def __init__(self, worker):
        super().__init__("%s not yet set to removing" % worker.description)


class Worker(metaclass=abc.ABCMeta):
    '''
    Abstract base class for classes which use a 'start-stop' service
    operation style. Implements the internal fields and helper methods
    for this.
    '''

    # pylint: disable=too-many-public-methods

    description = "worker"


    def __init__(self, states=None, use_setup=False, use_remove=False):
        '''
        Set up worker internal fields.
        '''

        self.use_setup = use_setup
        self.use_remove = use_remove

        self._states = dict.fromkeys(
            STATES,
            False,
        )

        # State value override.
        if states:
            for (key, value) in states.items():
                if key in self._states:
                    if not isinstance(value, bool):
                        raise InvalidWorkerStateValueError(self, key, value)
                    self._states[key] = value
                else:
                    raise InvalidWorkerStateError(self, key, self._states.keys())


    def _assert_state(self):
        '''
        Check that the worker state is valid.
        '''

        for state, value in self._states.items():
            if state not in STATES:
                raise InvalidWorkerStateError(self, state, STATES)
            if not isinstance(value, bool):
                raise InvalidWorkerStateError(self, state, value)


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
            raise SetupTwiceError(self)

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
            raise SetupTwiceError(self)

        if not self.is_settingup():
            raise NotYetSettingupError(self)

        self._states["settingup"] = False
        self._states["setup"] = True

        self._states["removing"] = False
        self._states["removed"] = False


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
            raise StartedTwiceError(self)

        if self.use_setup and not self.is_setup():
            raise NotYetSetupError(self)

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
            raise StartedTwiceError(self)

        if self.use_setup and not self.is_setup():
            raise NotYetSetupError(self)

        if not self.is_starting():
            raise NotYetStartingError(self)

        self._states["starting"] = False
        self._states["started"] = True

        self._states["stopping"] = False
        self._states["stopped"] = False


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
            raise StoppedTwiceError(self)

        if not self.is_started():
            raise NotYetStartedError(self)

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
            raise StoppedTwiceError(self)

        if not self.is_started():
            raise NotYetStartedError(self)

        if not self.is_stopping():
            raise NotYetStoppingError(self)

        self._states["stopping"] = False
        self._states["stopped"] = True

        self._states["starting"] = False
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
            raise RemovedTwiceError(self)

        if self.is_started():
            raise NotYetStoppedError(self)

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
            raise RemovedTwiceError(self)

        if self.is_started():
            raise NotYetStoppedError(self)

        if not self.is_removing():
            raise NotYetRemovingError(self)

        self._states["removing"] = False
        self._states["removed"] = True

        self._states["settingup"] = False
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
