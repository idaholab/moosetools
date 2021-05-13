#!/usr/bin/env python3
import unittest
from unittest import mock
import queue
import dataclasses
import logging
from moosetools.moosetest.base import make_runner, make_differ, TestCase, State
from moosetools.moosetest.runners import RunCommand
from moosetools.moosetest import run
from moosetools.moosetest.run import _execute_testcase, _execute_testcases

@dataclasses.dataclass
class PipeProxy(object):
    state: State = None
    result: dict = None

    def send(self, data):
        self.state = data[0]
        self.result = data[1]

    def close(self):
        pass

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
        self.assertEqual(data.returncode, 1)
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
        self.assertEqual(data.returncode,1)
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
        self.assertEqual(data.returncode, 0)
        self.assertEqual(data.stdout, "")
        self.assertIn("A previous", data.stderr)
        self.assertEqual(data.reasons, ['dependency'])

class TestRun(unittest.TestCase):
    def testProgress(self):
        r0 = make_runner(RunCommand, name='test0', command=('sleep', '2'))
        tc0 = TestCase(runner=r0)




    def test_run(self):

        r0 = make_runner(RunCommand, name='test0', command=('sleep', '0.2'))
        r1 = make_runner(RunCommand, name='test1', command=('sleep', '0.3'))

        tc0 = TestCase(runner=r0)
        tc1 = TestCase(runner=r1)

        tc_map = {tc0.getParam('_unique_id'):tc0, tc1.getParam('_unique_id'):tc1}


if __name__ == '__main__':
    unittest.main(module=__name__, verbosity=2)
