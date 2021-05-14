#!/usr/bin/env python3
import os
import sys
import unittest
from unittest import mock
import queue
import dataclasses
import logging
import concurrent.futures

from moosetools.moosetest.base import make_runner, make_differ, TestCase, State, Formatter
from moosetools.moosetest.runners import RunCommand
from moosetools.moosetest import run
from moosetools.moosetest.run import _execute_testcase, _execute_testcases
from moosetools.moosetest.run import _running_results, _running_progress

# I do not want the tests directory to be packages with __init__.py, so load from file
sys.path.append(os.path.join(os.path.dirname(__file__)))
from _helpers import TestController, TestRunner, TestDiffer


@dataclasses.dataclass
class PipeProxy(object):
    state: State = None
    result: dict = None

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
    def test_execute_testcase(self):
        r = make_runner(RunCommand, name='test', command=('sleep', '0'))
        tc = TestCase(runner=r)

        # No error
        conn = PipeProxy()
        _execute_testcase(tc, conn)

        self.assertEqual(conn.state, TestCase.Result.PASS)
        self.assertIn('test', conn.result)

        data = conn.result['test']
        self.assertEqual(data.state, TestCase.Result.PASS)
        self.assertEqual(data.returncode, 0)
        self.assertEqual(data.stdout, "")
        self.assertIn("sleep 0", data.stderr)
        self.assertEqual(data.reasons, None)

        # Exception
        with mock.patch('moosetools.moosetest.base.TestCase.execute', side_effect=Exception("wrong")):
            _execute_testcase(tc, conn)

        self.assertEqual(conn.state, TestCase.Result.FATAL)
        self.assertIn('test', conn.result)

        data = conn.result['test']
        self.assertEqual(data.state, TestCase.Result.FATAL)
        self.assertEqual(data.returncode, None)
        self.assertEqual(data.stdout, "")
        self.assertIn("wrong", data.stderr)
        self.assertEqual(data.reasons, None)

    def test_execute_testcases(self):
        r0 = make_runner(RunCommand, name='test0', command=('sleep', '0.2'))
        r1 = make_runner(RunCommand, name='test1', command=('sleep', '0.3'))

        tc0 = TestCase(runner=r0)
        tc1 = TestCase(runner=r1)

        # No error
        q = queue.Queue()
        _execute_testcases([tc0, tc1], q, 2)

        u, p, s, r = q.get()
        self.assertEqual(u, tc0.getParam('_unique_id'))
        self.assertEqual(p, TestCase.Progress.RUNNING)
        self.assertEqual(s, None)
        self.assertEqual(r, None)

        u, p, s, r = q.get()
        self.assertEqual(u, tc0.getParam('_unique_id'))
        self.assertEqual(p, TestCase.Progress.FINISHED)
        self.assertEqual(s, TestCase.Result.PASS)
        self.assertIn('test0', r)
        data = r['test0']
        self.assertEqual(data.state, TestCase.Result.PASS)
        self.assertEqual(data.returncode, 0)
        self.assertEqual(data.stdout, "")
        self.assertIn("sleep 0.2", data.stderr)
        self.assertEqual(data.reasons, None)

        u, p, s, r = q.get()
        self.assertEqual(u, tc1.getParam('_unique_id'))
        self.assertEqual(p, TestCase.Progress.RUNNING)
        self.assertEqual(s, None)
        self.assertEqual(r, None)

        u, p, s, r = q.get()
        self.assertEqual(u, tc1.getParam('_unique_id'))
        self.assertEqual(p, TestCase.Progress.FINISHED)
        self.assertEqual(s, TestCase.Result.PASS)
        self.assertIn('test1', r)
        data = r['test1']
        self.assertEqual(data.state, TestCase.Result.PASS)
        self.assertEqual(data.returncode, 0)
        self.assertEqual(data.stdout, "")
        self.assertIn("sleep 0.3", data.stderr)
        self.assertEqual(data.reasons, None)

        # Exception and skip
        with mock.patch('moosetools.moosetest.base.TestCase.execute', side_effect=[Exception("wrong"), None]):
            _execute_testcases([tc0, tc1], q, 2)

        u, p, s, r = q.get()
        self.assertEqual(u, tc0.getParam('_unique_id'))
        self.assertEqual(p, TestCase.Progress.RUNNING)
        self.assertEqual(s, None)
        self.assertEqual(r, None)

        u, p, s, r = q.get()
        self.assertEqual(u, tc0.getParam('_unique_id'))
        self.assertEqual(p, TestCase.Progress.FINISHED)
        self.assertEqual(s, TestCase.Result.FATAL)
        self.assertIn('test0', r)
        data = r['test0']
        self.assertEqual(data.state, TestCase.Result.FATAL)
        self.assertEqual(data.returncode, None)
        self.assertEqual(data.stdout, "")
        self.assertIn("wrong", data.stderr)
        self.assertEqual(data.reasons, None)

        u, p, s, r = q.get()
        self.assertEqual(u, tc1.getParam('_unique_id'))
        self.assertEqual(p, TestCase.Progress.FINISHED)
        self.assertEqual(s, TestCase.Result.SKIP)
        self.assertIn('test1', r)
        data = r['test1']
        self.assertEqual(data.state, TestCase.Result.SKIP)
        self.assertEqual(data.returncode, None)
        self.assertEqual(data.stdout, "")
        self.assertIn("A previous", data.stderr)
        self.assertEqual(data.reasons, ['dependency'])

        # Timeout
        r2 = make_runner(RunCommand, name='test2', command=('sleep', '2'))
        tc2 = TestCase(runner=r2)
        _execute_testcases([tc2], q, 1)
        u, p, s, r = q.get()
        self.assertEqual(u, tc2.getParam('_unique_id'))
        self.assertEqual(p, TestCase.Progress.RUNNING)
        self.assertEqual(s, None)
        self.assertEqual(r, None)

        u, p, s, r = q.get()
        self.assertEqual(u, tc2.getParam('_unique_id'))
        self.assertEqual(p, TestCase.Progress.FINISHED)
        self.assertEqual(s, TestCase.Result.TIMEOUT)
        self.assertIn('test2', r)
        data = r['test2']
        self.assertEqual(data.state, TestCase.Result.TIMEOUT)
        self.assertEqual(data.returncode, None)
        self.assertEqual(data.stdout, "")
        self.assertEqual(data.stderr, "")
        self.assertEqual(data.reasons, ['max time (1) exceeded'])


class TestRunningHelpers(unittest.TestCase):

    @mock.patch('moosetools.moosetest.base.Formatter.reportResults')
    @mock.patch('moosetools.moosetest.base.TestCase.setResults')
    @mock.patch('moosetools.moosetest.base.TestCase.setState')
    @mock.patch('moosetools.moosetest.base.TestCase.setProgress')
    def test_running_results(self, tc_prog, tc_state, tc_results, fm_results):

        fm = Formatter()
        q = queue.Queue()

        r0 = make_runner(RunCommand, name='test0', command=('sleep', '0.2'))
        tc0 = TestCase(runner=r0)
        tc_map = make_testcase_map(tc0)

        tc_prog.assert_called_with(TestCase.Progress.WAITING)
        tc_state.assert_not_called()
        tc_results.assert_not_called()
        fm_results.assert_not_called()
        tc_prog.reset_mock()

        q.put((get_uid(tc0), TestCase.Progress.RUNNING, None, None))
        _running_results(tc_map, fm, q)
        tc_prog.assert_called_with(TestCase.Progress.RUNNING)
        tc_state.assert_not_called()
        tc_results.assert_not_called()
        fm_results.assert_not_called()
        tc_prog.reset_mock()

        q.put((get_uid(tc0), TestCase.Progress.FINISHED, TestCase.Result.FATAL, 'data'))
        _running_results(tc_map, fm, q)
        tc_prog.assert_called_with(TestCase.Progress.FINISHED)
        tc_state.assert_called_with(TestCase.Result.FATAL)
        tc_results.assert_called_with('data')
        fm_results.assert_called_with(tc0)

        # tests that the queue.Empty exception is handled
        _running_results(tc_map, fm, queue.Queue())

    @mock.patch('moosetools.moosetest.base.TestCase.setResults')
    @mock.patch('moosetools.moosetest.base.TestCase.setState')
    @mock.patch('moosetools.moosetest.base.TestCase.setProgress')
    @mock.patch('moosetools.moosetest.base.Formatter.reportResults')
    @mock.patch('moosetools.moosetest.base.Formatter.reportProgress')
    def test_running_progress(self, fm_progress, fm_results, tc_prog, tc_state, tc_results):

        future = concurrent.futures.Future()
        fm = Formatter()
        q = queue.Queue()

        r0 = make_runner(RunCommand, name='test0', command=('sleep', '0.2'))
        r1 = make_runner(RunCommand, name='test0', command=('sleep', '0.1'))
        tc0 = TestCase(runner=r0)
        tc1 = TestCase(runner=r1)
        tc_prog.reset_mock()

        tc_map = make_testcase_map(tc0, tc1)

        # Make sure nothing is called
        _running_progress(tc_map, fm, [future], 1)
        tc_prog.assert_not_called()
        tc_state.assert_not_called()
        tc_results.assert_not_called()
        fm_progress.assert_not_called()
        fm_results.assert_not_called()

        # Running should report progress (function is mocked)
        tc0._TestCase__progress = TestCase.Progress.RUNNING
        _running_progress(tc_map, fm, [future], 1)
        tc_prog.assert_not_called()
        tc_state.assert_not_called()
        tc_results.assert_not_called()
        fm_progress.assert_called_with(tc0)
        fm_results.assert_not_called()
        fm_progress.reset_mock()

        # Failure of tc0 should trigger tc2 to cancel
        tc0._TestCase__progress = TestCase.Progress.FINISHED
        tc0._TestCase__state = TestCase.Result.ERROR
        tc1._TestCase__progress = TestCase.Progress.WAITING
        _running_progress(tc_map, fm, [future], 1)
        tc_prog.assert_called_with(TestCase.Progress.FINISHED)
        tc_state.assert_called_with(TestCase.Result.SKIP)
        tc_results.assert_called_with({tc1.name(): TestCase.Data(TestCase.Result.SKIP, 0, '', f"Max failures of 1 exceeded.", ['max failures reached'])})
        fm_progress.assert_not_called()
        fm_results.assert_called_with(tc1)

class TestRun(unittest.TestCase):
    ANY = 42

    class IN(object):
        def __init__(self, value):
            self.value = value

    def setUp(self):
        r_state_mock = mock.patch('moosetools.moosetest.base.Formatter.formatRunnerState')
        r_results_mock = mock.patch('moosetools.moosetest.base.Formatter.formatRunnerResult')
        d_state_mock = mock.patch('moosetools.moosetest.base.Formatter.formatDifferState')
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
                self.assertIn(key, call.kwargs)
            elif isinstance(value, TestRun.IN):
                self.assertIn(value.value, call.kwargs[key])
            else:
                self.assertEqual(call.kwargs[key], value)

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
        self.assertCall(self._r_state, name='Andrew', state=TestCase.Result.PASS, reasons=None, percent=100, duration=TestRun.ANY)
        self.assertCall(self._r_results, name='Andrew', state=TestCase.Result.PASS, reasons=None, percent=100, duration=TestRun.ANY, returncode=2011, stdout=TestRun.IN('runner stdout'), stderr=TestRun.IN('runner stderr'))

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
        self.assertCall(self._r_state, name='Andrew', state=TestCase.Result.ERROR, reasons=None, percent=100, duration=TestRun.ANY)
        self.assertCall(self._r_results, name='Andrew', state=TestCase.Result.ERROR, reasons=None, percent=100, duration=TestRun.ANY, returncode=2011, stdout='', stderr=TestRun.IN('runner error\n'))

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
        self.assertCall(self._r_state, name='Andrew', state=TestCase.Result.EXCEPTION, reasons=None, percent=100, duration=TestRun.ANY)
        self.assertCall(self._r_results, name='Andrew', state=TestCase.Result.EXCEPTION, reasons=None, percent=100, duration=TestRun.ANY, returncode=None, stdout='', stderr=TestRun.IN('runner raise\n'))

        # TIMEOUT
        self.resetMockObjects()
        r.setValue('raise', False)
        r.setValue('sleep', 1)
        rcode = run([[r]], tuple(), fm, None, 0.5)
        self.assertEqual(rcode, 1)
        self._r_state.assert_called_once()
        self._r_results.assert_called_once()
        self._d_state.assert_not_called()
        self._d_results.assert_not_called()
        self._complete.assert_called_once()
        self.assertCall(self._r_state, name='Andrew', state=TestCase.Result.TIMEOUT, reasons=['max time (0.5) exceeded'], percent=100, duration=TestRun.ANY)
        self.assertCall(self._r_results, name='Andrew', state=TestCase.Result.TIMEOUT, reasons=['max time (0.5) exceeded'], percent=100, duration=TestRun.ANY, returncode=None, stdout='', stderr=TestRun.IN(''))

    def testRunnerWithController(self):
        c = TestController(stdout=True, stderr=True)
        r = make_runner(TestRunner, (c,), name='Andrew')
        fm = Formatter()

        # PASS
        rcode = run([[r]], (c,), fm)
        self.assertEqual(rcode, 0)
        self._r_state.assert_called_once()
        self._r_results.assert_called_once()
        self._d_state.assert_not_called()
        self._d_results.assert_not_called()
        self._complete.assert_called_once()
        self.assertCall(self._r_state, name='Andrew', state=TestCase.Result.PASS, reasons=None, percent=100, duration=TestRun.ANY)
        self.assertCall(self._r_results, name='Andrew', state=TestCase.Result.PASS, reasons=None, percent=100, duration=TestRun.ANY, stdout=TestRun.IN('controller stdout'), stderr=TestRun.IN('controller stderr'))

        # ERROR, CONTROLLER
        self.resetMockObjects()
        c.setValue('error', True)
        c.setValue('stderr', False)
        c.setValue('stdout', False)
        rcode = run([[r]], (c,), fm)
        self.assertEqual(rcode, 1)
        self._r_state.assert_called_once()
        self._r_results.assert_called_once()
        self._d_state.assert_not_called()
        self._d_results.assert_not_called()
        self._complete.assert_called_once()
        self.assertCall(self._r_state, name='Andrew', state=TestCase.Result.FATAL, reasons=None, percent=100, duration=TestRun.ANY)
        self.assertCall(self._r_results, name='Andrew', state=TestCase.Result.FATAL, reasons=None, percent=100, duration=TestRun.ANY, returncode=None, stdout='', stderr=TestRun.IN('An error occurred, on the controller'))

        # ERROR, RUNNER (during execution of Controller)
        self.resetMockObjects()
        c.setValue('error', False)
        with mock.patch('moosetools.moosetest.base.Runner.status', return_value=1):
            rcode = run([[r]], (c,), fm)
        self.assertEqual(rcode, 1)
        self._r_state.assert_called_once()
        self._r_results.assert_called_once()
        self._d_state.assert_not_called()
        self._d_results.assert_not_called()
        self._complete.assert_called_once()
        self.assertCall(self._r_state, name='Andrew', state=TestCase.Result.FATAL, reasons=None, percent=100, duration=TestRun.ANY)
        self.assertCall(self._r_results, name='Andrew', state=TestCase.Result.FATAL, reasons=None, percent=100, duration=TestRun.ANY, returncode=None, stdout='', stderr=TestRun.IN('An error occurred, on the object'))

        # EXCEPTION
        self.resetMockObjects()
        c.setValue('error', False)
        c.setValue('raise', True)
        rcode = run([[r]], (c,), fm)
        self.assertEqual(rcode, 1)
        self._r_state.assert_called_once()
        self._r_results.assert_called_once()
        self._d_state.assert_not_called()
        self._d_results.assert_not_called()
        self._complete.assert_called_once()
        self.assertCall(self._r_state, name='Andrew', state=TestCase.Result.FATAL, reasons=None, percent=100, duration=TestRun.ANY)
        self.assertCall(self._r_results, name='Andrew', state=TestCase.Result.FATAL, reasons=None, percent=100, duration=TestRun.ANY, returncode=None, stdout='', stderr=TestRun.IN('An exception occurred'))

        # TIMEOUT (because of Controller)
        self.resetMockObjects()
        c.setValue('raise', False)
        c.setValue('sleep', 1)
        rcode = run([[r]], (c,), fm, None, 0.5)
        self.assertEqual(rcode, 1)
        self._r_state.assert_called_once()
        self._r_results.assert_called_once()
        self._d_state.assert_not_called()
        self._d_results.assert_not_called()
        self._complete.assert_called_once()
        self.assertCall(self._r_state, name='Andrew', state=TestCase.Result.TIMEOUT, reasons=['max time (0.5) exceeded'], percent=100, duration=TestRun.ANY)
        self.assertCall(self._r_results, name='Andrew', state=TestCase.Result.TIMEOUT, reasons=['max time (0.5) exceeded'], percent=100, duration=TestRun.ANY, returncode=None, stdout='', stderr='')

        # SKIP
        self.resetMockObjects()
        c.setValue('skip', True)
        c.setValue('sleep', 0)
        rcode = run([[r]], (c,), fm)
        self.assertEqual(rcode, 0)
        self._r_state.assert_called_once()
        self._r_results.assert_called_once()
        self._d_state.assert_not_called()
        self._d_results.assert_not_called()
        self._complete.assert_called_once()
        self.assertCall(self._r_state, name='Andrew', state=TestCase.Result.SKIP, reasons=['a reason'], percent=100, duration=TestRun.ANY)
        self.assertCall(self._r_results, name='Andrew', state=TestCase.Result.SKIP, reasons=['a reason'], percent=100, duration=TestRun.ANY, returncode=None, stdout='', stderr=TestRun.IN(''))


    def testRunnerWithDiffers(self):
        d0 = make_differ(TestDiffer, name='a', stderr=True)
        d1 = make_differ(TestDiffer, name='b', stdout=True)
        r = make_runner(TestRunner, name='Andrew', differs=(d0,d1))
        fm = Formatter()

        # PASS
        rcode = run([[r]], tuple(), fm)
        self.assertEqual(rcode, 0)
        self._r_state.assert_called_once()
        self._r_results.assert_called_once()
        self.assertEqual(self._d_state.call_count, 2)
        self.assertEqual(self._d_results.call_count, 2)
        self._complete.assert_called_once()
        self.assertCall(self._r_state, name='Andrew', state=TestCase.Result.PASS, reasons=None, percent=100, duration=TestRun.ANY)
        self.assertCall(self._r_results, name='Andrew', state=TestCase.Result.PASS, reasons=None, percent=100, duration=TestRun.ANY, stdout='', stderr='')

        self.assertCall(self._d_state.call_args_list[0], name='a', state=TestCase.Result.PASS, reasons=None, percent=100, duration=TestRun.ANY)
        self.assertCall(self._d_state.call_args_list[1], name='b', state=TestCase.Result.PASS, reasons=None, percent=100, duration=TestRun.ANY)

        self.assertCall(self._d_results.call_args_list[0], name='a', state=TestCase.Result.PASS, reasons=None, percent=100, duration=TestRun.ANY, stdout='', stderr=TestRun.IN('differ stderr'))
        self.assertCall(self._d_results.call_args_list[1], name='b', state=TestCase.Result.PASS, reasons=None, percent=100, duration=TestRun.ANY, stdout=TestRun.IN('differ stdout'), stderr='')

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
        self.assertCall(self._r_state, name='Andrew', state=TestCase.Result.DIFF, reasons=None, percent=100, duration=TestRun.ANY)
        self.assertCall(self._r_results, name='Andrew', state=TestCase.Result.PASS, reasons=None, percent=100, duration=TestRun.ANY, stdout='', stderr='')

        self.assertCall(self._d_state.call_args_list[0], name='a', state=TestCase.Result.DIFF, reasons=None, percent=100, duration=TestRun.ANY)
        self.assertCall(self._d_state.call_args_list[1], name='b', state=TestCase.Result.SKIP, reasons=['dependency'], percent=100, duration=TestRun.ANY)

        self.assertCall(self._d_results.call_args_list[0], name='a', state=TestCase.Result.DIFF, reasons=None, percent=100, duration=TestRun.ANY, stdout='', stderr=TestRun.IN('differ error'))
        self.assertCall(self._d_results.call_args_list[1], name='b', state=TestCase.Result.SKIP, reasons=None, percent=100, duration=TestRun.ANY, stdout='', stderr='')

#differs
#differs w/controllers

# max fails
# group skip
# return level

if __name__ == '__main__':
    unittest.main(module=__name__, verbosity=2, buffer=True)
