import os
import sys
import io
import enum
import time
import uuid
import logging
import collections
import multiprocessing
import threading
import textwrap
from moosetools import mooseutils
from moosetools.base import MooseObject
#from .MooseTestController import MooseTestController
from .Runner import Runner
from .Differ import Differ
from .Formatter import Formatter



class State(enum.Enum):
    def __new__(cls, value, exitcode, display, color):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.exitcode = exitcode
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
            return threading.main_thread().ident == threading.current_thread().ident
            #return multiprocessing.parent_process() is None

        def write(self, message):
            if self.is_main:
                self._sysout.write(message)
            else:
                self._out[threading.current_thread().ident].write(message)

        def flush(self):
            if self.is_main:
                self._sysout.flush()

    def __init__(self):
        #assert type
        self._stdout = collections.defaultdict(io.StringIO)
        self._stderr = collections.defaultdict(io.StringIO)

        self._sys_stdout = sys.stdout
        self._sys_stderr = sys.stderr

        self._logging_handlers = list()

    @property
    def stdout(self):
        #return sys.stdout.getvalue()
        return self._stdout[threading.current_thread().ident].getvalue()

    @property
    def stderr(self):
        #return sys.stderr.getvalue()
        return self._stderr[threading.current_thread().ident].getvalue()

    def __enter__(self):
        self._logging_handlers = list()
        #pass
        #print("ENTER")
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
        #pass
        sys.stdout = self._sys_stdout
        sys.stderr = self._sys_stderr

        for h, f in self._logging_handlers:
            h.setStream(self._sys_stderr)
            h.setFormatter(f)

        #
        #return self


class TestCase(MooseObject):
    class Progress(State):
        WAITING  = (1, 0, 'WAITING', ('grey_82',))
        RUNNING  = (2, 0, 'RUNNING', ('dodger_blue_3',))
        FINISHED = (3, 0, 'FINISHED', ('white',))
        CLOSED   = (4, 0, 'CLOSED', ('white',))

    class Result(State):
        SKIP      = (11, 0, 'SKIP', ('cyan_1',))
        PASS      = (12, 0, 'OK', ('green_1',))
        ERROR     = (13, 1, 'ERROR', ('red_1',))
        EXCEPTION = (14, 1, 'EXCEPTION', ('magenta_1',))
        FATAL     = (15, 1, 'FATAL', ('white', 'red_1')) # internal error (see, run.py)

    @staticmethod
    def validParams():
        params = MooseObject.validParams()

        params.add('runner', vtype=Runner, required=True, mutable=False,
                   doc="The 'Runner' object to execute.")
        params.add('formatter', vtype=Formatter, required=True, mutable=False,
                   doc="The 'Formatter object for displaying test case progress and results.")

        params.add('progress_interval', default=10, vtype=(float, int), private=True)


        params.add('_unique_id', vtype=uuid.UUID, mutable=True, private=True)

        # Don't add anything here, these don't get set from anywhere

        return params

    def __init__(self, *args, **kwargs):
        kwargs['_unique_id'] = uuid.uuid4()
        MooseObject.__init__(self, *args, **kwargs)



        #self._controller = self.getParam('controller') or MooseTestController()
        self._runner = self.getParam('runner')
        self._differs = self._runner.getParam('differs')
        self._formatter = self.getParam('formatter')
        self.parameters().set('name', self._runner.name())

        self.__results = None
        #self.__result = None
        self.__progress = TestCase.Progress.WAITING

        self.__progress_time = time.time()
        self.__progress_interval = self.getParam('progress_interval')

        self.__create_time = time.time()
        self.__start_time = None
        self.__duration = None

        #self.setProgress(TestCase.Progress.WAITING)

    def redirectOutput(self):
        return RedirectOutput()

    def setProgress(self, progress):
        self.__progress = progress

    def getProgress(self):
        return self.__progress

    def getDuration(self):
        if (self.__duration is None) and (self.__start_time is None):
            return time.time() - self.__start_time
        elif (self.__duration is None):
            return time.time() - self.__create_time
        return self.__duration

    def execute(self):
        #self.setProgress(TestCase.Progress.RUNNING)

        results = dict()

        self.__start_time = time.time()
        state, rcode, stdout, stderr = self.executeObject(self._runner)
        results[self._runner.name()] = (state, rcode, stdout, stderr)
        if (state == TestCase.Result.SKIP) or (state.exitcode > 0):
            return state, results

        #for obj in self._differs or []:
        #    d_state, d_rcode, d_stdout, d_stderr = self.executeObject(obj, returncode, out)
        #    results[obj.name()] = (d_state, d_rcode, d_stdout, d_stderr)
        #    if (d_state != TestCase.Result.SKIP) and (d_state.exitcode > 0):
        #        state = d_state

        return state, results

    def executeObject(self, obj, *args, **kwargs):

        """
        # Use Controller to determines if the runner can actually run
        try:
            with self.redirectOutput() as c_run_out:
                self._controller.reset() # clear log counts
                self._controller.execute(obj)
        except Exception as ex:
            with self.redirectOutput() as err_out:
                self._controller.exception("An unexpected exception occurred during execution of the controller ({}) with {} object.\n{}", type(self._controller), obj.name(), c_run_out.stdout)
            return TestCase.Result.FATAL, err_out.stdout, None

        # Stop if an error is logged on the Controller object
        if self._controller.status():
            with self.redirectOutput() as err_out:
                self._controller.error("An unexpected error was logged on the Controller '{}' during execution with the supplied '{}' object.\n{}", self._controller.name(), obj.name(), c_run_out.stdout)
            return TestCase.Result.FATAL, err_out.stdout, None

        # Stop if an error is logged on the Runner object, due to execution of Controller
        if obj.status():
            with self.redirectOutput() as err_out:
                obj.error("An unexpected error was logged on the supplied object '{}' during execution of the Controller '{}'.\n{}", obj.name(), self._controller.name(), c_run_out.stdout)
            return TestCase.Result.FATAL, err_out.stdout, None

        # Stop if the runner is unable to run...thanks Capt. obvious
        if not self._controller.isRunnable():
            return TestCase.Result.SKIP, c_run_out.stdout, None
        """

        #rcode = obj.execute(*args, **kwargs)
        #return TestCase.Result.Pass, rcode, '', ''


        try:
            with self.redirectOutput() as run_out:
                obj.reset() # clear log counts
                rcode = obj.execute(*args, **kwargs)
        except Exception as ex:
            with self.redirectOutput() as err_out:
                obj.exception("An exception occurred during execution of '{}' object.\n{}", obj.name(), run_out.stdout)
            return TestCase.Result.EXCEPTION, 1, err_out.stdout, err_out.stderr


        # If an error occurs then report it and exit
        if obj.status():
            with self.redirectOutput() as err_out:
                obj.error("An error was logged on the '{}' object during execution.\n{}", obj.name(), run_out.stdout)
            return TestCase.Result.ERROR, rcode, err_out.stdout, err_out.stderr

        return TestCase.Result.PASS, rcode, run_out.stdout, run_out.stderr

    def setState(self, state):
        self.__state = state

    def setResult(self, result):
        #self.setProgress(TestCase.Progress.FINISHED)
        #self.__state = state
        self.__results = result
        self.__duration = time.time() - self.__start_time
        #self._printResult()

    #def reportProgress(self):
    #    self._printProgress()

    def reportResult(self):

        #self.setProgress(TestCase.Progress.CLOSED)
        #state, out = self.__results
        self._printState(self._runner, self.__state)

        r_state, r_rcode, r_out, r_err = self.__results.get(self._runner.name())
        self._printResult(self._runner, r_state, r_rcode, r_out, r_err)

        #for obj in [d for d in self._differs if d.name() in out]:
        #    d_state, d_out = out.get(obj.name())
        #    self._printState(obj, d_state)
        #    if d_out:
        #        prefix = '{} '.format(mooseutils.color_text(obj.name(), *d_state.color))
        #        print(textwrap.indent(d_out.strip('\n'), prefix=prefix))

    def reportProgress(self):
        progress = self.getProgress()
        if progress == TestCase.Progress.RUNNING:
            current = time.time()
            if (current - self.__progress_time) > self.__progress_interval:
                self._printState(self._runner, progress)
                self.__progress_time = current

    # TODO:
    # _printDifferState
    # _printRunnerState
    def _printState(self, obj, state):
        """
        """
        print(self._formatter.formatState(obj, state, duration=self.getDuration()))


    def _printResult(self, obj, state, rcode, out, err):
        """
        """
        print(self._formatter.formatResult(obj, state, rcode, out, err), end='')
