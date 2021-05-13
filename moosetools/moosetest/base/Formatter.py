import time
from moosetools.base import MooseObject
from .TestCase import TestCase

class Formatter(MooseObject):
    """
    Base class for defining how the progress and results are presented during the execution of test.

    TODO: Document difference between Runner/Differ state and results as well as kwargs passed from Tc_Obj


    Refer to `moosetest.formatters.BasicFormatter` for an example implementation.

    See `moosetest.run` and `moosetest.base.TestCase` for details regarding the use of this object.
    """
    @staticmethod
    def validParams():
        params = MooseObject.validParams()
        params.add('progress_interval', default=10., vtype=float, mutable=False,
                   doc="Number of seconds in between progress updates for a test case.")
        return params

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('name', self.__class__.__name__)
        MooseObject.__init__(self, *args, **kwargs)
        self.__progress_time = time.time() # time of last progress report
        self.__progress_interval = self.getParam('progress_interval')

    @property
    def time(self):
        """
        Return the time since the last progress report.
        """
        return time.time() - self.__progress_time

    def formatRunnerState(self, **kwargs):
        raise NotImplementedError("The 'formatRunnerState' method must be overridden.")

    def formatRunnerResult(self, **kwargs):
        raise NotImplementedError("The 'formatRunnerResult' method must be overridden.")

    def formatDifferState(self, **kwargs):
       raise NotImplementedError("The 'formatDifferState' method must be overridden.")

    def formatDifferResult(self, **kwargs):
       raise NotImplementedError("The 'formatDifferResult' method must be overridden.")

    def formatComplete(self, complete, **kwargs):
        raise NotImplementedError("The 'formatComplete' method must be overridden.")

    def reportProgress(self, tc_obj):
        """
        Print the results of the `TestCase` in *tc_obj*.

        See `moosetools.run` for use.
        """
        if (time.time() - self.__progress_time) > self.__progress_interval:

            if tc_obj.progress is None:
                with TestCase.RedirectOutput() as out:
                    tc_obj.critical("The progress has not been set via the `setProgress` method.")
                tc_obj.setProgress(TestCase.Progress.FINISHED)
                tc_obj.setState(TestCase.Result.FATAL)
                tc_obj.setResults({tc_obj.runner.name():TestCase.Data(TestCase.Result.FATAL, None, out.stdout, out.stderr, None)})

            self._printState(tc_obj, tc_obj.runner, tc_obj.progress, None)
            self.__progress_time = time.time()

    def reportResult(self, tc_obj):
        """
        Print the results of the `TestCase` in *tc_obj*.

        See `moosetools.run` for use.
        """
        # Attempt to avoid unexpected calls to this function, these should not be hit unless
        # something has gone wrong.
        if tc_obj.state is None:
            with TestCase.RedirectOutput() as out:
                tc_obj.critical("The state has not been set via the `setState` method.")
            tc_obj.setProgress(TestCase.Progress.FINISHED)
            tc_obj.setState(TestCase.Result.FATAL)
            tc_obj.setResults({tc_obj.runner.name():TestCase.Data(TestCase.Result.FATAL, None, out.stdout, out.stderr, None)})

        elif tc_obj.results is None:
            with TestCase.RedirectOutput() as out:
                tc_obj.critical("The results have not been set via the `setResults` method.")
            tc_obj.setProgress(TestCase.Progress.FINISHED)
            tc_obj.setState(TestCase.Result.FATAL)
            tc_obj.setResults({self._runner.name():TestCase.Data(TestCase.Result.FATAL, None, out.stdout, out.stderr, None)})

        elif tc_obj.progress != TestCase.Progress.FINISHED:
            with TestCase.RedirectOutput() as out:
                tc_obj.critical("The execution has not finished, so results cannot be reported.")
            tc_obj.setProgress(TestCase.Progress.FINISHED)
            tc_obj.setState(TestCase.Result.FATAL)
            tc_obj.setResults({tc_obj.runner.name():TestCase.Data(TestCase.Result.FATAL, None, out.stdout, out.stderr, None)})

        # Report Runner results
        r_data = tc_obj.results.get(tc_obj.runner.name())
        self._printState(tc_obj, tc_obj.runner, tc_obj.state, r_data.reasons)
        self._printResult(tc_obj, tc_obj.runner, r_data)

        # Report Differ results
        for differ in [d for d in tc_obj.differs if d.name() in tc_obj.results]:
            d_data = tc_obj.results.get(differ.name())
            self._printState(tc_obj, differ, d_data.state, d_data.reasons)
            self._printResult(tc_obj, differ, d_data)

    def _printState(self, tc_obj, obj, state, reasons):
        """
        Helper to prepare information for passing to the Formatter state printing methods.
        """
        #if state == TestCase.Progress.RUNNING:
        #    duration = time.time() - self.__start_time
        #else:
        #    duration = self.__execute_time

        # Documented in `moosetools.base.Formatter`
        kwargs = dict()
        kwargs['name'] = obj.name()
        kwargs['object'] = obj
        kwargs['state'] = state
        kwargs['reasons'] = reasons
        kwargs['duration'] = tc_obj.time
        kwargs['percent'] = TestCase.__FINISHED__ / TestCase.__TOTAL__ * 100

        if obj is tc_obj.runner:
            txt = self.formatRunnerState(**kwargs)
        else:
            txt = self.formatDifferState(**kwargs)
        if txt:
            print(txt)

    def _printResult(self, tc_obj, obj, data):
        """
        Helper to prepare information for passing to the Formatter result printing methods.
        """
        kwargs = dict()

        # Documented in `moosetools.base.Formatter`
        kwargs['name'] = obj.name()
        kwargs['object'] = obj
        kwargs['state'] = data.state
        kwargs['reasons'] = data.reasons
        kwargs['returncode'] = data.returncode
        kwargs['duration'] = tc_obj.time#self.__execute_time
        kwargs['percent'] = TestCase.__FINISHED__ / TestCase.__TOTAL__ * 100

        kwargs['stdout'] = data.stdout
        kwargs['stderr'] = data.stderr

        if obj is tc_obj.runner:
            txt = self.formatRunnerResult(**kwargs)
        else:
            txt = self.formatDifferResult(**kwargs)
        if txt:
            print(txt)
