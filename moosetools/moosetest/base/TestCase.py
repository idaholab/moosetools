#* This file is part of MOOSETOOLS repository
#* https://www.github.com/idaholab/moosetools
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moosetools/blob/main/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html

import os
import sys
import io
import enum
import time
import uuid
import logging
import collections
import threading
import traceback
import textwrap
import platform
import contextlib
import subprocess
if platform.python_version() >= "3.7":
    import dataclasses

from moosetools import mooseutils
from moosetools.core import MooseObject
from .Runner import Runner
from .Differ import Differ
from .Controller import Controller

"""
ORIGINAL_PRINT = print#globals()['__builtins__'].print
THREAD_STDOUT = collections.defaultdict(io.StringIO)
THREAD_STDERR = collections.defaultdict(io.StringIO)
def thread_print(*args, **kwargs):
    f = kwargs.get('file', None)
    if (f is None) or (f is sys.stdout):
        f = THREAD_STDOUT[threading.get_ident()]
    elif f is sys.stderr:
        f = THREAD_STDERR[threading.get_ident()]
        kwargs['file'] = f
        ORIGINAL_PRINT(*args, **kwargs)
"""

class State(enum.Enum):
    """
    Enumeration base for defining progress and state values for the `TestCase` object.
    """
    def __new__(cls, value, level, text, color):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.level = level
        obj.text = text
        obj.color = color
        return obj

    @property
    def display(self):
        """
        Return the name (text) of the enum item colored using the defined color of the value.
        """
        return mooseutils.color_text(f"{self.text}", *self.color)

    def format(self, msg, *args, **kwargs):
        """
        Color the supplied *msg* string using the defined color for the enumeration value.

        The *\*args* and *\*\*kwargs* are applied the *msg* string with the built-in python
        `format` function.
        """
        return mooseutils.color_text(msg.format(*args, **kwargs), *self.color)


class RedirectLogs(object):

    def __init__(self, *moose_objects):
        self._objects = moose_objects
        self._stream = io.StringIO()
        self._handler = logging.StreamHandler(self._stream)

    def __enter__(self):
        """
        Setup redirection when entering the context (`with...`).
        """
        for obj in self._objects:
            obj._MooseObject__logger.addHandler(self._handler)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Restore `sys.stdout` and `sys.stderr` when exiting the context.
        """
        for obj in self._objects:
            obj._MooseObject__logger.removeHandler(self._handler)

    @property
    def text(self):
        return self._stream.getvalue()


class TestCase(MooseObject):
    """
    An object for managing the data associated with the execution of a test, which is composed of
    a `Runner` object and optionally one or more `Differ` objects.

    This object does not perform the execution, which is managed via the `moosetest.run` function, it
    is a means for handling the data associated with the execution. It is designed to be instantiated
    on demand in the `moosetest.run` function given `Runner` objects created via the
    `moosetest.discover` function. It is not expected that they will be instituted pragmatically.

    The design of the run (see `moosetest.run`) function is such that all `TestCase` objects are
    created on the root process. Then a pool of subprocesses is are created that execute the tests.
    The results obtained from execution are returned to the root process for reporting. As such,
    the execute methods on this class should be "const" and return the data that is to be
    sent back to the root process instance.
    """

    __TOTAL__ = 0  # total number of TestCase to be executed
    __FINISHED__ = 0  # number of TestCase object finished executed

    class Progress(State):
        """
        Enumeration for reporting the three possible running states of the `TestCase`.

        These values are not related to the result of execution of the `TestCase`, which
        can be waiting to run, running, or done running. The later gets a `Result` state applied
        that indicates what happened during the execution.

        The levels (second argument) are not utilized.
        """
        WAITING = (0, 0, 'WAITING', ('grey_82', ))
        RUNNING = (1, 0, 'RUNNING', ('dodger_blue_3', ))
        FINISHED = (2, 0, 'FINISHED', ('white', ))
        REPORTED = (3, 0, 'REPORTED', None)

    class Result(State):
        """
        Enumeration for reporting the result after the execution of the `TestCase` has finished.

        The levels (second argument) are designed to be used to control what comprises a failure,
        see `moosetest.run` and `moosetest.formatter.BasicFormatter` for example use.
        """
        REMOVE = (10, -2, 'REMOVE', ('grey_27', ))
        SKIP = (11, -1, 'SKIP', ('grey_50', ))
        PASS = (12, 0, 'OK', ('green_1', ))
        TIMEOUT = (13, 1, 'TIMEOUT', ('salmon_1', ))
        DIFF = (14, 2, 'DIFF', ('yellow_1', ))  # error on Differ
        ERROR = (15, 3, 'ERROR', ('red_1', ))  # error on Runner
        EXCEPTION = (16, 4, 'EXCEPTION', ('magenta_1', ))  # exception raised by Runner/Differ
        FATAL = (17, 5, 'FATAL', ('white', 'red_1'))  # internal error (see, run.py)

    if platform.python_version() >= "3.7":

        @dataclasses.dataclass
        class Data(object):
            """
            Data from execution of a `Runner` or `Differ` is returned from a process in this structure.

            This is mainly for convenience for accessing the results related data to allow for the API
            to return a single data object for all result related items and should allow for new items
            to be added if needed as the system expands.
            """
            state: State = None
            returncode: int = None
            text: str = None
            #reasons: list[str] = None #Py3.9 only
            reasons: list = None

    else:

        class Data(object):
            def __init__(self, state=None, returncode=None, text=None, reasons=None):
                self.state = state
                self.returncode = returncode
                self.text = stdout
                self.stderr = stderr
                self.reasons = reasons

            def __eq__(self, other):
                return self.state == other.state and self.returncode == other.returncode and \
                    self.text == other.text and self.reasons == other.reasons

    @staticmethod
    def validParams():
        """
        `TestCase` objects are not designed for internal use and the `validParams` are only set when
        the objects are constructed, which occurs within the `moosetest.run` function. As such, only
        add parameters that you expect that function to set, since there is no configuration file
        based way for altering these.
        """
        params = MooseObject.validParams()
        params.add('runner',
                   vtype=Runner,
                   required=True,
                   mutable=False,
                   doc="The `Runner` object to execute.")
        params.add('controllers',
                   vtype=Controller,
                   array=True,
                   mutable=False,
                   doc="`Controller` object(s) that dictate if the Runner should run.")

        params.add('min_fail_state',
                   vtype=TestCase.Result,
                   mutable=False,
                   default=TestCase.Result.TIMEOUT,
                   doc="The minimum state considered a failure for the entire test case.")
        return params

    def __init__(self, *args, **kwargs):
        MooseObject.__init__(self, *args, **kwargs)

        self._runner = self.getParam('runner')
        self._differs = self._runner.getParam('differs') or tuple()
        self._controllers = self.getParam('controllers') or tuple()
        self._min_fail_state = self.getParam('min_fail_state')
        self.parameters().setValue('name', self._runner.name())

        self.__results = None  # results from the Runner/Differ objects
        self.__progress = None  # execution progress of this TestCase
        self.__state = None  # the overall state (TestCase.Result)

        # The following are various time settings managed via the `setProgress` method
        self.__create_time = time.time()  # time when the object was created
        self.__start_time = None  # time when progress change to running
        self.__end_tie = None # time when progress changed to finished
        self.__execute_time = None  # duration of execution running to finished

        self.__unique_id = uuid.uuid4()  # a unique identifier for this instance

        self.setProgress(TestCase.Progress.WAITING)
        TestCase.__TOTAL__ += 1

    @property
    def unique_id(self):
        """
        Return a unique identifier for this object.
        """
        return self.__unique_id

    @property
    def waiting(self):
        """
        Return True if the test is waiting to start.
        """
        return self.__progress == TestCase.Progress.WAITING

    @property
    def running(self):
        """
        Return True if the test is running.
        """
        return self.__progress == TestCase.Progress.RUNNING

    @property
    def finished(self):
        """
        Return True if the test is finished running.
        """
        return self.__progress == TestCase.Progress.FINISHED

    @property
    def reported(self):
        """
        Return True if the test is finished and the results were reported.
        """
        return self.__progress == TestCase.Progress.REPORTED

    @property
    def progress(self):
        """
        Return the test progress state (TestCase.Progress).
        """
        return self.__progress

    @property
    def runner(self):
        """
        Return the `Runner` object.
        """
        return self._runner

    @property
    def differs(self):
        """
        Return the `Differ` object(s).
        """
        return self._differs

    @property
    def state(self):
        """
        Return the overall result state of the test (TestCase.Result).

        This will return `None` if it has not been set.
        """
        return self.__state

    @property
    def results(self):
        """
        Return the available results.

        This will return None if the `setResults` method has not been called.
        """
        return self.__results

    @property
    def time(self):
        """
        Return the time information based on the progress of the test.

        When the progress is `TestCase.Progress.WAITING` it returns how long the test has been
        waiting to start, when it is `TestCase.Progress.RUNNING` it returns how long the test has
        been running, and when it is `TestCase.Progress.FINISHED` it returns how long the test took
        to execute.

        !alert! info title=Times will be approximate
        The `setProgress` method is called during the on the root process while the various
        subprocesses are executing. It is called will monitoring the subprocess and data that is
        made available via the queue. As such, the times that are set are when the data arrives on
        the root process, not when the data was sent.

        This was done for simplicity, in the future if more accurate time is required the time
        information could be added to the `TestCase.Data` object.
        !alert-end!
        """
        if self.waiting:
            return time.time() - self.__create_time
        elif self.running:
            return time.time() - self.__start_time
        return self.__execute_time

    @property
    def start_time(self):
        """
        Return the start time for the TestCase object.

        See `Formatter.reportProgress`.
        """
        return self.__start_time

    def setStartTime(self, t):
        self.__start_time = t

    def setExecuteTime(self, t):
        self.__execute_time = t

    def setInfo(self, *, progress=None, state=None, results=None, start_time=None, execute_time=None):
        """
        Update items (e.g., progress, state, results) on this object.
        """
        if progress is not None: self.setProgress(progress)
        if state is not None: self.setState(state)
        if results is not None: self.setResults(results)
        if start_time is not None: self.setStartTime(start_time)
        if execute_time is not None: self.setExecuteTime(execute_time)

    def setProgress(self, progress):
        """
        Update this execution status with *progress*.

        See `moosetest.run` for use.
        """
        if not isinstance(progress, TestCase.Progress):
            with RedirectLogs(self) as out:
                self.critical("The supplied progress must be of type `TestCase.Progress`.")
            results = {
                self._runner.name():
                TestCase.Data(TestCase.Result.FATAL, None, out.text, None)
            }
            self.setState(TestCase.Result.FATAL)
            self.setResults(results)
            progress = TestCase.Progress.FINISHED

        """
        current = time.time()
        if progress == TestCase.Progress.WAITING:
            if self.__create_time is None: self.__create_time = current
        elif progress == TestCase.Progress.RUNNING:
            if self.__start_time is None: self.__start_time = current
        elif progress == TestCase.Progress.FINISHED:
            TestCase.__FINISHED__ += 1
            if self.__execute_time is None:
                self.__execute_time = current - self.__start_time if self.__start_time else 0
        """

        if not self.finished and (progress == TestCase.Progress.FINISHED):
            TestCase.__FINISHED__ += 1

        self.__progress = progress

    def setState(self, state):
        """
        Update the result status of this object with *state*.

        See `moosetest.run` for use.
        """
        if not isinstance(state, TestCase.Result):
            with RedirectLogs(self) as out:
                self.critical("The supplied state must be of type `TestCase.Result`.")
            results = {
                self._runner.name():
                TestCase.Data(TestCase.Result.FATAL, None, out.text, None)
            }
            self.setProgress(TestCase.Progress.FINISHED)
            self.setResults(results)
            state = TestCase.Result.FATAL

        self.__state = state

    def setResults(self, results):
        """
        Store the data returned from the `execute` method.

        In practice the data is computed on a subprocess and then stored on the root processor
        instance using this function.

        See `moosetest.run`.
        """
        # Attempt to avoid adding unexpected data. If a problem is detected change the state and
        # log a critical error message.
        with RedirectLogs(self) as out:
            self.reset()

            if not isinstance(results, dict):
                self.critical("The supplied result must be of type `dict`.")

            if any(not isinstance(val, TestCase.Data) for val in results.values()):
                self.critical("The supplied result values must be of type `TestCase.Data`.")

            names = [self._runner.name()] + [d.name() for d in self._differs]
            if any(key not in names for key in results.keys()):
                self.critical("The supplied result keys must be the names of the `Runner` or `Differ` object(s).")

            if self.status():
                results = {
                    self._runner.name():
                    TestCase.Data(TestCase.Result.FATAL, None, out.text, None)
                }
                self.setState(TestCase.Result.FATAL)

        self.__results = results

    def execute(self):
        """
        Execute the test starting with `Runner` followed by `Differ` objects, if they exist.

        This method should return a `dict` that contains a `TestCase.Data` object for the `Runner`
        and `Differ` objects, using the names of these objects as the key.

        !alert warning title=Must return state and results
        The `execute` method is called via the `moosetest.run` function on a subprocess. The state
        and results returned from this method are communicated to the root process instance and
        stored there for reporting.
        """
        # The results to be returned
        results = dict()

        # Get the working directory, this parameter is tested for validity in the Runner so raise
        # an exception if it doesn't exist
        working_dir = self._runner.getParam('working_dir')
        if not os.path.isdir(working_dir):
            raise RuntimeError(f"The 'working_dir' does not exist: {working_dir}")

        # Execute the runner, if it does not return a PASS state, then execution is complete
        r_data = self._executeObject(self._runner)
        results[self._runner.name()] = r_data
        if r_data.state.level != 0:
            return r_data.state, results

        # Execute the differs, when the runner returns a PASS state. All differs run, regardless of
        # the state returned by each. The overall state is tracked and is always set to the largest
        # state level.
        state = r_data.state
        for obj in self._differs:
            d_data = self._executeObject(obj, r_data.returncode, r_data.text)
            results[obj.name()] = d_data
            if (d_data.state.level >= self._min_fail_state.level) and (d_data.state.level >
                                                                       state.level):
                state = d_data.state

        return state, results

    def _executeObject(self, obj, *args, **kwargs):
        """
        Call the `execute` method of the supplied *obj* with *\*args* and *\*\*kwargs* as arguments.

        The `TestCase.execute` method calls this for the `Runner` object and `Differ` objects, if
        any. Prior to executing the *obj*, it is passed to the `Controller` objects associated
        with this object upon construction. Then, if the object is allowed to execute, it does.

        !alert info
        This method is designed to be as stable as possible, i.e., it should not raise an exception
        regardless of the object being executed. But, just in case there is additional protection
        around the calling it (via `TestCase.execute` method) in the
        `moosetest.run._execute_testcase` function.
        """

        # The supplied *obj* as well as the `Controller` objects are expected to be a
        # `core.MooseObject` derived objects. As such the built-in logging capability is leveraged.
        # When executing any object the first step is to clear any logged errors, which is done by
        # calling the `reset` method. All calls are also wrapped in a try-statement to catch any
        # unexpected problems and the output is redirected such that it can be reported to the root
        # instance of the `TestCase` object. Unexpected problems result in a FATAL status being
        # returned.


        with RedirectLogs(self, obj, *self._controllers) as out:

            # Reset the state of supplied "obj". The status of the object will be checked after all
            # calls that could lead the object to produce an error are completed. The object status at
            # this point indicates if the objected execution succeeded.
            try:
                obj.reset()  # clear log counts of the object to be passed to the Controller
            except Exception as ex:
                self.exception(
                    "An exception occurred within the `reset` method of the '{}' object.",
                    obj.name())
                return TestCase.Data(TestCase.Result.FATAL, None, out.text, None)

            # Loop through each `Controller` object
            for controller in self._controllers:

                # Skip of controller not associated with current type
                if not isinstance(obj, controller.OBJECT_TYPES):
                    self.debug(
                        "Controller object of type '{}' is not setup to execute with an object of type '{}'.",
                        type(controller), type(obj))
                    continue

                # Execute the `Controller`
                try:
                    controller.reset()  # clear log counts
                    params = obj.getParam(controller.getParam('prefix')) if controller.isParamValid(
                        'prefix') else None
                    controller.execute(obj, params)

                    # Stop if an error is logged on the Controller object
                    if controller.status():
                        self.error(
                            "An error occurred, on the controller, within the `execute` method of the {} controller with '{}' object.",
                            type(controller).__name__, obj.name())
                        return TestCase.Data(TestCase.Result.FATAL, None, out.text, controller.getReasons())

                    # Stop if an error is logged on the object, due to execution of Controller
                    if obj.status():
                        self.error(
                            "An error occurred, on the object, within the `execute` method of the {} controller with '{}' object.",
                            type(controller).__name__, obj.name())
                        return TestCase.Data(TestCase.Result.FATAL, None, out.text, obj.getReasons())

                    # Skip it...maybe
                    c_state = controller.state()
                    if c_state is not None:
                        return TestCase.Data(c_state, None, out.text, controller.getReasons())

                except Exception as ex:
                    self.error(
                        "An exception occurred within the `execute` method of the {} controller with '{}' object.\n{}",
                        type(controller).__name__, obj.name(), traceback.format_exc())
                    return TestCase.Data(TestCase.Result.FATAL, None, out.text, None)

            # Call `preExecute`, stop if this fails in any capacity
            try:
                obj.reset()
                obj.preExecute()
                if obj.status():
                    self.error(
                        "An error occurred within the `preExecute` method of the '{}' object.",
                        obj.name())
                    return TestCase.Data(TestCase.Result.FATAL, None, out.text, obj.getReasons())

            except Exception as ex:
                self.exception(
                    "An exception occurred within the `preExecute` method of the '{}' object.",
                    obj.name())
                return TestCase.Data(TestCase.Result.FATAL, None, out.text, None)

            # Call `execute`, always call `postExecute` even if this fails
            execute_failure = None
            try:
                obj.reset()
                rcode = obj.execute(*args, **kwargs)
                print(out.text)
                if obj.status():
                    state = TestCase.Result.DIFF if isinstance(obj,
                                                               Differ) else TestCase.Result.ERROR
                    self.error("An error occurred within the `execute` method of the '{}' object.",
                               obj.name())
                    execute_failure = TestCase.Data(state, rcode, out.text, obj.getReasons())

            except subprocess.TimeoutExpired as ex:

                self.error("An timeout occurred within the `execute` method of the '{}' object.",
                           obj.name())
                execute_failure = TestCase.Data(TestCase.Result.TIMEOUT, None, out.text, None)

            except Exception as ex:
                self.exception(
                    "An exception occurred within the `execute` method of the '{}' object.",
                    obj.name())
                execute_failure = TestCase.Data(TestCase.Result.EXCEPTION, None, out.text, None)

            # Call `postExecute`
            try:
                obj.reset()
                obj.postExecute()
                if obj.status():
                    self.error(
                        "An error occurred within the `postExecute` method of the '{}' object.",
                        obj.name())
                    return TestCase.Data(TestCase.Result.FATAL, None, out.text, obj.getReasons())

            except Exception as ex:
                self.exception(
                    "An exception occurred within the `postExecute` method of the '{}' object.",
                    obj.name())
                return TestCase.Data(TestCase.Result.FATAL, None, out.text, None)

            if execute_failure is not None:
                return execute_failure

        #TODO: This prefixing should be moved to BasicFormatter, don't recall why it is here
        #stdout += textwrap.indent(stdout, mooseutils.color_text('sys.stdout > ', 'grey_30'))
        #stderr += textwrap.indent(stderr, mooseutils.color_text('sys.stderr > ', 'grey_30'))
        #
        # I think what is need is a way to distinguish between output from moosetest errors/messages
        # vs. output from the execute methods...
        #
        return TestCase.Data(TestCase.Result.PASS, rcode, out.text, obj.getReasons())
