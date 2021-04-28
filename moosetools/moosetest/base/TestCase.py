import os
import sys
import io
import enum
import time
import uuid
import logging
import collections
import multiprocessing
#import threading
import textwrap
from moosetools import mooseutils
from moosetools.base import MooseObject
#from .MooseTestController import MooseTestController
from .Runner import Runner
from .Differ import Differ
from .Controller import Controller
from .Formatter import Formatter



class State(enum.Enum):
    def __new__(cls, value, level, display, color):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.level = level
        obj.display = display
        obj.color = color
        return obj


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
    class Progress(State):
        WAITING  = (0, 0, 'WAITING', ('grey_82',))
        RUNNING  = (1, 0, 'RUNNING', ('dodger_blue_3',))
        FINISHED = (2, 0, 'FINISHED', ('white',))

    class Result(State):
        PASS      = (10, 0, 'OK', ('green_1',))
        SKIP      = (11, 1, 'SKIP', ('cyan_1',))
        TIMEOUT   = (12, 2, 'TIMEOUT', ('orange_1',))
        ERROR     = (13, 3, 'ERROR', ('red_1',))
        EXCEPTION = (14, 4, 'EXCEPTION', ('magenta_1',))
        FATAL     = (15, 5, 'FATAL', ('white', 'red_1')) # internal error (see, run.py)

    @staticmethod
    def validParams():
        params = MooseObject.validParams()

        params.add('runner', vtype=Runner, required=True, mutable=False,
                   doc="The `Runner` object to execute.")
        params.add('formatter', vtype=Formatter, required=False, mutable=True,
                   doc="The `Formatter` object for displaying test case progress and results.")
        params.add('controllers', vtype=Controller, array=True, mutable=False,
                   doc="`Controller` object(s) that dictate if the Runner should run.")

        params.add('progress_interval', default=5, vtype=(float, int), mutable=False,
                   doc="Interval, in seconds, between progress updates.")

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

        self.__progress_interval = self.getParam('progress_interval')
        self.__progress_time = None
        self.__create_time = None
        self.__start_time = None
        self.__execute_time = None

        self.setProgress(TestCase.Progress.WAITING, time.time())

    def redirectOutput(self):
        return RedirectOutput()

    def setProgress(self, progress, t):
        if progress == TestCase.Progress.WAITING:
            self.__create_time = t
            self.__progress_time = t
        elif progress == TestCase.Progress.RUNNING:
            self.__start_time = t
            self.__progress_time = t
        elif progress == TestCase.Progress.FINISHED:
            self.__execute_time = t - self.__start_time if self.__start_time else 0

        self.__progress = progress

    def getProgress(self):
        return self.__progress


    def getState(self):
        return self.__state


    def execute(self):
        """

        """
        results = dict()

        state, rcode, stdout, stderr = self.executeObject(self._runner)
        results[self._runner.name()] = (state, rcode, stdout, stderr)
        if state.level > 0:
            return state, results

        for obj in self._differs:
            d_state, d_rcode, d_stdout, d_stderr = self.executeObject(obj, rcode, stdout, stderr)
            results[obj.name()] = (d_state, d_rcode, d_stdout, d_stderr)
            if d_state.level > state.level:
                state = d_state

        return state, results

    def executeObject(self, obj, *args, **kwargs):

        # Reset the state of supplied "obj". The status of the object will be checked after all
        # calls that could lead the object to produce an error. If an error is detected a FATAL
        # state is returned.
        with self.redirectOutput() as out:
            try:
                obj.reset() # clear log counts of the object to be passed to the Controller
            except Exception as ex:
                #self.exception("An unexpected exception occurred during the reset call of the {} object in preparation for calling the {} controller.\n{}", obj.name(), type(self._controller))
                return TestCase.Result.FATAL, 1, out.stdout, out.stderr

        # Loop through each `Controller` object
        for controller in self._controllers:

            # Execute the `Controller`
            with self.redirectOutput() as out:
                try:
                    controller.reset() # clear log counts
                    controller.execute(obj)

                    # Stop if an error is logged on the Controller object
                    if controller.status():
                        self.error("An error occurred, on the controller, during execution of the Controller '{}' with '{}' object.", type(controller), obj.name())
                        return TestCase.Result.FATAL, 1, out.stdout, out.stderr

                    # Stop if an error is logged on the object, due to execution of Controller
                    if obj.status():
                        self.error("An error occurred, on the object, during execution of the Controller '{}' with '{}' object.", type(controller), obj.name())
                        return TestCase.Result.FATAL, 1, out.stdout, out.stderr

                    # Skip it...maybe
                    if not controller.isRunnable():
                        return TestCase.Result.SKIP, 0, out.stdout, out.stderr

                except Exception as ex:
                    self.error("An exception occurred during execution of the Controller '{}' with '{}' object.", type(controller), obj.name())
                    return TestCase.Result.FATAL, 1, out.stdout, out.stderr

        # Execute the object
        with self.redirectOutput() as out:
            try:
                rcode = obj.execute(*args, **kwargs)

                # Errors on object result in failure
                if obj.status():
                    self.error("An error occurred during execution of '{}' object.", obj.name())
                    return TestCase.Result.ERROR, 1, out.stdout, out.stderr

            except Exception as ex:
                self.exception("An exception occurred during execution of '{}' object.", obj.name())
                return TestCase.Result.EXCEPTION, 1, out.stdout, out.stderr


        return TestCase.Result.PASS, rcode, out.stdout, out.stderr

    def setState(self, state):
        self.__state = state

    def setResult(self, result):
        self.__results = result

    def reportResult(self):
        self._printState(self._runner, self.__state)

        r_state, r_rcode, r_out, r_err = self.__results.get(self._runner.name())
        self._printResult(self._runner, r_state, r_rcode, r_out, r_err)

        for obj in [d for d in self._differs if d.name() in self.__results]:
            d_state, d_rcode, d_out, d_err = self.__results.get(obj.name())
            self._printState(obj, d_state)
            self._printResult(obj, d_state, d_rcode, d_out, d_err)

    def reportProgress(self):
        progress = self.getProgress()
        if progress == TestCase.Progress.RUNNING:
            current = time.time()
            if (current - self.__progress_time) > self.__progress_interval:
                self._printState(self._runner, progress)
                self.__progress_time = current

    def _printState(self, obj, state):
        """
        """
        if state == TestCase.Progress.RUNNING:
            duration = time.time() - self.__start_time
        else:
            duration = self.__execute_time

        if obj is self._runner:
            txt = self._formatter.formatRunnerState(obj, state, duration=duration)
        else:
            txt = self._formatter.formatDifferState(obj, state, duration=duration)
        if txt:
            print(txt)

    def _printResult(self, obj, state, rcode, out, err):
        """
        """
        if obj is self._runner:
            txt = self._formatter.formatRunnerResult(obj, state, rcode, out, err)
        else:
            txt = self._formatter.formatDifferResult(obj, state, rcode, out, err)
        if txt:
            print(txt)
