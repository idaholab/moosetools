import os
import sys
import io
import enum
import time
import uuid
import logging
import multiprocessing
import threading
from moosetools import mooseutils
from moosetools.base import MooseObject
from .MooseTestController import MooseTestController
from .Runner import Runner

class State(enum.Enum):
    def __new__(cls, value, exitcode, display, color):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.exitcode = exitcode
        obj.display = display
        obj.color = color
        return obj


"""
class SysRedirect(object):
    def __init__(self):
        self.terminal = sys.stdout                  # To continue writing to terminal
        self.log={}                                 # A dictionary of file pointers for file logging

    def register(self,filename):                    # To start redirecting to filename
        ident = threading.currentThread().ident     # Get thread ident (thanks @michscoots)
        if ident in self.log:                       # If already in dictionary :
            self.log[ident].close()                 # Closing current file pointer
        self.log[ident] = open(filename, "a")       # Creating a new file pointed associated with thread id

    def write(self, message):
        self.terminal.write(message)                # Write in terminal (comment this line to remove terminal logging)
        ident = threading.current_thread().ident     # Get Thread id
        if ident in self.log:                       # Check if file pointer exists
            self.log[ident].write(message)          # write in file
        else:                                       # if no file pointer
            for ident in self.log:                  # write in all thread (this can be replaced by a Write in terminal)
                 self.log[ident].write(message)
    def flush(self):
            #this flush method is needed for python 3 compatibility.
            #this handles the flush command by doing nothing.
            #you might want to specify some extra behavior here.
            pass
"""

class RedirectOutput(object):
    """

    TODO: move to mooseutils, process/threading toggle

    """
    class SysRedirect(object):
        def __init__(self, sysout, out):
            self._sysout = sysout
            self._out = out

        @property
        def is_main(self):
            return threading.main_thread().ident == threading.current_thread().ident

        def write(self, message):
            if self.is_main:
                self._sysout.write(message)
            else:
                self._out.write(message)

        def flush(self):
            if self.is_main:
                self._sysout.flush()

    def __init__(self, stdout=None, stderr=None):
        #assert type
        self._stdout = stdout or io.StrigIO()
        self._stderr = stderr or io.StrigIO()

        self._sys_stdout = sys.stdout
        self._sys_stderr = sys.stderr

    @property
    def stdout(self):
        return self._stdout.getvalue().strip('\n')

    @property
    def stderr(self):
        return self._stdrr.getvalue().strip('\n')

    def __enter__(self):
        sys.stdout = RedirectOutput.SysRedirect(self._sys_stdout, self._stdout)
        sys.stderr = RedirectOutput.SysRedirect(self._sys_stderr, self._stderr)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        sys.stdout = self._sys_stdout
        sys.stderr = self._sys_stderr


class TestCase(MooseObject):
    class Progress(State):
        WAITING  = (1, 0, 'WAITING', ('grey_82',))
        RUNNING  = (2, 0, 'RUNNING', ('dodger_blue_3',))
        FINISHED = (3, 0, 'FINISHED', ('white',))

    class Result(State):
        SKIP      = (11, 0, 'SKIP', ('cyan_1',))
        PASS      = (12, 0, 'OK', ('green_1',))
        ERROR     = (14, 1, 'ERROR', ('red_1',))
        EXCEPTION = (15, 1, 'EXCEPTION', ('magenta_1',))
        FATAL     = (16, 1, 'FATAL', ('white', 'red_1')) # internal error (see, run.py)

    @staticmethod
    def validParams():
        params = MooseObject.validParams()
        params.add('controller', vtype=MooseTestController,
                   doc="The 'MooseTestController' used to determine if the TestCase members should execute.")
        params.add('runner', vtype=Runner, required=True,
                   doc="The 'Runner' object to execute.")
        params.add('_unique_id', vtype=uuid.UUID, mutable=True, private=True)

        # Don't add anything here, these don't get set from anywhere

        return params

    def __init__(self, *args, **kwargs):
        kwargs['_unique_id'] = uuid.uuid4()
        MooseObject.__init__(self, *args, **kwargs)
        self._controller = self.getParam('controller') or MooseTestController()
        self._runner = self.getParam('runner')
        self.__results = None
        self.__progress = None


        self.__running_report_time = None
        self.__running_report_interval = self._runner.getParam('output_progress_interval')
        self.__start_time = multiprocessing.Value('d', 0)

        self.setProgress(TestCase.Progress.WAITING)

    #def redirectOutput(self, stdout, stderr):
    #    return

    def setProgress(self, progress):
        self.__progress = progress

    def getProgress(self):
        return self.__progress

    def execute(self):
        self.setProgress(TestCase.Progress.RUNNING)
        #return TestCase.Result.PASS, 'WTF'


        self.__start_time.value = time.time()

        # Setup streams
        result_out = io.StringIO()
        redirect_output = RedirectOutput(result_out, result_out)
        #s = sys.stdout
        #r = SysRedirect(sys.stdout)
        #sys.stdout = r

        # Runner.initialize
        # Determines if the runner can actually run, see Runner.initialize for details
        """
        try:
            with redirect_output:
                self._controller.reset() # clear log counts
                self._controller.execute(self._runner)
        except Exception as ex:
            self.exception("Exception occurred during execution of the controller ({}) with {} object.", type(self._controller), self._runner.name())
            return TestCase.Result.EXCEPTION, out.stdout

        # Stop if the runner is unable to run...thanks Capt. obvious
        if not self._controller.status():
            return TestCase.Result.SKIP, out.stdout
        """


        # Stop if an error is logged on the Runner object
        #if self._runner.status():
        #    self.error("An error was logged during during initialization of {} object.", self._runner.name())
        #    return TestCase.Result.ERROR, out.stdout

        # If an error occurs then report it and exit
        #if self._runner.status():
        #    self.exception("An error was logged during during execution of {} object.", self._runner.name())
        #    return TestCase.Result.ERROR, out.stdout

        # Runner.execute
        try:
            with redirect_output:
                self._runner.reset() # clear log counts
                returncode = self._runner.execute()
        except Exception as ex:
            self.exception("Exception occurred during execution of {} object.", self._runner.name())
            return TestCase.Result.EXCEPTION, redirect_output.stdout

        # If an error occurs then report it and exit
        if self._runner.status():
            self.error("The Runner object logged an error during execution.")
            return TestCase.Result.ERROR, redirect_output.stdout

        return TestCase.Result.PASS, redirect_output.stdout

    #def doneCallback(self, future):
    #    self.setProgress(TestCase.Progress.FINISHED)
    #    self.__results = future.result()

    def setResult(self, result):
        self.setProgress(TestCase.Progress.FINISHED)
        self.__results = result


    def report(self):
        progress = self.getProgress()
        if progress != TestCase.Progress.FINISHED:
            self._printProgress()

        elif progress == TestCase.Progress.FINISHED:
            self._printResult()




    def _printResult(self):
        r_state, r_out = self.__results#.get(self._runner.name())
        self._printState(self._runner, r_state)
        print(r_out)

        #print('SHOW RESULTS HERE')
        pass #self._printProgress()

    def _printProgress(self):
        progress = self.getProgress()
        if progress == TestCase.Progress.RUNNING:
            if self.__running_report_time is None:
                self.__running_report_time = self.__start_time.value
            current = time.time()
            if (current - self.__running_report_time) > self.__running_report_interval:
                self._printState(self._runner, self.getProgress(), show_time=True)
                self.__running_report_time = current

    def _printState(self, obj, state, show_time=False):
        """
        """

        pcolor = state.color
        name = obj.name()
        state = state.display
        tinfo = '[{:.1f}s] '.format(time.time() - self.__start_time.value) if show_time else ''
        width = 100 - len(name) - len(state) - len(tinfo)
        dots = '.'*width
        state = mooseutils.color_text(state, *pcolor)
        name = mooseutils.color_text(name, *pcolor)
        kwargs = dict(name=name, dots=dots, tinfo=tinfo, state=state)
        frmt = '{name}{dots}{tinfo}{state}'

        msg = frmt.format(**kwargs)
        print(msg)

    #def update(self):
    #    if getState()

    #    return None#'update'

    #def results(self):
    #    self.setState(State.CLOSED)
    #    return self.__results
