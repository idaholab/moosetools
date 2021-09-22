#* This file is part of MOOSETOOLS repository
#* https://www.github.com/idaholab/moosetools
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moosetools/blob/main/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html

import time
from moosetools.core import MooseObject
from .TestCase import TestCase, RedirectLogs


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
        params.add('progress_interval',
                   default=10.,
                   vtype=(int, float),
                   mutable=False,
                   doc="Number of seconds in between progress updates for a test case.")

        params.add('min_print_progress',
                   vtype=TestCase.Result,
                   default=TestCase.Result.SKIP,
                   doc="The minimum `TestCase.Result` level necessary for a finished `TestCase` object progress to be displayed.")

        params.add('min_print_result',
                   vtype=TestCase.Result,
                   default=TestCase.Result.DIFF,
                   doc="The minimum `TestCase.Result` level necessary for a finished `TestCase` object result to be displayed.")

        params.add('min_print_differ_progress',
                   default=TestCase.Result.TIMEOUT,
                   vtype=TestCase.Result,
                   doc="The minimum `TestCase.Result` necessary for the `TestCase` to show `Differ` progress. If `TestCase` and all the `Differ` objects have a result level less than this level then `Differ` progress information will not be displayed.")

        params.add('min_print_differ_result',
                   default=TestCase.Result.DIFF,
                   vtype=TestCase.Result,
                   doc="The minimum `TestCase.Result` necessary for the `TestCase` to show `Differ` result. If `TestCase` and all the `Differ` objects have a result level less than this level then the `Differ` result information will not be displayed.")

        return params

    @staticmethod
    def validCommandLineArguments(parser, params):
        """
        Add command-line arguments to the `argparse.ArgumentParser` in *parser*.

        The *params* is the `parameters.InputParameter` object for an instance, see
        `moosetest.base.TestHarness` for use.
        """
        parser.add_argument('--verbose',
                            action='store_true',
                            help=("Enable complete output, this will override necessary flags to "
                                  "ensure all output is shown."))

        params.toArgs(parser, 'min_print_result', 'min_print_progress', 'min_print_differ_progress', 'min_print_differ_result')

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('name', self.__class__.__name__)
        MooseObject.__init__(self, *args, **kwargs)
        self.__progress_time = dict()
        self.__progress_interval = self.getParam('progress_interval')

        if self.getParam('min_print_result').level < self.getParam('min_print_progress').level:
            msg = "The 'min_print_result' ({}) level must be greater than or equal to 'min_print_progress' ({})."
            self.error(msg.format(self.getParam('min_print_result'), self.getParam('min_print_progress')))


    def _setup(self, args):
        """
        Function for applying the command line arguments in *args* to the object.
        """
        self.parameters().fromArgs(args, 'min_print_result', 'min_print_progress',
                                   'min_print_differ_progress', 'min_print_differ_result')

        if args.verbose:
            self.parameters().setValue('min_print_progress', TestCase.Result.REMOVE)
            self.parameters().setValue('min_print_result', TestCase.Result.REMOVE)
            self.parameters().setValue('min_print_differ_progress', TestCase.Result.REMOVE)
            self.parameters().setValue('min_print_differ_result', TestCase.Result.REMOVE)

    def formatRunnerProgress(self, **kwargs):
        raise NotImplementedError("The 'formatRunnerProgress' method must be overridden.")

    def formatRunnerResult(self, **kwargs):
        raise NotImplementedError("The 'formatRunnerResult' method must be overridden.")

    def formatDifferProgress(self, **kwargs):
        raise NotImplementedError("The 'formatDifferProgress' method must be overridden.")

    def formatDifferResult(self, **kwargs):
        raise NotImplementedError("The 'formatDifferResult' method must be overridden.")

    def formatComplete(self, complete, **kwargs):
        raise NotImplementedError("The 'formatComplete' method must be overridden.")

    def reportComplete(self, complete, start_time):
        """
        Print information at conclusion of the test case execution.

        The completed `TestCase` objects are provided in the `list` *complete* along with the
        starting time (in seconds) of the run in *start_time*.

        See `moosetools.run` for use.
        """
        print(self.formatComplete(complete, duration=time.perf_counter() - start_time))

    def reportProgress(self, tc_obj):
        """
        Print the progress of the `TestCase` in *tc_obj*.

        See `moosetools.run` for use.
        """
        with RedirectLogs(self) as out:
            self.reset()
            if tc_obj.progress is None:
                self.critical("The progress has not been set via the `setProgress` method.")

            if self.status():
                tc_obj.setProgress(TestCase.Progress.FINISHED)
                tc_obj.setState(TestCase.Result.FATAL)
                tc_obj.setResults({
                    tc_obj.runner.name():
                    TestCase.Data(TestCase.Result.FATAL, None, out.text, None)
                })

        if tc_obj.running:
            current = time.perf_counter()
            progress_time = self.__progress_time.get(tc_obj.unique_id, tc_obj.start_time)
            if current - progress_time >= self.__progress_interval:
                self.__progress_time[tc_obj.unique_id] = current
                self._printProgress(tc_obj, tc_obj.runner, TestCase.Data(state=tc_obj.progress))

    def reportResults(self, tc_obj):
        """
        Print the results of the `TestCase` in *tc_obj*.

        See `moosetools.run` for use.
        """
        # Attempt to avoid unexpected calls to this function, these should not be hit unless
        # something has gone wrong.
        with RedirectLogs(self) as out:
            self.reset()
            if tc_obj.state is None:
                self.critical("The state has not been set via the `setState` method.")

            elif tc_obj.results is None:
                self.critical("The results have not been set via the `setResults` method.")

            elif tc_obj.progress != TestCase.Progress.FINISHED:
                self.critical("The execution has not finished, so results cannot be reported.")

            if self.status():
                tc_obj.setProgress(TestCase.Progress.FINISHED)
                tc_obj.setState(TestCase.Result.FATAL)
                tc_obj.setResults({
                    tc_obj.runner.name():
                    TestCase.Data(TestCase.Result.FATAL, None, out.text,  None)
                })

        # Report Runner results
        r_data = tc_obj.results.get(tc_obj.runner.name())
        if tc_obj.state.level >= self.getParam('min_print_progress').level:
            self._printProgress(tc_obj, tc_obj.runner, r_data)
        if tc_obj.state.level >= self.getParam('min_print_result').level:
            self._printResult(tc_obj, tc_obj.runner, r_data)

        # Report Differ results
        min_progress_level = self.getParam('min_print_differ_progress').level
        min_result_level = self.getParam('min_print_differ_result').level
        differ_and_data = [(d, tc_obj.results.get(d.name())) for d in tc_obj.differs if d.name() in tc_obj.results]
        if differ_and_data:
            differ_level = max(d_data[1].state.level for d_data in differ_and_data)
            for differ, d_data in differ_and_data:
                if (tc_obj.state.level >= min_progress_level) and (differ_level >= min_progress_level):
                    self._printProgress(tc_obj, differ, d_data)
                if (tc_obj.state.level >= min_result_level) and (differ_level >= min_result_level):
                    self._printResult(tc_obj, differ, d_data)


    def _printProgress(self, tc_obj, obj, data):
        """
        Helper to prepare information for passing to the Formatter state printing methods.
        """
        kwargs = dict()
        kwargs['name'] = obj.name()
        kwargs['reasons'] = data.reasons
        kwargs['duration'] = tc_obj.time
        kwargs['percent'] = TestCase.__FINISHED__ / TestCase.__TOTAL__ * 100

        if obj is tc_obj.runner:
            kwargs['state'] = tc_obj.state or data.state
            txt = self.formatRunnerProgress(**kwargs)
        else:
            kwargs['state'] = data.state
            txt = self.formatDifferProgress(**kwargs)
        if txt:
            print(txt)

    def _printResult(self, tc_obj, obj, data):
        """
        Helper to prepare information for passing to the Formatter result printing methods.
        """
        kwargs = dict()
        kwargs['name'] = obj.name()
        kwargs['reasons'] = data.reasons
        kwargs['returncode'] = data.returncode
        kwargs['duration'] = tc_obj.time
        kwargs['percent'] = TestCase.__FINISHED__ / TestCase.__TOTAL__ * 100
        kwargs['prefix'] = ''

        kwargs['text'] = data.text

        if obj is tc_obj.runner:
            kwargs['state'] = tc_obj.state or data.state
            txt = self.formatRunnerResult(**kwargs)
        else:
            kwargs['state'] = data.state
            txt = self.formatDifferResult(**kwargs)

        if txt:
            print(txt)
