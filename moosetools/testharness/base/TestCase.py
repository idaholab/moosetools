import os
import sys
import io
import enum
import time
import logging
import multiprocessing
import threading
from moosetools import mooseutils
from moosetools.base import MooseObject
from ..runners.Runner import Runner

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

class SysRedirect(object):
    def __init__(self):
        self.stdout = sys.stdout
        self.out = io.StringIO()

    def write(self, message):
        if threading.main_thread().ident == threading.current_thread().ident:
            self.stdout.write(message)
        else:
            self.out.write(message)

    def flush(self):
        self.stdout.flush()


class RedirectOutput(object):
    """

    """
    #def __init__(self):
    #    self._sys_stdout = sys.stdout
    #    self._sys_stderr = sys.stderr

    def __enter__(self):
        if threading.current_thread().native_id != threading.main_thread().native_id:
            self._sys_stdout = sys.stdout
            self._sys_stderr = sys.stdout
            self._sys_stdout.flush()
            self._sys_stderr.flush()
            sys.stdout = self.stdout = io.StringIO()
            sys.stderr = self.stderr = io.StringIO()

    def __exit__(self, exc_type, exc_value, traceback):
        if threading.current_thread().native_id != threading.main_thread().native_id:
            self.stdout.flush(); self.stderr.flush()
            sys.stdout = self._sys_stdout
            sys.stderr = self._sys_stderr


class TestCase(MooseObject):
    class Progress(State):
        WAITING  = (1, 0, 'WAITING', 'grey_82')
        RUNNING  = (2, 0, 'RUNNING', 'dodger_blue_3')
        FINISHED = (3, 0, 'FINISHED', 'white')

    class Result(State):
        SKIP      = (11, 0, 'SKIP', 'cyan')
        PASS      = (12, 0, 'OK', 'green')
        #FAIL      = (13, 1, 'FAIL', 'red')
        ERROR     = (14, 1, 'ERROR', 'red')
        EXCEPTION = (15, 1, 'EXCEPTION', 'magenta')

    @staticmethod
    def validParams():
        params = MooseObject.validParams()
        params.add('runner', vtype=Runner, required=True,
                   doc="The 'Runner' object to execute.")

        # Don't add anything here, these don't get set from anywhere

        # Runner parameters
        #r_params =





        return params

    def __init__(self, *args, **kwargs):
        MooseObject.__init__(self, *args, **kwargs)
        self._runner = self.getParam('runner')
        self.__results = None
        self.__progress = None



        self.__running_report_time = None
        self.__running_report_interval = self._runner.getParam('output_progress_interval')

        self.__start_time = multiprocessing.Value('d', 0)


        self.setProgress(TestCase.Progress.WAITING)

    def redirectOutput(self):
        return RedirectOutput()

    def setProgress(self, progress):
        self.__progress = progress

    def getProgress(self):
        return self.__progress

    def execute(self):
        self.setProgress(TestCase.Progress.RUNNING)

        self.__start_time.value = time.time()

        # Setup streams
        s = sys.stdout
        r = SysRedirect()
        sys.stdout = r

        # Runner.initialize
        # Determines if the runner can actually run, see Runner.initialize for details
        self._runner.reset() # clear log counts
        try:
            #with self.redirectOutput() as out:
            self._runner.initialize()
        except Exception as ex:
            self.exception("Exception occurred during initialization of {} object.", self._runner.name())
            return {self._runner.name() : (TestCase.Result.EXCEPTION, out)}

        # Stop if the runner is unable to run...thanks Capt. obvious
        if not self._runner.isRunnable():
            return {self._runner.name() : (TestCase.Result.SKIP, out)}

        # Stop if an error is logged on the Runner object
        if self._runner.status():
            self.error("An error was logged during during initialization of {} object.", runner.name())
            return {self._runner.name() : (TestCase.Result.ERROR, out)}

        # If an error occurs then report it and exit
        if self._runner.status():
            self.exception("An error was logged during during execution of {} object.", runner.name())
            return {self._runner.name() : (TestCase.Result.ERROR, out)}

        # Runner.execute
        self._runner.reset() # clear log counts
        try:
            #with self.redirectOutput() as out:
            returncode, stdout, stderr = self._runner.execute()
        except Exception as ex:
            self.exception("Exception occurred during execution of {} object.", self._runner.name())
            return {self._runner.name() : (TestCase.Result.EXCEPTION, out)}

        # If an error occurs then report it and exit
        if self._runner.status():
            self.error("The Runner object logged an error during execution.")
            return {self._runner.name() : (TestCase.Result.ERROR, out)}

        sys.stdout = s
        print(r.out.getvalue())

        # Tester.execute

        #if self._runner.status(logging.ERROR, logging.CRITICAL):
        #    return TestCase.Result.FAIL, self._runner.getStream()

        # Retore stream


        out = dict()
        out[self._runner.name()] = (TestCase.Result.PASS, stdout)



        return out

    def doneCallback(self, future):
        self.setProgress(TestCase.Progress.FINISHED)
        self.__results = future.result()

    def report(self):
        progress = self.getProgress()
        if progress != TestCase.Progress.FINISHED:
            self._printProgress()

        elif progress == TestCase.Progress.FINISHED:
            self._printResult()




    def _printResult(self):

        r_state, r_out = self.__results.get(self._runner.name())
        self._printState(self._runner, r_state)


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
        state = mooseutils.color_text(state, pcolor)
        name = mooseutils.color_text(name, pcolor)
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
