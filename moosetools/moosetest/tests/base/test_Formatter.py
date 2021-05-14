#!/usr/bin/env python3
import os
import sys
import io
import logging
import unittest
import time
from unittest import mock
from moosetools.parameters import InputParameters
from moosetools.base import MooseException
from moosetools import moosetest
from moosetools.moosetest.base import make_runner, Runner, make_differ, Differ
from moosetools.moosetest.base import Controller, Formatter, TestCase, State, RedirectOutput

# I do not want the tests directory to be packages with __init__.py, so load from file
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from _helpers import TestController, TestRunner, TestDiffer

class TestFormatter(unittest.TestCase):
    def testDefault(self):

        f = moosetest.base.Formatter()
        self.assertEqual(f.name(), 'Formatter')

        methods = ['formatRunnerState', 'formatRunnerResult', 'formatDifferState', 'formatDifferResult']
        for method in methods:
            with self.assertRaises(NotImplementedError) as ex:
                getattr(f, method)()
            self.assertIn(f"The '{method}' method must be overridden.", str(ex.exception))

        with self.assertRaises(NotImplementedError) as ex:
            f.formatComplete(None)
        self.assertIn(f"The 'formatComplete' method must be overridden.", str(ex.exception))

    @mock.patch("moosetools.moosetest.base.Formatter._printResult")
    @mock.patch("moosetools.moosetest.base.Formatter._printState")
    def testReportResults(self, pstate, presult):

        # Runner
        fm = moosetest.base.Formatter(progress_interval=0)
        ct = TestController()
        rr = make_runner(TestRunner, [ct], name='r')
        tc = TestCase(runner=rr, controllers=(ct,))

        tc.setResults({'r':TestCase.Data(TestCase.Result.ERROR, None, 'out', 'err', None)})
        tc.setProgress(TestCase.Progress.FINISHED)
        tc.setState(TestCase.Result.PASS)
        fm.reportResults(tc)

        pstate.assert_called_with(tc, rr, tc.state, None)
        presult.assert_called_with(tc, rr, tc.results['r'])

        # Differ
        dr = make_differ(TestDiffer, [ct], name='d')
        rr = make_runner(TestRunner, [ct], differs=(dr,), name='r')
        tc = TestCase(runner=rr, controllers=(ct,))
        tc.setProgress(TestCase.Progress.FINISHED)
        tc.setState(TestCase.Result.PASS)
        tc.setResults({'r':TestCase.Data(TestCase.Result.ERROR, None, 'r_out', 'r_err', None),
                      'd':TestCase.Data(TestCase.Result.TIMEOUT, None, 'd_out', 'd_err', None)})

        fm.reportResults(tc)
        pstate.assert_called_with(tc, dr, tc.results['d'].state, None)
        presult.assert_called_with(tc, dr, tc.results['d'])

        # Errors
        ct = TestController()
        rr = make_runner(TestRunner, [ct], name='r')
        tc = TestCase(runner=rr, controllers=(ct,))
        fm.reportResults(tc)
        self.assertEqual(tc.progress, TestCase.Progress.FINISHED)
        self.assertEqual(tc.state, TestCase.Result.FATAL)
        r = tc.results
        self.assertEqual(r['r'].state, TestCase.Result.FATAL)
        self.assertEqual(r['r'].returncode, None)
        self.assertEqual(r['r'].stdout, '')
        self.assertIn("The state has not been set via the `setState` method.", r['r'].stderr)
        self.assertEqual(r['r'].reasons, None)

        ct = TestController()
        rr = make_runner(TestRunner, [ct], name='r')
        tc = TestCase(runner=rr, controllers=(ct,))
        tc.setState(TestCase.Result.PASS)
        fm.reportResults(tc)
        self.assertEqual(tc.progress, TestCase.Progress.FINISHED)
        self.assertEqual(tc.state, TestCase.Result.FATAL)
        r = tc.results
        self.assertEqual(r['r'].state, TestCase.Result.FATAL)
        self.assertEqual(r['r'].returncode, None)
        self.assertEqual(r['r'].stdout, '')
        self.assertIn("The results have not been set via the `setResults` method.", r['r'].stderr)
        self.assertEqual(r['r'].reasons, None)

        ct = TestController()
        rr = make_runner(TestRunner, [ct], name='r')
        tc = TestCase(runner=rr, controllers=(ct,))
        tc.setState(TestCase.Result.PASS)
        tc.setResults({'r':TestCase.Data(TestCase.Result.ERROR, None, 'r_out', 'r_err', None)})
        fm.reportResults(tc)
        self.assertEqual(tc.progress, TestCase.Progress.FINISHED)
        self.assertEqual(tc.state, TestCase.Result.FATAL)
        r = tc.results
        self.assertEqual(r['r'].state, TestCase.Result.FATAL)
        self.assertEqual(r['r'].returncode, None)
        self.assertEqual(r['r'].stdout, '')
        self.assertIn("The execution has not finished, so results cannot be reported.", r['r'].stderr)
        self.assertEqual(r['r'].reasons, None)


    @mock.patch("moosetools.moosetest.base.Formatter._printState")
    def testReportProgress(self, pstate):

        # Runner
        fm = Formatter(progress_interval=0)
        ct = TestController()
        rr = make_runner(TestRunner, [ct], name='r')
        tc = TestCase(runner=rr, controllers=(ct,))

        fm.reportProgress(tc)
        pstate.assert_called_with(tc, rr, TestCase.Progress.WAITING, None)

        tc.setProgress(TestCase.Progress.RUNNING)
        fm.reportProgress(tc)
        pstate.assert_called_with(tc, rr, TestCase.Progress.RUNNING, None)

        tc.setProgress(TestCase.Progress.FINISHED)
        fm.reportProgress(tc)
        pstate.assert_called_with(tc, rr, TestCase.Progress.FINISHED, None)

        # Error
        tc._TestCase__progress = None
        fm.reportProgress(tc)
        pstate.assert_called_with(tc, rr, TestCase.Progress.FINISHED, None)
        self.assertEqual(tc.progress, TestCase.Progress.FINISHED)
        self.assertEqual(tc.state, TestCase.Result.FATAL)
        r = tc.results
        self.assertEqual(r['r'].state, TestCase.Result.FATAL)
        self.assertEqual(r['r'].returncode, None)
        self.assertEqual(r['r'].stdout, '')
        self.assertIn("The progress has not been set via the `setProgress` method.", r['r'].stderr)
        self.assertEqual(r['r'].reasons, None)


    @mock.patch("moosetools.moosetest.base.Formatter.formatDifferResult")
    @mock.patch("moosetools.moosetest.base.Formatter.formatRunnerResult")
    @mock.patch("moosetools.moosetest.base.Formatter.formatDifferState")
    @mock.patch("moosetools.moosetest.base.Formatter.formatRunnerState")
    def testPrintState(self, r_state, d_state, r_result, d_result):

        # Runner
        ct = TestController()
        fm = Formatter()
        dr = make_differ(TestDiffer, [ct], name='d')
        rr = make_runner(TestRunner, [ct], differs=(dr,), name='r')
        tc = TestCase(runner=rr, controllers=(ct,))
        tc.setProgress(TestCase.Progress.RUNNING)

        # Runner, progress
        fm._printState(tc, rr, TestCase.Progress.RUNNING, ["all the reasons"])
        kwargs = r_state.call_args.kwargs
        self.assertEqual(kwargs['name'], 'r')
        self.assertEqual(kwargs['state'], TestCase.Progress.RUNNING)
        self.assertEqual(kwargs['reasons'], ["all the reasons"])
        self.assertIsInstance(kwargs['duration'], float) # exact number can't be tested
        self.assertIsInstance(kwargs['percent'], float)

        # Differ, progress
        tc.setProgress(TestCase.Progress.FINISHED) # call this to use execute time
        fm._printState(tc, dr, TestCase.Progress.FINISHED, ["all the reasons"])
        kwargs = d_state.call_args.kwargs
        self.assertEqual(kwargs['name'], 'd')
        self.assertEqual(kwargs['state'], TestCase.Progress.FINISHED)
        self.assertEqual(kwargs['reasons'], ["all the reasons"])
        self.assertIsInstance(kwargs['duration'], float) # exact number can't be tested
        self.assertIsInstance(kwargs['percent'], float)

        # Runner, results
        tc.setProgress(TestCase.Progress.FINISHED)
        tc.setState(TestCase.Result.PASS)
        tc.setResults({'r':TestCase.Data(TestCase.Result.PASS, None, 'r_out', 'r_err', None),
                      'd':TestCase.Data(TestCase.Result.PASS, None, 'd_out', 'd_err', None)})
        fm._printResult(tc, rr, tc.results['r'])
        kwargs = r_result.call_args.kwargs
        self.assertEqual(kwargs['name'], 'r')
        self.assertEqual(kwargs['state'], TestCase.Result.PASS)
        self.assertEqual(kwargs['reasons'], None)
        self.assertIsInstance(kwargs['duration'], float) # exact number can't be tested
        self.assertIsInstance(kwargs['percent'], float)
        self.assertEqual(kwargs['stdout'], 'r_out')
        self.assertEqual(kwargs['stderr'], 'r_err')

        # Differ, results
        tc.setState(TestCase.Result.PASS)
        tc.setResults({'r':TestCase.Data(TestCase.Result.PASS, None, 'r_out', 'r_err', None),
                       'd':TestCase.Data(TestCase.Result.PASS, None, 'd_out', 'd_err', None)})
        fm._printResult(tc, dr, tc.results['d'])
        kwargs = d_result.call_args.kwargs
        self.assertEqual(kwargs['name'], 'd')
        self.assertEqual(kwargs['state'], TestCase.Result.PASS)
        self.assertEqual(kwargs['reasons'], None)
        self.assertIsInstance(kwargs['duration'], float) # exact number can't be tested
        self.assertIsInstance(kwargs['percent'], float)
        self.assertEqual(kwargs['stdout'], 'd_out')
        self.assertEqual(kwargs['stderr'], 'd_err')

    def testTime(self):
        fm = Formatter()
        self.assertTrue(fm.time < 0.01)
        time.sleep(1.01)
        self.assertTrue(fm.time > 1)

    @mock.patch("moosetools.moosetest.base.Formatter._printState")
    def testProgressTime(self, pstate):
        rr = make_runner(TestRunner, name='r')
        tc = TestCase(runner=rr)

        fm = Formatter(progress_interval=1)
        fm.reportProgress(tc)
        pstate.assert_not_called()

        time.sleep(1.1)
        fm.reportProgress(tc)
        pstate.assert_called()



if __name__ == '__main__':
    unittest.main(module=__name__, verbosity=2, buffer=True)
