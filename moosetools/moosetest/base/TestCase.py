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
import multiprocessing
import traceback
from dataclasses import dataclass
import textwrap

from moosetools import mooseutils
from moosetools.base import MooseObject
from .Runner import Runner
from .Differ import Differ
from .Controller import Controller


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


class RedirectOutput(object):
    """
    A context object (i.e., `with...`) for redirecting sys.stdout and sys.stderr to `dict` keyed
    on the current process.

    This object is used by the `TestCase` object to extract all output from the execution of the
    `TestCase` so that that it can be sent back to the root process for output.

    It also updates the `Handler` objects from the `logging` package, which store their own
    reference to `sys.stderr`. Thus, without this the logging output will not be redirected.
    """
    class SysRedirect(object):
        """
        A replacement IO object for sys.stdout/err that stores content in *out*, which should be a
        `dict` of `io.StringIO` objects.
        """
        def __init__(self, out):
            self._out = out

        def write(self, message):
            self._out[multiprocessing.current_process().pid].write(message)

        def flush(self):
            pass

    def __init__(self):
        self._stdout = collections.defaultdict(io.StringIO)
        self._stderr = collections.defaultdict(io.StringIO)

        self._sys_stdout = sys.stdout
        self._sys_stderr = sys.stderr

        self._logging_handlers = list()  # storage for (handler, formatter) for resetting stream

    @property
    def stdout(self):
        """
        Return the redirect output to `sys.stdout` for the current process.
        """
        return self._stdout[multiprocessing.current_process().pid].getvalue()

    @property
    def stderr(self):
        """
        Return the redirect output to `sys.stderr` for the current process.
        """
        return self._stderr[multiprocessing.current_process().pid].getvalue()

    def __enter__(self):
        """
        Setup redirection when entering the context (`with...`).
        """
        self._logging_handlers = list()
        sys.stdout = RedirectOutput.SysRedirect(self._stdout)
        sys.stderr = RedirectOutput.SysRedirect(self._stderr)

        logger = logging.getLogger()
        for h in logger.handlers:
            if hasattr(h, 'setStream'):
                self._logging_handlers.append((h, h.formatter))
                h.setStream(sys.stderr)
                h.setFormatter(logging.Formatter())

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Restore `sys.stdout` and `sys.stderr` when exiting the context.
        """
        sys.stdout = self._sys_stdout
        sys.stderr = self._sys_stderr

        for h, f in self._logging_handlers:
            h.setStream(self._sys_stderr)
            h.setFormatter(f)


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

    class Result(State):
        """
        Enumeration for reporting the result after the execution of the `TestCase` has finished.

        The levels (second argument) are designed to be used to control what comprises a failure,
        see `moosetest.run` and `moosetest.formatter.BasicFormatter` for example use.
        """
        PASS = (10, 0, 'OK', ('green_1', ))
        SKIP = (11, 1, 'SKIP', ('grey_42', ))
        TIMEOUT = (12, 2, 'TIMEOUT', ('salmon_1', ))
        DIFF = (13, 3, 'DIFF', ('yellow_1', ))  # error on Differ
        ERROR = (14, 4, 'ERROR', ('red_1', ))  # error on Runner
        EXCEPTION = (15, 5, 'EXCEPTION', ('magenta_1', ))  # exception raised by Runner/Differ
        FATAL = (16, 6, 'FATAL', ('white', 'red_1'))  # internal error (see, run.py)

    @dataclass
    class Data:
        """
        Data from execution of a `Runner` or `Differ` is returned from a process in this structure.

        This is mainly for convenience for accessing the results related data to allow for the API
        to return a single data object for all result related items and should allow for new items
        to be added if needed as the system expands.
        """
        state: State = None
        returncode: int = None
        stdout: str = None
        stderr: str = None
        #reasons: list[str] = None #Py3.9 only
        reasons: list = None

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
        params.add('_unique_id',
                   vtype=uuid.UUID,
                   mutable=True,
                   private=True,
                   doc="A unique id used for collecting data returned from sub-processes.")
        return params

    def __init__(self, *args, **kwargs):
        kwargs['_unique_id'] = uuid.uuid4()
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
        self.__create_time = None  # time when the object was created
        self.__start_time = None  # time when progress change to running
        self.__execute_time = None  # duration of execution running to finished

        self.setProgress(TestCase.Progress.WAITING)
        TestCase.__TOTAL__ += 1

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
        current = time.time()
        if self.waiting:
            return current - self.__create_time
        elif self.running:
            return current - self.__start_time

        return self.__execute_time

    def setProgress(self, progress):
        """
        Update this execution status with *progress*.

        See `moosetest.run` for use.
        """
        if not isinstance(progress, TestCase.Progress):
            with RedirectOutput() as out:
                self.critical("The supplied progress must be of type `TestCase.Progress`.")
            results = {
                self._runner.name():
                TestCase.Data(TestCase.Result.FATAL, None, out.stdout, out.stderr, None)
            }
            self.setState(TestCase.Result.FATAL)
            self.setResults(results)
            progress = TestCase.Progress.FINISHED

        current = time.time()
        if progress == TestCase.Progress.WAITING:
            if self.__create_time is None: self.__create_time = current
        elif progress == TestCase.Progress.RUNNING:
            if self.__start_time is None: self.__start_time = current
        elif progress == TestCase.Progress.FINISHED:
            TestCase.__FINISHED__ += 1
            if self.__execute_time is None:
                self.__execute_time = current - self.__start_time if self.__start_time else 0

        self.__progress = progress

    def setState(self, state):
        """
        Update the result status of this object with *state*.

        See `moosetest.run` for use.
        """
        if not isinstance(state, TestCase.Result):
            with RedirectOutput() as out:
                self.critical("The supplied state must be of type `TestCase.Result`.")
            results = {
                self._runner.name():
                TestCase.Data(TestCase.Result.FATAL, None, out.stdout, out.stderr, None)
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
        if not isinstance(results, dict):
            with RedirectOutput() as out:
                self.critical("The supplied result must be of type `dict`.")
            results = {
                self._runner.name():
                TestCase.Data(TestCase.Result.FATAL, None, out.stdout, out.stderr, None)
            }
            self.setState(TestCase.Result.FATAL)

        if any(not isinstance(val, TestCase.Data) for val in results.values()):
            with RedirectOutput() as out:
                self.critical("The supplied result values must be of type `TestCase.Data`.")
            results = {
                self._runner.name():
                TestCase.Data(TestCase.Result.FATAL, None, out.stdout, out.stderr, None)
            }
            self.setState(TestCase.Result.FATAL)

        names = [self._runner.name()] + [d.name() for d in self._differs]
        if any(key not in names for key in results.keys()):
            with RedirectOutput() as out:
                self.critical(
                    "The supplied result keys must be the names of the `Runner` or `Differ` object(s)."
                )
            results = {
                self._runner.name():
                TestCase.Data(TestCase.Result.FATAL, None, out.stdout, out.stderr, None)
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

        # Execute the runner, if it does not return a PASS state, then execution is complete
        r_data = self._executeObject(self._runner)
        results[self._runner.name()] = r_data
        if r_data.state.level > 0:
            return r_data.state, results

        # Execute the differs, when the runner returns a PASS state. All differs run, regardless of
        # the state returned by each. The overall state is tracked and is always set to the largest
        # state level.
        state = r_data.state
        for obj in self._differs:
            d_data = self._executeObject(obj, r_data.returncode, r_data.stdout, r_data.stderr)
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
        # `base.MooseObject` derived objects. As such the built-in logging capability is leveraged.
        # When executing any object the first step is to clear any logged errors, which is done by
        # calling the `reset` method. All calls are also wrapped in a try-statement to catch any
        # unexpected problems and the output is redirected such that it can be reported to the root
        # instance of the `TestCase` object. Unexpected problems result in a FATAL status being
        # returned.

        # All output from the various calls are accumulated so that all output is returned to the
        # stored in the object on the main process
        stdout = ''
        stderr = ''

        # Reset the state of supplied "obj". The status of the object will be checked after all
        # calls that could lead the object to produce an error are completed. The object status at
        # this point indicates if the objected execution succeeded.
        with RedirectOutput() as out:
            try:
                obj.reset()  # clear log counts of the object to be passed to the Controller
            except Exception as ex:
                self.exception(
                    "An exception occurred while calling the `reset` method of the '{}' object.",
                    obj.name())
                return TestCase.Data(TestCase.Result.FATAL, None, out.stdout, out.stderr, None)

            finally:
                stdout += out.stdout
                stderr += out.stderr

        # Loop through each `Controller` object
        for controller in self._controllers:

            # Execute the `Controller`
            with RedirectOutput() as out:
                try:
                    controller.reset()  # clear log counts
                    controller.execute(obj, obj.getParam(controller.getParam('prefix')))

                    # Stop if an error is logged on the Controller object
                    if controller.status():
                        self.error(
                            "An error occurred, on the controller, during execution of the {} controller with '{}' object.",
                            type(controller).__name__, obj.name())
                        return TestCase.Data(TestCase.Result.FATAL, None, out.stdout, out.stderr,
                                             None)

                    # Stop if an error is logged on the object, due to execution of Controller
                    if obj.status():
                        self.error(
                            "An error occurred, on the object, during execution of the {} controller with '{}' object.",
                            type(controller).__name__, obj.name())
                        return TestCase.Data(TestCase.Result.FATAL, None, out.stdout, out.stderr,
                                             None)

                    # Skip it...maybe
                    if not controller.isRunnable():
                        return TestCase.Data(TestCase.Result.SKIP, None, out.stdout, out.stderr,
                                             controller.reasons())

                except Exception as ex:
                    self.error(
                        "An exception occurred during execution of the {} controller with '{}' object.\n{}",
                        type(controller).__name__, obj.name(), traceback.format_exc())
                    return TestCase.Data(TestCase.Result.FATAL, None, out.stdout, out.stderr, None)

                finally:
                    stdout += out.stdout
                    stderr += out.stderr

        # Execute the object
        with RedirectOutput() as out:
            try:
                rcode = obj.execute(*args, **kwargs)

                # Errors on object result in failure
                if obj.status():
                    state = TestCase.Result.DIFF if isinstance(obj,
                                                               Differ) else TestCase.Result.ERROR
                    self.error("An error occurred during execution of the '{}' object.", obj.name())
                    return TestCase.Data(state, rcode, out.stdout, out.stderr, None)

            except Exception as ex:
                self.exception("An exception occurred during execution of the '{}' object.",
                               obj.name())
                return TestCase.Data(TestCase.Result.EXCEPTION, None, out.stdout, out.stderr, None)

            finally:
                stdout += out.stdout
                stderr += out.stderr

        return TestCase.Data(TestCase.Result.PASS, rcode, stdout, stderr, None)
