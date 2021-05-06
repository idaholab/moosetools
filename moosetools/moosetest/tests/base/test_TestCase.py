#!/usr/bin/env python3
import sys
import io
import time
import multiprocessing
import collections
import logging
import unittest
from unittest import mock
from moosetools.moosetest.base import make_runner, Runner, make_differ, Differ, Controller, TestCase, State, RedirectOutput

class TestController(Controller):
    @staticmethod
    def validParams():
        params = Controller.validParams()
        params.set('prefix', 'ctrl')
        return params

    @staticmethod
    def validObjectParams():
        params = Controller.validObjectParams()
        params.add('platform')
        return params

    def __init__(self, *args, **kwargs):
        Controller.__init__(self, *args, **kwargs)
        self._skip = False
        self._print = False
        self._stderr = False
        self._error = False
        self._raise = False

    def execute(self, *args):
        if self._skip:
            self.skip("a reason")
        if self._print:
            print("controller print")
        if self._stderr:
            logging.error("controller stderr")
        if self._error:
            self.error("controller error")
        if self._raise:
            raise Exception("controller raise")
        return 1980

class TestRunner(Runner):
    def __init__(self, *args, **kwargs):
        Runner.__init__(self, *args, **kwargs)
        self._print = False
        self._stderr = False
        self._error = False
        self._raise = False

    def execute(self, *args):
        if self._print:
            print("runner print")
        if self._stderr:
            logging.error("runner stderr")
        if self._error:
            self.error("runner error")
        if self._raise:
            raise Exception("runner raise")
        return 2011

class TestDiffer(Differ):
    def __init__(self, *args, **kwargs):
        Differ.__init__(self, *args, **kwargs)
        self._print = False
        self._stderr = False
        self._error = False
        self._raise = False

    def execute(self, *args):
        if self._print:
            print("differ print")
        if self._stderr:
            logging.error("differ stderr")
        if self._error:
            self.error("differ error")
        if self._raise:
            raise Exception("differ raise")
        return 2013

class TestState(unittest.TestCase):
    def testDefault(self):
        class MarcoPolo(State):
            MARCO  = (10, 0, 'MARCO', ('grey_82',))
            POLO  = (11, 1, 'POLO', ('white', 'red_1'))

        m = MarcoPolo.MARCO
        self.assertEqual(m.value, 10)
        self.assertEqual(m.level, 0)
        self.assertEqual(m.text, 'MARCO')
        self.assertEqual(m.color, ('grey_82',))

        self.assertEqual(m.display, '\x1b[38;5;252mMARCO\x1b[0m')
        self.assertEqual(m.format('foo'), '\x1b[38;5;252mfoo\x1b[0m')


class TestRedirectOutput(unittest.TestCase):
    def testSysRedirect(self):
        out = collections.defaultdict(io.StringIO)
        new = RedirectOutput.SysRedirect(out)
        sys.stdout = new
        print("testing")
        self.assertEqual("testing\n", out[multiprocessing.current_process().pid].getvalue())

    def testRedirectOutput(self):

        # Without logging configured
        with RedirectOutput() as out:
            print("test print")
            logging.error("test log")
        self.assertEqual("test print\n", out.stdout)
        self.assertEqual("ERROR:root:test log\n", out.stderr)

        # Without logging configured, this adds a handler
        logging.basicConfig()
        l = logging.getLogger()
        with RedirectOutput() as out:
            print("test print")
            l.error("test log")
        self.assertEqual("test print\n", out.stdout)
        self.assertEqual("test log\n", out.stderr)

class TestTestCase(unittest.TestCase):
    def testCounts(self):
        self.assertEqual(TestCase.__TOTAL__, 0)
        self.assertEqual(TestCase.__FINISHED__, 0)

        tc0 = TestCase(runner=Runner(name='a'))
        self.assertEqual(tc0.__TOTAL__, 1)
        self.assertEqual(TestCase.__TOTAL__, 1)
        self.assertEqual(tc0.__FINISHED__, 0)
        self.assertEqual(TestCase.__FINISHED__, 0)

        tc1 = TestCase(runner=Runner(name='b'))
        self.assertEqual(tc0.__TOTAL__, 2)
        self.assertEqual(tc0.__FINISHED__, 0)
        self.assertEqual(tc1.__TOTAL__, 2)
        self.assertEqual(tc1.__FINISHED__, 0)
        self.assertEqual(TestCase.__TOTAL__, 2)
        self.assertEqual(TestCase.__FINISHED__, 0)

        tc0.setProgress(TestCase.Progress.FINISHED)
        self.assertEqual(tc0.__TOTAL__, 2)
        self.assertEqual(tc0.__FINISHED__, 1)
        self.assertEqual(tc1.__TOTAL__, 2)
        self.assertEqual(tc1.__FINISHED__, 1)
        self.assertEqual(TestCase.__TOTAL__, 2)
        self.assertEqual(TestCase.__FINISHED__, 1)

    def testProgessAndTime(self):
        tc = TestCase(runner=Runner(name='a'))

        self.assertEqual(tc.progress, TestCase.Progress.WAITING)
        self.assertTrue(tc.waiting)
        self.assertTrue(not tc.running)
        self.assertTrue(not tc.finished)
        time.sleep(0.5);
        self.assertTrue(tc.time > 0.5) # waiting time

        tc.setProgress(TestCase.Progress.RUNNING)
        self.assertEqual(tc.progress, TestCase.Progress.RUNNING)
        self.assertTrue(not tc.waiting)
        self.assertTrue(tc.running)
        self.assertTrue(not tc.finished)
        self.assertTrue(tc.time < 0.01)
        time.sleep(0.5);
        self.assertTrue(tc.time > 0.5) # running time

        tc.setProgress(TestCase.Progress.FINISHED)
        self.assertEqual(tc.progress, TestCase.Progress.FINISHED)
        self.assertTrue(not tc.waiting)
        self.assertTrue(not tc.running)
        self.assertTrue(tc.finished)
        self.assertTrue(tc.time > 0.5)
        t = tc.time
        time.sleep(0.5);
        self.assertEqual(tc.time, t) # execute time (should not change)

    def testState(self):
        tc = TestCase(runner=Runner(name='a'))
        self.assertIsNone(tc.state)

        tc.setState(TestCase.Result.PASS)
        self.assertIsNotNone(tc.state)
        self.assertEqual(tc.state, TestCase.Result.PASS)

    def testExecuteObject_Runner(self):
        obj = make_runner(TestRunner, name='a')
        tc = TestCase(runner=obj)

        # No error, no output
        out = tc._executeObject(obj)
        self.assertEqual(out.state, TestCase.Result.PASS)
        self.assertEqual(out.returncode, 2011)
        self.assertEqual(out.stdout, '')
        self.assertEqual(out.stderr, '')
        self.assertEqual(out.reasons, None)

        # No error, with stdout and stderr
        obj._print = True
        obj._stderr = True
        out = tc._executeObject(obj)
        self.assertEqual(out.state, TestCase.Result.PASS)
        self.assertEqual(out.returncode, 2011)
        self.assertEqual(out.stdout, 'runner print\n')
        self.assertIn('runner stderr\n', out.stderr)
        self.assertEqual(out.reasons, None)

        # Error
        obj._error = True
        out = tc._executeObject(obj)
        self.assertEqual(out.state, TestCase.Result.ERROR)
        self.assertEqual(out.returncode, 2011)
        self.assertEqual(out.stdout, 'runner print\n')
        self.assertIn('runner stderr\n', out.stderr)
        self.assertIn('runner error', out.stderr)
        self.assertIn("An error occurred during execution of the 'a' object.", out.stderr)
        self.assertEqual(out.reasons, None)

        # Exception
        obj._raise = True
        out = tc._executeObject(obj)
        self.assertEqual(out.state, TestCase.Result.EXCEPTION)
        self.assertEqual(out.returncode, None)
        self.assertEqual(out.stdout, 'runner print\n')
        self.assertIn('runner stderr\n', out.stderr)
        self.assertIn('runner error', out.stderr)
        self.assertIn('runner raise', out.stderr)
        self.assertIn("An exception occurred during execution of the 'a' object.", out.stderr)
        self.assertEqual(out.reasons, None)

        # Exception during reset
        def side_effect():
            print('print text')
            raise Execption("reset failed")
        with mock.patch("moosetools.moosetest.base.Runner.reset") as reset:
            reset.side_effect = side_effect
            out = tc._executeObject(obj)
        self.assertEqual(out.state, TestCase.Result.FATAL)
        self.assertEqual(out.returncode, None)
        self.assertEqual(out.stdout, 'print text\n')
        self.assertIn('reset failed', out.stderr)
        self.assertIn("An exception occurred while calling the `reset` method of the 'a' object.", out.stderr)
        self.assertEqual(out.reasons, None)

    def testExecuteObject_Differ(self):
        obj = make_differ(TestDiffer, name='a')
        r = make_runner(TestRunner, name='a', differs=(obj,))
        tc = TestCase(runner=r)

        # No error, no output
        out = tc._executeObject(obj)
        self.assertEqual(out.state, TestCase.Result.PASS)
        self.assertEqual(out.returncode, 2013)
        self.assertEqual(out.stdout, '')
        self.assertEqual(out.stderr, '')
        self.assertEqual(out.reasons, None)

        # No error, with stdout and stderr
        obj._print = True
        obj._stderr = True
        out = tc._executeObject(obj)
        self.assertEqual(out.state, TestCase.Result.PASS)
        self.assertEqual(out.returncode, 2013)
        self.assertEqual(out.stdout, 'differ print\n')
        self.assertIn('differ stderr\n', out.stderr)
        self.assertEqual(out.reasons, None)

        # Error
        obj._error = True
        out = tc._executeObject(obj)
        self.assertEqual(out.state, TestCase.Result.DIFF)
        self.assertEqual(out.returncode, 2013)
        self.assertEqual(out.stdout, 'differ print\n')
        self.assertIn('differ stderr\n', out.stderr)
        self.assertIn('differ error', out.stderr)
        self.assertIn("An error occurred during execution of the 'a' object.", out.stderr)
        self.assertEqual(out.reasons, None)

        # Exception
        obj._raise = True
        out = tc._executeObject(obj)
        self.assertEqual(out.state, TestCase.Result.EXCEPTION)
        self.assertEqual(out.returncode, None)
        self.assertEqual(out.stdout, 'differ print\n')
        self.assertIn('differ stderr\n', out.stderr)
        self.assertIn('differ error', out.stderr)
        self.assertIn('differ raise', out.stderr)
        self.assertIn("An exception occurred during execution of the 'a' object.", out.stderr)
        self.assertEqual(out.reasons, None)

        # Exception during reset
        def side_effect():
            print('print text')
            raise Execption("reset failed")
        with mock.patch("moosetools.moosetest.base.Differ.reset") as reset:
            reset.side_effect = side_effect
            out = tc._executeObject(obj)
        self.assertEqual(out.state, TestCase.Result.FATAL)
        self.assertEqual(out.returncode, None)
        self.assertEqual(out.stdout, 'print text\n')
        self.assertIn('reset failed', out.stderr)
        self.assertIn("An exception occurred while calling the `reset` method of the 'a' object.", out.stderr)
        self.assertEqual(out.reasons, None)

    def testExecuteObject_Controller(self):

        ctrl = TestController()
        obj = make_runner(TestRunner, [ctrl,], name='a')
        tc = TestCase(runner=obj, controllers=(ctrl,))

        # No error, no output
        out = tc._executeObject(obj)
        self.assertEqual(out.state, TestCase.Result.PASS)
        self.assertEqual(out.returncode, 2011)
        self.assertEqual(out.stdout, '')
        self.assertEqual(out.stderr, '')
        self.assertEqual(out.reasons, None)

        with mock.patch("moosetools.moosetest.base.Controller.reset") as func:
            func.side_effect = Exception("raise")
            out = tc._executeObject(obj)

        self.assertEqual(out.state, TestCase.Result.FATAL)
        self.assertEqual(out.returncode, None)
        self.assertEqual(out.stdout, '')
        self.assertIn('raise', out.stderr)
        self.assertIn("An exception occurred during execution of the TestController controller with 'a' object.", out.stderr)
        self.assertEqual(out.reasons, None)

        ctrl._raise = True
        out = tc._executeObject(obj)
        self.assertEqual(out.state, TestCase.Result.FATAL)
        self.assertEqual(out.returncode, None)
        self.assertEqual(out.stdout, '')
        self.assertIn('raise', out.stderr)
        self.assertIn("An exception occurred during execution of the TestController controller with 'a' object.", out.stderr)
        self.assertEqual(out.reasons, None)

        ctrl._raise = False
        with mock.patch("moosetools.moosetest.base.Controller.status") as func:
            func.return_value = 1
            out = tc._executeObject(obj)
        self.assertEqual(out.state, TestCase.Result.FATAL)
        self.assertEqual(out.returncode, None)
        self.assertEqual(out.stdout, '')
        self.assertIn("An error occurred, on the controller, during execution of the TestController controller with 'a' object.", out.stderr)
        self.assertEqual(out.reasons, None)

        with mock.patch("moosetools.moosetest.base.Runner.status") as func:
            func.return_value = 1
            out = tc._executeObject(obj)
        self.assertEqual(out.state, TestCase.Result.FATAL)
        self.assertEqual(out.returncode, None)
        self.assertEqual(out.stdout, '')
        self.assertIn("An error occurred, on the object, during execution of the TestController controller with 'a' object.", out.stderr)
        self.assertEqual(out.reasons, None)

        ctrl._skip = True
        out = tc._executeObject(obj)
        self.assertEqual(out.state, TestCase.Result.SKIP)
        self.assertEqual(out.returncode, None)
        self.assertEqual(out.stdout, '')
        self.assertEqual(out.stderr, '')
        self.assertEqual(out.reasons, ['a reason'])

    def testExecute(self):
        ct = TestController()
        dr = make_differ(TestDiffer, [ct], name='d')
        rr = make_runner(TestRunner, [ct], differs=(dr,), name='r')

        tc = TestCase(runner=rr, controllers=(ct,))

        s, r = tc.execute()
        self.assertEqual(s, TestCase.Result.PASS)
        self.assertEqual(list(r.keys()), ['r', 'd'])
        self.assertEqual(r['r'], TestCase.Data(TestCase.Result.PASS, 2011, '', '', None))
        self.assertEqual(r['d'], TestCase.Data(TestCase.Result.PASS, 2013, '', '', None))



if __name__ == '__main__':
    unittest.main(module=__name__, verbosity=2)
