#!/usr/bin/env python3
import sys
import io
import time
import multiprocessing
import collections
import logging
import unittest
from unittest import mock
from moosetools.moosetest.base import make_runner, Runner, make_differ, Differ, TestCase, State, RedirectOutput

#class TestRunner(Runner):
#    def execute(self):
#        return TestCase.Result.PASS, dict()

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

    @mock.patch("moosetools.moosetest.base.Runner.execute")
    def testExecuteObject_Runner(self, exc):

        r = make_runner(Runner, name='a')
        tc = TestCase(runner=r)

        # No error, no output
        exc.return_value = 1980
        out = tc._executeObject(r)
        gold = TestCase.Data(TestCase.Result.PASS, 1980, '', '', None)
        self.assertEqual(out, gold)

        # No error, with stdout and stderr
        def side_effect():
            logging.error('log error')
            print('print text')
            return 1980

        exc.side_effect = side_effect
        out = tc._executeObject(r)
        gold = TestCase.Data(TestCase.Result.PASS, 1980, 'print text\n', 'ERROR:root:log error\n', None)
        self.assertEqual(out, gold)

        # Error
        def side_effect():
            r.error('log error')
            print('print text')
            return 1980

        exc.side_effect = side_effect
        out = tc._executeObject(r)
        self.assertEqual(out.state, TestCase.Result.ERROR)
        self.assertEqual(out.returncode, 1980)
        self.assertEqual(out.stdout, 'print text\n')
        self.assertIn('log error', out.stderr)
        self.assertIn("An error occurred during execution of the 'a' object.", out.stderr)
        self.assertEqual(out.reasons, None)

        # Exception
        def side_effect():
            print('print text')
            raise Exception("no worky")
            return 1980

        exc.side_effect = side_effect
        out = tc._executeObject(r)
        self.assertEqual(out.state, TestCase.Result.EXCEPTION)
        self.assertEqual(out.returncode, None)
        self.assertEqual(out.stdout, 'print text\n')
        self.assertIn('no worky', out.stderr)
        self.assertIn("An exception occurred during execution of the 'a' object.", out.stderr)
        self.assertEqual(out.reasons, None)

        # Exception during reset
        def side_effect():
            print('print text')
            raise Execption("reset failed")
        with mock.patch("moosetools.moosetest.base.Runner.reset") as reset:
            reset.side_effect = side_effect
            out = tc._executeObject(r)
        self.assertEqual(out.state, TestCase.Result.FATAL)
        self.assertEqual(out.returncode, None)
        self.assertEqual(out.stdout, 'print text\n')
        self.assertIn('reset failed', out.stderr)
        self.assertIn("An exception occurred while calling the `reset` method of the 'a' object.", out.stderr)
        self.assertEqual(out.reasons, None)



        #with mock.patch("moosetools.moosetest.base.Runner.execute") as exc:
        #    exc.return_value = TestCase.Result.PASS, dict()
        #    tc._executeObject(r)








if __name__ == '__main__':
    unittest.main(module=__name__, verbosity=2)
