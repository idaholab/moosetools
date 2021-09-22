#!/usr/bin/env python3
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
import unittest
from unittest import mock
import queue
import uuid
import platform
import logging
import concurrent.futures

from moosetools.moosetest.base import make_runner, make_differ, TestCase, State, Formatter, Runner, Differ
from moosetools.moosetest.runners import ExecuteCommand
from moosetools.moosetest import run, fuzzer
from moosetools.moosetest.run import _execute_testcase, _execute_testcases
from moosetools.moosetest.run import _report_progress_and_results

# I do not want the tests directory to be packages with __init__.py, so load from file
sys.path.append(os.path.join(os.path.dirname(__file__)))
from _helpers import TestController, TestRunner, TestDiffer


class PipeProxy(object):
    def __init__(self):
        self.state = None
        self.result = None

    def send(self, data):
        self.state = data[0]
        self.result = data[1]

    def close(self):
        pass


def get_uid(tc):
    return tc.getParam('_unique_id')


def make_testcase_map(*args):
    out = dict()
    for tc in args:
        out[tc.getParam('_unique_id')] = tc
    return out


class TestRunExecuteHelpers(unittest.TestCase):
    @unittest.skipIf(platform.python_version() < '3.7', "Python 3.7 or greater required")
    def test_execute_testcase(self):
        r = make_runner(ExecuteCommand, name='test', command=('sleep', '0'))
        tc = TestCase(runner=r)

        # No error
        conn = PipeProxy()
        _execute_testcase(tc, conn)

        self.assertEqual(conn.state, TestCase.Result.PASS)
        self.assertIn('test', conn.result)

        data = conn.result['test']
        self.assertEqual(data.state, TestCase.Result.PASS)
        self.assertEqual(data.returncode, 0)
        self.assertEqual(data.stderr, "")
        self.assertIn("sleep 0", data.stdout)
        self.assertEqual(data.reasons, [])

        # Exception
        with mock.patch('moosetools.moosetest.base.TestCase.execute',
                        side_effect=Exception("wrong")):
            _execute_testcase(tc, conn)

        self.assertEqual(conn.state, TestCase.Result.FATAL)
        self.assertIn('test', conn.result)

        data = conn.result['test']
        self.assertEqual(data.state, TestCase.Result.FATAL)
        self.assertEqual(data.returncode, None)
        self.assertEqual(data.stdout, None)
        self.assertIn("wrong", data.stderr)
        self.assertEqual(data.reasons, None)

    @unittest.skipIf(platform.python_version() < '3.7', "Python 3.7 or greater required")
    def test_execute_testcases(self):

        r0 = make_runner(TestRunner, name='test0', sleep=0.2)
        r1 = make_runner(TestRunner, name='test1', sleep=0.3)

        tc0 = TestCase(runner=r0)
        tc1 = TestCase(runner=r1)

        # No error
        q = queue.Queue()
        _execute_testcases([tc0, tc1], q, 2)

        u, p, s, r = q.get()
        self.assertEqual(u, tc0.unique_id)
        self.assertEqual(p, TestCase.Progress.RUNNING)
        self.assertEqual(s, None)
        self.assertEqual(r, None)

        u, p, s, r = q.get()
        self.assertEqual(u, tc0.unique_id)
        self.assertEqual(p, TestCase.Progress.FINISHED)
        self.assertEqual(s, TestCase.Result.PASS)
        self.assertIn('test0', r)
        data = r['test0']
        self.assertEqual(data.state, TestCase.Result.PASS)
        self.assertEqual(data.returncode, 2011)
        self.assertEqual(data.stdout, "")
        self.assertEqual(data.stderr, "")
        self.assertEqual(data.reasons, [])

        u, p, s, r = q.get()
        self.assertEqual(u, tc1.unique_id)
        self.assertEqual(p, TestCase.Progress.RUNNING)
        self.assertEqual(s, None)
        self.assertEqual(r, None)

        u, p, s, r = q.get()
        self.assertEqual(u, tc1.unique_id)
        self.assertEqual(p, TestCase.Progress.FINISHED)
        self.assertEqual(s, TestCase.Result.PASS)
        self.assertIn('test1', r)
        data = r['test1']
        self.assertEqual(data.state, TestCase.Result.PASS)
        self.assertEqual(data.returncode, 2011)
        self.assertEqual(data.stdout, "")
        self.assertEqual(data.stderr, "")
        self.assertEqual(data.reasons, [])

        # Exception and run
        r0.parameters().setValue('raise', True)
        _execute_testcases([tc0, tc1], q, 2)

        u, p, s, r = q.get()
        self.assertEqual(u, tc0.unique_id)
        self.assertEqual(p, TestCase.Progress.RUNNING)
        self.assertEqual(s, None)
        self.assertEqual(r, None)

        u, p, s, r = q.get()
        self.assertEqual(u, tc0.unique_id)
        self.assertEqual(p, TestCase.Progress.FINISHED)
        self.assertEqual(s, TestCase.Result.EXCEPTION)
        self.assertIn('test0', r)
        data = r['test0']
        self.assertEqual(data.state, TestCase.Result.EXCEPTION)
        self.assertEqual(data.returncode, None)
        self.assertEqual(data.stdout, "")
        self.assertIn("runner raise", data.stderr)
        self.assertEqual(data.reasons, None)

        u, p, s, r = q.get()
        self.assertEqual(u, tc1.unique_id)
        self.assertEqual(p, TestCase.Progress.RUNNING)
        self.assertEqual(s, None)
        self.assertEqual(r, None)

        u, p, s, r = q.get()
        self.assertEqual(u, tc1.unique_id)
        self.assertEqual(p, TestCase.Progress.FINISHED)
        self.assertEqual(s, TestCase.Result.PASS)
        self.assertIn('test1', r)
        data = r['test1']
        self.assertEqual(data.state, TestCase.Result.PASS)
        self.assertEqual(data.returncode, 2011)
        self.assertEqual(data.stderr, "")
        self.assertEqual(data.stdout, "")
        self.assertEqual(data.reasons, [])

        # Exception and skip
        r1.parameters().setValue('requires', ('test0', ))
        _execute_testcases([tc0, tc1], q, 2)

        u, p, s, r = q.get()
        self.assertEqual(u, tc0.unique_id)
        self.assertEqual(p, TestCase.Progress.RUNNING)
        self.assertEqual(s, None)
        self.assertEqual(r, None)

        u, p, s, r = q.get()
        self.assertEqual(u, tc0.unique_id)
        self.assertEqual(p, TestCase.Progress.FINISHED)
        self.assertEqual(s, TestCase.Result.EXCEPTION)
        self.assertIn('test0', r)
        data = r['test0']
        self.assertEqual(data.state, TestCase.Result.EXCEPTION)
        self.assertEqual(data.returncode, None)
        self.assertEqual(data.stdout, "")
        self.assertIn("runner raise", data.stderr)
        self.assertEqual(data.reasons, None)

        u, p, s, r = q.get()
        self.assertEqual(u, tc1.unique_id)
        self.assertEqual(p, TestCase.Progress.FINISHED)
        self.assertEqual(s, TestCase.Result.SKIP)
        self.assertIn('test1', r)
        data = r['test1']
        self.assertEqual(data.state, TestCase.Result.SKIP)
        self.assertEqual(data.returncode, None)
        self.assertEqual(
            data.stderr,
            "For the test 'test1', the required test(s) 'test0' have not executed and passed.")
        self.assertEqual(data.stdout, None)
        self.assertEqual(data.reasons, ['failed dependency'])

        # 'Incorrect' requires
        r0.parameters().setValue('requires', ('wrong', ))
        _execute_testcases([tc0, tc1], q, 2)
        u, p, s, r = q.get()
        self.assertEqual(u, tc0.unique_id)
        self.assertEqual(p, TestCase.Progress.FINISHED)
        self.assertEqual(s, TestCase.Result.FATAL)
        self.assertIn('test0', r)
        data = r['test0']
        self.assertEqual(data.state, TestCase.Result.FATAL)
        self.assertEqual(data.returncode, None)
        self.assertEqual(data.stdout, None)
        self.assertEqual(
            data.stderr,
            "For the test 'test0', the required test(s) 'wrong' have not executed. Either the names provided the the 'requires' parameter are incorrect or the tests are in the wrong order."
        )
        self.assertEqual(data.reasons, ['unknown required test(s)'])

        u, p, s, r = q.get()
        self.assertEqual(u, tc1.unique_id)
        self.assertEqual(p, TestCase.Progress.FINISHED)
        self.assertEqual(s, TestCase.Result.SKIP)
        self.assertIn('test1', r)
        data = r['test1']
        self.assertEqual(data.state, TestCase.Result.SKIP)
        self.assertEqual(data.returncode, None)
        self.assertEqual(
            data.stderr,
            "For the test 'test1', the required test(s) 'test0' have not executed and passed.")
        self.assertEqual(data.stdout, None)
        self.assertEqual(data.reasons, ['failed dependency'])

        # Timeout
        r2 = make_runner(ExecuteCommand, name='test2', command=('sleep', '2'))
        tc2 = TestCase(runner=r2)
        _execute_testcases([tc2], q, 1)

        u, p, s, r = q.get()
        self.assertEqual(u, tc2.unique_id)
        self.assertEqual(p, TestCase.Progress.RUNNING)
        self.assertEqual(s, None)
        self.assertEqual(r, None)

        u, p, s, r = q.get()
        self.assertEqual(u, tc2.unique_id)
        self.assertEqual(p, TestCase.Progress.FINISHED)
        self.assertEqual(s, TestCase.Result.TIMEOUT)
        self.assertIn('test2', r)
        data = r['test2']
        self.assertEqual(data.state, TestCase.Result.TIMEOUT)
        self.assertEqual(data.returncode, None)
        self.assertEqual(data.stdout, None)
        self.assertEqual(data.stderr, None)
        self.assertEqual(data.reasons, ['max time (1) exceeded'])


@unittest.skipIf(platform.python_version() < '3.7', "Python 3.7 or greater required")
class TestReportHelper(unittest.TestCase):
    @mock.patch('moosetools.moosetest.base.Formatter.reportResults')
    @mock.patch('moosetools.moosetest.base.TestCase.setResults')
    @mock.patch('moosetools.moosetest.base.TestCase.setState')
    @mock.patch('moosetools.moosetest.base.TestCase.setProgress')
    def test_report_progress_and_results(self, tc_prog, tc_state, tc_results, fm_results):

        fm = Formatter()
        r0 = make_runner(ExecuteCommand, name='test0', command=('sleep', '0.2'))
        tc0 = TestCase(runner=r0)
        tc_prog.reset_mock()

        _report_progress_and_results(tc0, fm, None, None, None)
        tc_prog.assert_not_called()
        tc_state.assert_not_called()
        tc_results.assert_not_called()
        fm_results.assert_not_called()
        tc_prog.reset_mock()

        _report_progress_and_results(tc0, fm, TestCase.Progress.RUNNING, None, None)
        tc_prog.assert_called_once_with(TestCase.Progress.RUNNING)
        tc_state.assert_not_called()
        tc_results.assert_not_called()
        fm_results.assert_not_called()
        tc_prog.reset_mock()

        _report_progress_and_results(tc0, fm, TestCase.Progress.FINISHED, None, None)
        tc_prog.assert_called_once_with(TestCase.Progress.FINISHED)
        tc_state.assert_called_once_with(None)
        tc_results.assert_called_once_with(None)
        fm_results.assert_called_once_with(tc0)


@unittest.skipIf(platform.python_version() < '3.7', "Python 3.7 or greater required")
class TestRun(unittest.TestCase):
    ANY = 42

    class IN(object):
        def __init__(self, value):
            self.value = value

    def setUp(self):
        r_state_mock = mock.patch('moosetools.moosetest.base.Formatter.formatRunnerProgress')
        r_results_mock = mock.patch('moosetools.moosetest.base.Formatter.formatRunnerResult')
        d_state_mock = mock.patch('moosetools.moosetest.base.Formatter.formatDifferProgress')
        d_results_mock = mock.patch('moosetools.moosetest.base.Formatter.formatDifferResult')
        complete_mock = mock.patch('moosetools.moosetest.base.Formatter.formatComplete')

        self._r_state = r_state_mock.start()
        self.addCleanup(r_state_mock.stop)

        self._r_results = r_results_mock.start()
        self.addCleanup(r_results_mock.stop)

        self._d_state = d_state_mock.start()
        self.addCleanup(d_state_mock.stop)

        self._d_results = d_results_mock.start()
        self.addCleanup(d_results_mock.stop)

        self._complete = complete_mock.start()
        self.addCleanup(complete_mock.stop)

        TestCase.__TOTAL__ = 0
        TestCase.__FINISHED__ = 0

    def resetMockObjects(self):
        self._r_state.reset_mock()
        self._d_state.reset_mock()
        self._r_results.reset_mock()
        self._d_results.reset_mock()
        self._complete.reset_mock()

    def assertCall(self, mock_obj, *args, **kwargs):
        if isinstance(mock_obj, mock._Call):
            call = mock_obj
        else:
            call = mock_obj.call_args

        for arg in args:
            self.assertIn(arg, mock_obj.call_args.args)

        for key, value in kwargs.items():
            if value is TestRun.ANY:
                self.assertIn(key, call[1])  # call.kwargs[key] in python > 3.7
            elif isinstance(value, TestRun.IN):
                self.assertIn(value.value, call[1][key])  # call.kwargs[key] in python > 3.7
            else:
                self.assertEqual(call[1][key], value)  # call.kwargs[key] in python > 3.7

    def testFutureException(self):
        r = TestRunner(name='Andrew', stderr=True, stdout=True)
        fm = Formatter()

        with mock.patch('concurrent.futures.Future.exception', return_value=Exception('future exception')), \
        self.assertRaises(Exception) as cm:
            rcode = run([[r]], tuple(), fm)
        self.assertIn('future exception', str(cm.exception))

    def testRunnerOnly(self):
        r = TestRunner(name='Andrew', stderr=True, stdout=True)
        fm = Formatter()

        # PASS
        rcode = run([[r]], tuple(), fm)
        self.assertEqual(rcode, 0)
        self._r_state.assert_called_once()
        self._r_results.assert_called_once()
        self._d_state.assert_not_called()
        self._d_results.assert_not_called()
        self._complete.assert_called_once()
        self.assertCall(self._r_state,
                        name='Andrew',
                        state=TestCase.Result.PASS,
                        reasons=[],
                        percent=100,
                        duration=TestRun.ANY)
        self.assertCall(self._r_results,
                        name='Andrew',
                        state=TestCase.Result.PASS,
                        reasons=[],
                        percent=100,
                        duration=TestRun.ANY,
                        returncode=2011,
                        stdout=TestRun.IN('runner stdout'),
                        stderr=TestRun.IN('runner stderr'))

        # ERROR
        self.resetMockObjects()
        r.setValue('error', True)
        r.setValue('stderr', False)
        r.setValue('stdout', False)
        rcode = run([[r]], tuple(), fm)
        self.assertEqual(rcode, 1)
        self._r_state.assert_called_once()
        self._r_results.assert_called_once()
        self._d_state.assert_not_called()
        self._d_results.assert_not_called()
        self._complete.assert_called_once()
        self.assertCall(self._r_state,
                        name='Andrew',
                        state=TestCase.Result.ERROR,
                        reasons=[],
                        percent=100,
                        duration=TestRun.ANY)
        self.assertCall(self._r_results,
                        name='Andrew',
                        state=TestCase.Result.ERROR,
                        reasons=[],
                        percent=100,
                        duration=TestRun.ANY,
                        returncode=2011,
                        stdout='',
                        stderr=TestRun.IN('runner error\n'))

        # EXCEPTION
        self.resetMockObjects()
        r.setValue('error', False)
        r.setValue('raise', True)
        rcode = run([[r]], tuple(), fm)
        self.assertEqual(rcode, 1)
        self._r_state.assert_called_once()
        self._r_results.assert_called_once()
        self._d_state.assert_not_called()
        self._d_results.assert_not_called()
        self._complete.assert_called_once()
        self.assertCall(self._r_state,
                        name='Andrew',
                        state=TestCase.Result.EXCEPTION,
                        reasons=None,
                        percent=100,
                        duration=TestRun.ANY)
        self.assertCall(self._r_results,
                        name='Andrew',
                        state=TestCase.Result.EXCEPTION,
                        reasons=None,
                        percent=100,
                        duration=TestRun.ANY,
                        returncode=None,
                        stdout='',
                        stderr=TestRun.IN('runner raise\n'))

        # TIMEOUT
        self.resetMockObjects()
        r.setValue('raise', False)
        r.setValue('sleep', 1)
        rcode = run([[r]], tuple(), fm, timeout=0.5)
        self.assertEqual(rcode, 1)
        self._r_state.assert_called_once()
        self._r_results.assert_called_once()
        self._d_state.assert_not_called()
        self._d_results.assert_not_called()
        self._complete.assert_called_once()
        self.assertCall(self._r_state,
                        name='Andrew',
                        state=TestCase.Result.TIMEOUT,
                        reasons=['max time (0.5) exceeded'],
                        percent=100,
                        duration=TestRun.ANY)
        self.assertCall(self._r_results,
                        name='Andrew',
                        state=TestCase.Result.TIMEOUT,
                        reasons=['max time (0.5) exceeded'],
                        percent=100,
                        duration=TestRun.ANY,
                        returncode=None,
                        stdout=None,
                        stderr=None)

    def testRunnerWithController(self):
        c = TestController(stdout=True, stderr=True)
        r = make_runner(TestRunner, (c, ), name='Andrew')
        fm = Formatter()

        # PASS
        rcode = run([[r]], (c, ), fm)
        self.assertEqual(rcode, 0)
        self._r_state.assert_called_once()
        self._r_results.assert_called_once()
        self._d_state.assert_not_called()
        self._d_results.assert_not_called()
        self._complete.assert_called_once()
        self.assertCall(self._r_state,
                        name='Andrew',
                        state=TestCase.Result.PASS,
                        reasons=[],
                        percent=100,
                        duration=TestRun.ANY)
        self.assertCall(self._r_results,
                        name='Andrew',
                        state=TestCase.Result.PASS,
                        reasons=[],
                        percent=100,
                        duration=TestRun.ANY,
                        stdout=TestRun.IN('controller stdout'),
                        stderr=TestRun.IN('controller stderr'))

        # ERROR, CONTROLLER
        self.resetMockObjects()
        c.setValue('error', True)
        c.setValue('stderr', False)
        c.setValue('stdout', False)
        rcode = run([[r]], (c, ), fm)
        self.assertEqual(rcode, 1)
        self._r_state.assert_called_once()
        self._r_results.assert_called_once()
        self._d_state.assert_not_called()
        self._d_results.assert_not_called()
        self._complete.assert_called_once()
        self.assertCall(self._r_state,
                        name='Andrew',
                        state=TestCase.Result.FATAL,
                        reasons=[],
                        percent=100,
                        duration=TestRun.ANY)
        self.assertCall(self._r_results,
                        name='Andrew',
                        state=TestCase.Result.FATAL,
                        reasons=[],
                        percent=100,
                        duration=TestRun.ANY,
                        returncode=None,
                        stdout='',
                        stderr=TestRun.IN('An error occurred, on the controller'))

        # ERROR, RUNNER (during execution of Controller)
        self.resetMockObjects()
        c.setValue('error', False)
        with mock.patch('moosetools.moosetest.base.Runner.status', return_value=1):
            rcode = run([[r]], (c, ), fm)
        self.assertEqual(rcode, 1)
        self._r_state.assert_called_once()
        self._r_results.assert_called_once()
        self._d_state.assert_not_called()
        self._d_results.assert_not_called()
        self._complete.assert_called_once()
        self.assertCall(self._r_state,
                        name='Andrew',
                        state=TestCase.Result.FATAL,
                        reasons=[],
                        percent=100,
                        duration=TestRun.ANY)
        self.assertCall(self._r_results,
                        name='Andrew',
                        state=TestCase.Result.FATAL,
                        reasons=[],
                        percent=100,
                        duration=TestRun.ANY,
                        returncode=None,
                        stdout='',
                        stderr=TestRun.IN('An error occurred, on the object'))

        # EXCEPTION
        self.resetMockObjects()
        c.setValue('error', False)
        c.setValue('raise', True)
        rcode = run([[r]], (c, ), fm)
        self.assertEqual(rcode, 1)
        self._r_state.assert_called_once()
        self._r_results.assert_called_once()
        self._d_state.assert_not_called()
        self._d_results.assert_not_called()
        self._complete.assert_called_once()
        self.assertCall(self._r_state,
                        name='Andrew',
                        state=TestCase.Result.FATAL,
                        reasons=None,
                        percent=100,
                        duration=TestRun.ANY)
        self.assertCall(self._r_results,
                        name='Andrew',
                        state=TestCase.Result.FATAL,
                        reasons=None,
                        percent=100,
                        duration=TestRun.ANY,
                        returncode=None,
                        stdout='',
                        stderr=TestRun.IN('An exception occurred'))

        # TIMEOUT (because of Controller)
        self.resetMockObjects()
        c.setValue('raise', False)
        c.setValue('sleep', 1)
        rcode = run([[r]], (c, ), fm, timeout=0.5)
        self.assertEqual(rcode, 1)
        self._r_state.assert_called_once()
        self._r_results.assert_called_once()
        self._d_state.assert_not_called()
        self._d_results.assert_not_called()
        self._complete.assert_called_once()
        self.assertCall(self._r_state,
                        name='Andrew',
                        state=TestCase.Result.TIMEOUT,
                        reasons=['max time (0.5) exceeded'],
                        percent=100,
                        duration=TestRun.ANY)
        self.assertCall(self._r_results,
                        name='Andrew',
                        state=TestCase.Result.TIMEOUT,
                        reasons=['max time (0.5) exceeded'],
                        percent=100,
                        duration=TestRun.ANY,
                        returncode=None,
                        stdout=None,
                        stderr=None)

        # SKIP
        self.resetMockObjects()
        c.setValue('skip', True)
        c.setValue('sleep', 0)
        rcode = run([[r]], (c, ), fm)
        self.assertEqual(rcode, 0)
        self._r_state.assert_called_once()
        self._r_results.assert_called_once()
        self._d_state.assert_not_called()
        self._d_results.assert_not_called()
        self._complete.assert_called_once()
        self.assertCall(self._r_state,
                        name='Andrew',
                        state=TestCase.Result.SKIP,
                        reasons=['a reason'],
                        percent=100,
                        duration=TestRun.ANY)
        self.assertCall(self._r_results,
                        name='Andrew',
                        state=TestCase.Result.SKIP,
                        reasons=['a reason'],
                        percent=100,
                        duration=TestRun.ANY,
                        returncode=None,
                        stdout='',
                        stderr=TestRun.IN(''))

    def testRunnerWithDiffers(self):
        d0 = make_differ(TestDiffer, name='a', stderr=True)
        d1 = make_differ(TestDiffer, name='b', stdout=True)
        r = make_runner(TestRunner, name='Andrew', differs=(d0, d1))
        fm = Formatter()

        # PASS
        rcode = run([[r]], tuple(), fm)
        self.assertEqual(rcode, 0)
        self._r_state.assert_called_once()
        self._r_results.assert_called_once()
        self.assertEqual(self._d_state.call_count, 2)
        self.assertEqual(self._d_results.call_count, 2)
        self._complete.assert_called_once()
        self.assertCall(self._r_state,
                        name='Andrew',
                        state=TestCase.Result.PASS,
                        reasons=[],
                        percent=100,
                        duration=TestRun.ANY)
        self.assertCall(self._r_results,
                        name='Andrew',
                        state=TestCase.Result.PASS,
                        reasons=[],
                        percent=100,
                        duration=TestRun.ANY,
                        stdout='',
                        stderr='')

        self.assertCall(self._d_state.call_args_list[0],
                        name='a',
                        state=TestCase.Result.PASS,
                        reasons=[],
                        percent=100,
                        duration=TestRun.ANY)
        self.assertCall(self._d_state.call_args_list[1],
                        name='b',
                        state=TestCase.Result.PASS,
                        reasons=[],
                        percent=100,
                        duration=TestRun.ANY)

        self.assertCall(self._d_results.call_args_list[0],
                        name='a',
                        state=TestCase.Result.PASS,
                        reasons=[],
                        percent=100,
                        duration=TestRun.ANY,
                        stdout='',
                        stderr=TestRun.IN('differ stderr'))
        self.assertCall(self._d_results.call_args_list[1],
                        name='b',
                        state=TestCase.Result.PASS,
                        reasons=[],
                        percent=100,
                        duration=TestRun.ANY,
                        stdout=TestRun.IN('differ stdout'),
                        stderr='')

        # ERROR, DIFFER 0
        self.resetMockObjects()
        d0.setValue('stderr', False)
        d1.setValue('stdout', False)
        d0.setValue('error', True)
        rcode = run([[r]], tuple(), fm)
        self.assertEqual(rcode, 1)
        self._r_state.assert_called_once()
        self._r_results.assert_called_once()
        self.assertEqual(self._d_state.call_count, 2)
        self.assertEqual(self._d_results.call_count, 2)
        self._complete.assert_called_once()
        self.assertCall(self._r_state,
                        name='Andrew',
                        state=TestCase.Result.DIFF,
                        reasons=[],
                        percent=100,
                        duration=TestRun.ANY)
        self.assertCall(self._r_results,
                        name='Andrew',
                        state=TestCase.Result.PASS,
                        reasons=[],
                        percent=100,
                        duration=TestRun.ANY,
                        stdout='',
                        stderr='')

        self.assertCall(self._d_state.call_args_list[0],
                        name='a',
                        state=TestCase.Result.DIFF,
                        reasons=[],
                        percent=100,
                        duration=TestRun.ANY)
        self.assertCall(self._d_state.call_args_list[1],
                        name='b',
                        state=TestCase.Result.PASS,
                        reasons=[],
                        percent=100,
                        duration=TestRun.ANY)

        self.assertCall(self._d_results.call_args_list[0],
                        name='a',
                        state=TestCase.Result.DIFF,
                        reasons=[],
                        percent=100,
                        duration=TestRun.ANY,
                        stdout='',
                        stderr=TestRun.IN('differ error'))
        self.assertCall(self._d_results.call_args_list[1],
                        name='b',
                        state=TestCase.Result.PASS,
                        reasons=[],
                        percent=100,
                        duration=TestRun.ANY,
                        stdout='',
                        stderr='')

        # EXCEPTION, DIFFER 1
        self.resetMockObjects()
        d0.setValue('error', False)
        d1.setValue('raise', True)
        rcode = run([[r]], tuple(), fm)
        self.assertEqual(rcode, 1)
        self._r_state.assert_called_once()
        self._r_results.assert_called_once()
        self.assertEqual(self._d_state.call_count, 2)
        self.assertEqual(self._d_results.call_count, 2)
        self._complete.assert_called_once()
        self.assertCall(self._r_state,
                        name='Andrew',
                        state=TestCase.Result.EXCEPTION,
                        reasons=[],
                        percent=100,
                        duration=TestRun.ANY)
        self.assertCall(self._r_results,
                        name='Andrew',
                        state=TestCase.Result.PASS,
                        reasons=[],
                        percent=100,
                        duration=TestRun.ANY,
                        stdout='',
                        stderr='')

        self.assertCall(self._d_state.call_args_list[0],
                        name='a',
                        state=TestCase.Result.PASS,
                        reasons=[],
                        percent=100,
                        duration=TestRun.ANY)
        self.assertCall(self._d_state.call_args_list[1],
                        name='b',
                        state=TestCase.Result.EXCEPTION,
                        reasons=None,
                        percent=100,
                        duration=TestRun.ANY)

        self.assertCall(self._d_results.call_args_list[0],
                        name='a',
                        state=TestCase.Result.PASS,
                        reasons=[],
                        percent=100,
                        duration=TestRun.ANY,
                        stdout='',
                        stderr='')
        self.assertCall(self._d_results.call_args_list[1],
                        name='b',
                        state=TestCase.Result.EXCEPTION,
                        reasons=None,
                        percent=100,
                        duration=TestRun.ANY,
                        stdout='',
                        stderr=TestRun.IN('differ raise'))

        # TIMEOUT, DIFFER 1
        self.resetMockObjects()
        d1.setValue('sleep', 1)
        d1.setValue('raise', False)
        rcode = run([[r]], tuple(), fm, timeout=0.5)
        self.assertEqual(rcode, 1)
        self._r_state.assert_called_once()
        self._r_results.assert_called_once()
        self.assertEqual(self._d_state.call_count, 0)
        self.assertEqual(self._d_results.call_count, 0)
        self._complete.assert_called_once()
        self.assertCall(self._r_state,
                        name='Andrew',
                        state=TestCase.Result.TIMEOUT,
                        reasons=['max time (0.5) exceeded'],
                        percent=100,
                        duration=TestRun.ANY)
        self.assertCall(self._r_results,
                        name='Andrew',
                        state=TestCase.Result.TIMEOUT,
                        reasons=['max time (0.5) exceeded'],
                        percent=100,
                        duration=TestRun.ANY,
                        stdout=None,
                        stderr=None)

    def testRunnerWithDiffersWithControllers(self):
        c = TestController()
        d0 = make_differ(TestDiffer, (c, ), name='a')
        d1 = make_differ(TestDiffer, (c, ), name='b')
        r = make_runner(TestRunner, (c, ), name='Andrew', differs=(d0, d1))
        fm = Formatter()

        # SKIP, RUNNER
        c.setValue('skip', True)
        rcode = run([[r]], (c, ), fm)
        self.assertEqual(rcode, 0)
        self._r_state.assert_called_once()
        self._r_results.assert_called_once()
        self._d_state.assert_not_called()
        self._d_results.assert_not_called()
        self._complete.assert_called_once()
        self.assertCall(self._r_state,
                        name='Andrew',
                        state=TestCase.Result.SKIP,
                        reasons=['a reason'],
                        percent=100,
                        duration=TestRun.ANY)
        self.assertCall(self._r_results,
                        name='Andrew',
                        state=TestCase.Result.SKIP,
                        reasons=['a reason'],
                        percent=100,
                        duration=TestRun.ANY,
                        returncode=None,
                        stdout='',
                        stderr='')

        # SKIP, DIFFER
        self.resetMockObjects()
        c.setValue('object_name', d0.name())
        rcode = run([[r]], (c, ), fm)
        self.assertEqual(rcode, 0)
        self._r_state.assert_called_once()
        self._r_results.assert_called_once()
        self.assertEqual(self._d_state.call_count, 2)
        self.assertEqual(self._d_results.call_count, 2)
        self._complete.assert_called_once()
        self.assertCall(self._r_state,
                        name='Andrew',
                        state=TestCase.Result.PASS,
                        reasons=[],
                        percent=100,
                        duration=TestRun.ANY)
        self.assertCall(self._r_results,
                        name='Andrew',
                        state=TestCase.Result.PASS,
                        reasons=[],
                        percent=100,
                        duration=TestRun.ANY,
                        returncode=2011,
                        stdout='',
                        stderr='')

        self.assertCall(self._d_state.call_args_list[0],
                        name='a',
                        state=TestCase.Result.SKIP,
                        reasons=['a reason'],
                        percent=100,
                        duration=TestRun.ANY)
        self.assertCall(self._d_state.call_args_list[1],
                        name='b',
                        state=TestCase.Result.PASS,
                        reasons=[],
                        percent=100,
                        duration=TestRun.ANY)

        self.assertCall(self._d_results.call_args_list[0],
                        name='a',
                        state=TestCase.Result.SKIP,
                        reasons=['a reason'],
                        percent=100,
                        duration=TestRun.ANY,
                        stdout='',
                        stderr='')
        self.assertCall(self._d_results.call_args_list[1],
                        name='b',
                        state=TestCase.Result.PASS,
                        reasons=[],
                        percent=100,
                        duration=TestRun.ANY,
                        stdout='',
                        stderr='')

    def testMaxFail(self):
        r0 = make_runner(TestRunner, name='Just Andrew', error=True)
        r1 = make_runner(TestRunner, name='Other Andrew', requires=("Just Andrew", ), sleep=0.5)
        r2 = make_runner(TestRunner, name='Best Andrew', requires=("Just Andrew", ))
        fm = Formatter()

        # This test helped me catch a logic bug. This is a single group, so only a single worker
        # is created. Thus, even if max fail is hit the worker should finish, thus nothing reported
        # as max failed. At one point both the max fail and dependency message were being dumped
        # with this test, but it should only be the dependency.
        rcode = run([[r0, r1, r2]], tuple(), fm, max_fails=1)
        self.assertEqual(rcode, 1)
        self.assertEqual(self._r_state.call_count, 3)
        self.assertEqual(self._r_results.call_count, 3)

        self.assertCall(self._r_state.call_args_list[0],
                        name='Just Andrew',
                        state=TestCase.Result.ERROR,
                        reasons=[],
                        percent=TestRun.ANY,
                        duration=TestRun.ANY)
        self.assertCall(self._r_results.call_args_list[0],
                        name='Just Andrew',
                        state=TestCase.Result.ERROR,
                        reasons=[],
                        percent=TestRun.ANY,
                        duration=TestRun.ANY,
                        returncode=2011,
                        stdout='',
                        stderr=TestRun.IN('runner error'))

        self.assertCall(self._r_state.call_args_list[1],
                        name='Other Andrew',
                        state=TestCase.Result.SKIP,
                        reasons=['failed dependency'],
                        percent=TestRun.ANY,
                        duration=TestRun.ANY)
        self.assertCall(
            self._r_results.call_args_list[1],
            name='Other Andrew',
            state=TestCase.Result.SKIP,
            reasons=['failed dependency'],
            percent=TestRun.ANY,
            duration=TestRun.ANY,
            returncode=None,
            stdout=None,
            stderr=TestRun.
            IN("For the test 'Other Andrew', the required test(s) 'Just Andrew' have not executed and passed."
               ))

        self.assertCall(self._r_state.call_args_list[2],
                        name='Best Andrew',
                        state=TestCase.Result.SKIP,
                        reasons=['failed dependency'],
                        percent=100,
                        duration=TestRun.ANY)
        self.assertCall(
            self._r_results.call_args_list[2],
            name='Best Andrew',
            state=TestCase.Result.SKIP,
            reasons=['failed dependency'],
            percent=100,
            duration=TestRun.ANY,
            returncode=None,
            stdout=None,
            stderr=TestRun.
            IN("For the test 'Best Andrew', the required test(s) 'Just Andrew' have not executed and passed."
               ))

        # Similar to above, but with individual groups
        groups = list()
        for i in range(5):
            r = make_runner(TestRunner, name=str(i), sleep=1)
            groups.append([r])

        groups[0][0].setValue('error', True)
        groups[0][0].setValue('sleep', 0)

        self.resetMockObjects()
        rcode = run(groups, tuple(), fm, n_threads=1, max_fails=1)

        self.assertEqual(rcode, 1)
        self.assertEqual(self._r_state.call_count, 5)
        self.assertEqual(self._r_results.call_count, 5)

        # Only look at first and last, the middle can change depending how fast works fire up
        self.assertCall(self._r_state.call_args_list[0],
                        name='0',
                        state=TestCase.Result.ERROR,
                        reasons=[],
                        percent=TestRun.ANY,
                        duration=TestRun.ANY)
        self.assertCall(self._r_results.call_args_list[0],
                        name='0',
                        state=TestCase.Result.ERROR,
                        reasons=[],
                        percent=TestRun.ANY,
                        duration=TestRun.ANY,
                        returncode=2011,
                        stdout='',
                        stderr=TestRun.IN('runner error'))

        self.assertCall(self._r_state.call_args_list[-1],
                        name='4',
                        state=TestCase.Result.SKIP,
                        reasons=['max failures reached'],
                        percent=100,
                        duration=TestRun.ANY)
        self.assertCall(self._r_results.call_args_list[-1],
                        name='4',
                        state=TestCase.Result.SKIP,
                        reasons=['max failures reached'],
                        percent=100,
                        duration=TestRun.ANY,
                        returncode=None,
                        stdout='',
                        stderr=TestRun.IN("Max failures of 1 exceeded."))

    def testMinFailState(self):
        # SKIP as failure
        c = TestController(skip=True)
        r = make_runner(TestRunner, (c, ), name='Andrew')
        fm = Formatter()

        rcode = run([[r]], (c, ), fm, min_fail_state=TestCase.Result.SKIP)
        self.assertEqual(rcode, 1)  # this is what is being tested
        self.assertEqual(self._r_state.call_count, 1)
        self.assertEqual(self._r_results.call_count, 1)

        self.assertCall(self._r_state.call_args_list[0],
                        name='Andrew',
                        state=TestCase.Result.SKIP,
                        reasons=['a reason'],
                        percent=TestRun.ANY,
                        duration=TestRun.ANY)
        self.assertCall(self._r_results.call_args_list[0],
                        name='Andrew',
                        state=TestCase.Result.SKIP,
                        reasons=['a reason'],
                        percent=TestRun.ANY,
                        duration=TestRun.ANY,
                        returncode=None,
                        stdout='',
                        stderr='')

    def testGroupSkip(self):
        # Same as first test in testMaxFails, but without the max fails

        r0 = make_runner(TestRunner, name='Just Andrew', error=True)
        r1 = make_runner(TestRunner, name='Other Andrew', sleep=0.5, requires=('Just Andrew', ))
        r2 = make_runner(TestRunner, name='Best Andrew', requires=('Other Andrew', ))
        fm = Formatter()

        rcode = run([[r0, r1, r2]], tuple(), fm)
        self.assertEqual(rcode, 1)
        self.assertEqual(self._r_state.call_count, 3)
        self.assertEqual(self._r_results.call_count, 3)

        self.assertCall(self._r_state.call_args_list[0],
                        name='Just Andrew',
                        state=TestCase.Result.ERROR,
                        reasons=[],
                        percent=TestRun.ANY,
                        duration=TestRun.ANY)
        self.assertCall(self._r_results.call_args_list[0],
                        name='Just Andrew',
                        state=TestCase.Result.ERROR,
                        reasons=[],
                        percent=TestRun.ANY,
                        duration=TestRun.ANY,
                        returncode=2011,
                        stdout='',
                        stderr=TestRun.IN('runner error'))

        self.assertCall(self._r_state.call_args_list[1],
                        name='Other Andrew',
                        state=TestCase.Result.SKIP,
                        reasons=['failed dependency'],
                        percent=TestRun.ANY,
                        duration=TestRun.ANY)
        self.assertCall(
            self._r_results.call_args_list[1],
            name='Other Andrew',
            state=TestCase.Result.SKIP,
            reasons=['failed dependency'],
            percent=TestRun.ANY,
            duration=TestRun.ANY,
            returncode=None,
            stdout=None,
            stderr=TestRun.
            IN("For the test 'Other Andrew', the required test(s) 'Just Andrew' have not executed and passed."
               ))

        self.assertCall(self._r_state.call_args_list[2],
                        name='Best Andrew',
                        state=TestCase.Result.SKIP,
                        reasons=['failed dependency'],
                        percent=100,
                        duration=TestRun.ANY)
        self.assertCall(
            self._r_results.call_args_list[2],
            name='Best Andrew',
            state=TestCase.Result.SKIP,
            reasons=['failed dependency'],
            percent=100,
            duration=TestRun.ANY,
            returncode=None,
            stdout=None,
            stderr=TestRun.
            IN("For the test 'Best Andrew', the required test(s) 'Other Andrew' have not executed and passed."
               ))


if __name__ == '__main__':
    unittest.main(module=__name__, verbosity=2, buffer=True)
