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
from .Formatter import Formatter

class State(enum.Enum):
    def __new__(cls, value, level, text, color):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.level = level
        obj.text = text
        obj.color = color
        return obj

    @property
    def display(self):
        return mooseutils.color_text(f"{self.text}", *self.color)

    def format(self, msg, *args, **kwargs):
        return mooseutils.color_text(msg.format(*args, **kwargs), *self.color)


class RedirectOutput(object):
    class SysRedirect(object):
        def __init__(self, sysout, out):
            self._sysout = sysout
            self._out = out

        @property
        def is_main(self):
            return multiprocessing.parent_process() is None
            #return threading.main_thread().ident == threading.current_thread().ident

        def write(self, message):
            if self.is_main:
                self._sysout.write(message)
            else:
                self._out[multiprocessing.current_process().pid].write(message)
                #self._out[threading.current_thread().ident].write(message)

        def flush(self):
            if self.is_main:
                self._sysout.flush()

    def __init__(self):
        self._stdout = collections.defaultdict(io.StringIO)
        self._stderr = collections.defaultdict(io.StringIO)

        self._sys_stdout = sys.stdout
        self._sys_stderr = sys.stderr

        self._logging_handlers = list()

    @property
    def stdout(self):
        return self._stdout[multiprocessing.current_process().pid].getvalue()
        #return self._stdout[threading.current_thread().ident].getvalue()

    @property
    def stderr(self):
        return self._stderr[multiprocessing.current_process().pid].getvalue()
        #return self._stderr[threading.current_thread().ident].getvalue()

    def __enter__(self):
        self._logging_handlers = list()
        sys.stdout = RedirectOutput.SysRedirect(self._sys_stdout, self._stdout)
        sys.stderr = RedirectOutput.SysRedirect(self._sys_stderr, self._stderr)

        logger = logging.getLogger()
        for h in logger.handlers:
            if hasattr(h, 'setStream'):
                self._logging_handlers.append((h, h.formatter))
                h.setStream(sys.stderr)
                h.setFormatter(logging.Formatter())

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        sys.stdout = self._sys_stdout
        sys.stderr = self._sys_stderr

        for h, f in self._logging_handlers:
            h.setStream(self._sys_stderr)
            h.setFormatter(f)

class TestCase(MooseObject):

    __TOTAL = 0
    __FINISHED = 0

    class Progress(State):
        WAITING  = (0, 0, 'WAITING', ('grey_82',))
        RUNNING  = (1, 0, 'RUNNING', ('dodger_blue_3',))
        FINISHED = (2, 0, 'FINISHED', ('white',))

    class Result(State):
        PASS      = (10, 0, 'OK', ('green_1',))
        SKIP      = (11, 1, 'SKIP', ('grey_42',))
        TIMEOUT   = (12, 2, 'TIMEOUT', ('orange_1',))
        ERROR     = (13, 3, 'ERROR', ('red_1',))
        EXCEPTION = (14, 4, 'EXCEPTION', ('magenta_1',))
        FATAL     = (15, 5, 'FATAL', ('white', 'red_1')) # internal error (see, run.py)

    @dataclass
    class Data:
        state: State = None
        returncode: int = None
        stdout: str = None
        stderr: str = None
        reasons: list[str] = None

    @staticmethod
    def validParams():
        params = MooseObject.validParams()

        params.add('runner', vtype=Runner, required=True, mutable=False,
                   doc="The `Runner` object to execute.")
        params.add('formatter', vtype=Formatter, required=False, mutable=True,
                   doc="The `Formatter` object for displaying test case progress and results.")
        params.add('controllers', vtype=Controller, array=True, mutable=False,
                   doc="`Controller` object(s) that dictate if the Runner should run.")

        params.add('_unique_id', vtype=uuid.UUID, mutable=True, private=True)

        # TODO: comment on these: Don't add anything here, these don't get set from anywhere

        return params

    def __init__(self, *args, **kwargs):
        kwargs['_unique_id'] = uuid.uuid4()
        MooseObject.__init__(self, *args, **kwargs)

        self._runner = self.getParam('runner')
        self._differs = self._runner.getParam('differs') or tuple()
        self._formatter = self.getParam('formatter')
        self._controllers = self.getParam('controllers') or tuple()
        self.parameters().set('name', self._runner.name())

        self.__results = None
        self.__progress = None
        self.__state = None

        self.__progress_time = None
        self.__create_time = None
        self.__start_time = None
        self.__execute_time = None

        TestCase.__TOTAL += 1

        self.setProgress(TestCase.Progress.WAITING)

    @property
    def waiting(self):
        return self.__progress == TestCase.Progress.WAITING

    @property
    def running(self):
        return self.__progress == TestCase.Progress.RUNNING

    @property
    def finished(self):
        return self.__progress == TestCase.Progress.FINISHED

    @property
    def state(self):
        return self.__state

    @property
    def progress(self):
        return self.__progress

    @property
    def time(self):
        """
        TODO: error check that execute_time exists
        """


        current = time.time()
        if self.waiting:
            return current - self.__create_time
        elif self.running:
            return current - self.__progress_time

        return self.__execute_time

    def redirectOutput(self):
        return RedirectOutput()

    def setProgress(self, progress):
        current = time.time()
        if progress == TestCase.Progress.WAITING:
            if self.__create_time is None: self.__create_time = current
            self.__progress_time = current
        elif progress == TestCase.Progress.RUNNING:
            if self.__start_time is None: self.__start_time = current
            self.__progress_time = current
        elif progress == TestCase.Progress.FINISHED:
            TestCase.__FINISHED += 1
            if self.__execute_time is None: self.__execute_time = current - self.__start_time if self.__start_time else 0

        self.__progress = progress

    def execute(self):
        """

        """
        results = dict()

        r_data = self.executeObject(self._runner)
        results[self._runner.name()] = r_data
        if r_data.state.level > 0:
            return r_data.state, results

        state = r_data.state
        for obj in self._differs:
            d_data = self.executeObject(obj, r_data.returncode, r_data.stdout, r_data.stderr)
            results[obj.name()] = d_data
            if d_data.state.level > state.level:
                state = d_data.state

        return state, results

    def executeObject(self, obj, *args, **kwargs):

        # Reset the state of supplied "obj". The status of the object will be checked after all
        # calls that could lead the object to produce an error. If an error is detected a FATAL
        # state is returned.
        with self.redirectOutput() as out:
            try:
                obj.reset() # clear log counts of the object to be passed to the Controller
            except Exception as ex:
                self.exception("An error occurred while calling the reset method of the '{}' object.", obj.name())
                return TestCase.Data(TestCase.Result.FATAL, 1, out.stdout, out.stderr, None)

        # Loop through each `Controller` object
        for controller in self._controllers:

            # Execute the `Controller`
            with self.redirectOutput() as out:
                try:
                    controller.reset() # clear log counts
                    controller.execute(obj, obj.getParam(controller.getParam('prefix')))

                    # Stop if an error is logged on the Controller object
                    if controller.status():
                        self.error("An error occurred, on the controller, during execution of the {} with '{}' object.", type(controller).__name__, obj.name())
                        return TestCase.Data(TestCase.Result.FATAL, 1, out.stdout, out.stderr, None)

                    # Stop if an error is logged on the object, due to execution of Controller
                    if obj.status():
                        self.error("An error occurred, on the object, during execution of the {} with '{}' object.", type(controller).__name__, obj.name())
                        return TestCase.Data(TestCase.Result.FATAL, 1, out.stdout, out.stderr, None)

                    # Skip it...maybe
                    if not controller.isRunnable():
                        return TestCase.Data(TestCase.Result.SKIP, 0, out.stdout, out.stderr, controller.reasons())

                except Exception as ex:
                    self.error("An exception occurred during execution of the {} with '{}' object.\n{}", type(controller).__name__, obj.name(), traceback.format_exc())
                    return TestCase.Data(TestCase.Result.FATAL, 1, out.stdout, out.stderr, None)

        # Execute the object
        with self.redirectOutput() as out:
            try:
                rcode = obj.execute(*args, **kwargs)

                # Errors on object result in failure
                if obj.status():
                    self.error("An error occurred during execution of the '{}' object.", obj.name())
                    return TestCase.Data(TestCase.Result.ERROR, 1, out.stdout, out.stderr, None)

            except Exception as ex:
                self.exception("An exception occurred during execution of the '{}' object.", obj.name())
                return TestCase.Data(TestCase.Result.EXCEPTION, 1, out.stdout, out.stderr, None)


        return TestCase.Data(TestCase.Result.PASS, rcode, out.stdout, out.stderr, None)

    def setState(self, state):
        self.__state = state

    def setResult(self, result):
        self.__results = result

    def reportResult(self):
        r_data = self.__results.get(self._runner.name())

        self._printState(self._runner, self.__state, r_data.reasons)
        self._printResult(self._runner, r_data)

        for obj in [d for d in self._differs if d.name() in self.__results]:
            d_data = self.__results.get(obj.name())
            self._printState(obj, d_data.state, d_data.reasons)
            self._printResult(obj, d_data)

    def reportProgress(self):
        self._printState(self._runner, self.__progress, None)
        self.__progress_time = time.time()

    def _printState(self, obj, state, reasons):
        """
        """
        if state == TestCase.Progress.RUNNING:
            duration = time.time() - self.__start_time
        else:
            duration = self.__execute_time

        # TODO: Document these items and make them the same
        kwargs = dict()
        kwargs['name'] = obj.name()
        kwargs['state'] = state
        kwargs['reasons'] = reasons
        kwargs['duration'] = duration
        kwargs['percent'] = TestCase.__FINISHED / TestCase.__TOTAL * 100

        if obj is self._runner:
            txt = self._formatter.formatRunnerState(**kwargs)
        else:
            txt = self._formatter.formatDifferState(**kwargs)
        if txt:
            print(txt)

    def _printResult(self, obj, data):
        """
        """
        kwargs = dict()

        # TODO: Document these items
        kwargs['name'] = obj.name()
        kwargs['state'] = data.state
        kwargs['reasons'] = data.reasons
        kwargs['returncode'] = data.returncode
        kwargs['duration'] = self.__execute_time
        kwargs['percent'] = TestCase.__FINISHED / TestCase.__TOTAL * 100

        kwargs['stdout'] = data.stdout
        kwargs['stderr'] = data.stderr

        if obj is self._runner:
            txt = self._formatter.formatRunnerResult(**kwargs)
        else:
            txt = self._formatter.formatDifferResult(**kwargs)
        if txt:
            print(txt)
