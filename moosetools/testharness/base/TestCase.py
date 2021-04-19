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

class RedirectOutput(object):
    """

    TODO: pass in io.StringIO()

    """
    class SysRedirect(object):
        def __init__(self, sysout, out):
            self._sysout = sysout
            self._out = out

        def write(self, message):
            if threading.main_thread().ident == threading.current_thread().ident:
                self._sysout.write(message)
            else:
                self._out.write(message)

        def flush(self):
            if threading.main_thread().ident == threading.current_thread().ident:
                self._sysout.flush()

    def __init__(self, stdout, stderr):
        #assert type
        self._stdout = stdout
        self._stderr = stderr

        self._sys_stdout = sys.stdout
        self._sys_stderr = sys.stderr

    @property
    def stdout(self):
        return self._stdout.getvalue()

    @property
    def stderr(self):
        return self._stdrr.getvalue()

    def __enter__(self):
        sys.stdout = RedirectOutput.SysRedirect(self._sys_stdout, self._stdout)
        sys.stderr = RedirectOutput.SysRedirect(self._sys_stderr, self._stderr)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        #self.stdout = sys.stdout.out
        #self.stderr = sys.stderr.out

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
        params.add('_job_id', vtype=int, private=True)

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

    def redirectOutput(self, stdout, stderr):
        return RedirectOutput(stdout, stderr)

    def setProgress(self, progress):
        self.__progress = progress

    def getProgress(self):
        return self.__progress

    def execute(self):
        self.setProgress(TestCase.Progress.RUNNING)

        """
        TODO:
        I don't think we need a TestSpec class, as below, but just different methods that main
        function uses...I really would like the running of the TestCase to be separated from the hit
        file so that they can be created programattically. But, if using hit it should also be part
        of the execute. Which brings me back to the testspecification idea that can encapsulate it.



        - Loop through files and create TestSpecification for each file, but do nothing that could cause an error
        - Execute the TestSpecification:
          1. Parse the file (The TestSpecification should be the warehouse and require a factory)
          2. Create TestCase for each block, pass in the Runner and Tester objects
          3. Run the test cases

        TestRunner -> TestSpecification
        TestExecutioner should operate on actual TestCases
        TestSpecificationExectuioner should use a factory to parse the input then pass along to
        base class method.

        - The TestSpecification should parse the file (report errors if needed) and return the
          constructed TestCases. It should loop through the TestCases one after another...

        - Create TestSpecification.createRunner, createTester methods so they can be mocked.
        - Annotate the methods that are used off process, the entire TestCase should be off-process,
          these methods could assert if not used as such. Use @subprocess decorator???

        TestExecutioner::execute():
        for tc in testcases:
          tc.execute()


        TestCase::execute(objs)
        for obj in objs:
          self.executeObject(obj)

        TestCase::executeObject(obj)



        """



        self.__start_time.value = time.time()

        # Setup streams
        r_stdout, r_stderr = io.StringIO(), io.StringIO()
        #s = sys.stdout
        #r = SysRedirect(sys.stdout)
        #sys.stdout = r

        # Runner.initialize
        # Determines if the runner can actually run, see Runner.initialize for details
        try:
            with self.redirectOutput(r_stdout, r_stderr):
                self._runner.reset() # clear log counts
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
        try:
            with self.redirectOutput(r_stdout, r_stderr):
                self._runner.reset() # clear log counts
                returncode = self._runner.execute()
        except Exception as ex:
            self.exception("Exception occurred during execution of {} object.", self._runner.name())
            return {self._runner.name() : (TestCase.Result.EXCEPTION, out)}

        # If an error occurs then report it and exit
        if self._runner.status():
            self.error("The Runner object logged an error during execution.")
            return {self._runner.name() : (TestCase.Result.ERROR, out)}



        # TODO: Create context manager in constructor so that stderr, stdout can go to the same
        # object. Then provide nice access from to the io.StrigIO via stderr, stdout properties



        #sys.stdout = s
        #print(r.out.getvalue())

        # Tester.execute

        #if self._runner.status(logging.ERROR, logging.CRITICAL):
        #    return TestCase.Result.FAIL, self._runner.getStream()

        # Retore stream


        #out = dict()
        #out[self._runner.name()] = (TestCase.Result.PASS, stdout)

        #print(out)

        return TestCase.Result.PASS, r_stdout.getvalue().rstrip('\n')

    def doneCallback(self, future):
        self.setProgress(TestCase.Progress.FINISHED)
        self.__results = future.result()

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
