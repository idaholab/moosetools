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
import io
import time
import multiprocessing
import collections
import logging
import unittest
import uuid
from unittest import mock
from moosetools.moosetest.base import make_runner, Runner, make_differ, Differ
from moosetools.moosetest.base import Controller, Formatter, TestCase, State, RedirectOutput

# I do not want the tests directory to be packages with __init__.py, so load from file
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from _helpers import TestController, TestRunner, TestDiffer


class TestState(unittest.TestCase):
    def testDefault(self):
        class MarcoPolo(State):
            MARCO = (10, 0, 'MARCO', ('grey_82', ))
            POLO = (11, 1, 'POLO', ('white', 'red_1'))

        m = MarcoPolo.MARCO
        self.assertEqual(m.value, 10)
        self.assertEqual(m.level, 0)
        self.assertEqual(m.text, 'MARCO')
        self.assertEqual(m.color, ('grey_82', ))

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
        self.assertIn("test print\n", out.stdout)
        self.assertIn("test log\n", out.stderr)

        # Without logging configured, this adds a handler
        logging.basicConfig()
        l = logging.getLogger()
        with RedirectOutput() as out:
            print("test print")
            l.error("test log")
        self.assertIn("test print\n", out.stdout)
        self.assertIn("test log\n", out.stderr)


class TestTestCase(unittest.TestCase):
    def test_unique_id(self):
        tc0 = TestCase(runner=Runner(name='a'))
        self.assertIsInstance(tc0.unique_id, uuid.UUID)

    def testCounts(self):
        TestCase.__TOTAL__ = 0
        TestCase.__FINISHED__ = 0
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
        time.sleep(0.5)
        self.assertTrue(tc.time > 0.5)  # waiting time

        tc.setProgress(TestCase.Progress.RUNNING)
        self.assertEqual(tc.progress, TestCase.Progress.RUNNING)
        self.assertTrue(not tc.waiting)
        self.assertTrue(tc.running)
        self.assertTrue(not tc.finished)
        self.assertTrue(tc.time < 0.01)
        time.sleep(0.5)
        self.assertTrue(tc.time > 0.5)  # running time

        tc.setProgress(TestCase.Progress.FINISHED)
        self.assertEqual(tc.progress, TestCase.Progress.FINISHED)
        self.assertTrue(not tc.waiting)
        self.assertTrue(not tc.running)
        self.assertTrue(tc.finished)
        self.assertTrue(tc.time > 0.5)
        t = tc.time
        time.sleep(0.5)
        self.assertEqual(tc.time, t)  # execute time (should not change)

        tc.setProgress("wrong")
        self.assertEqual(tc.progress, TestCase.Progress.FINISHED)
        self.assertEqual(tc.state, TestCase.Result.FATAL)
        r = tc.results
        self.assertEqual(r['a'].state, TestCase.Result.FATAL)
        self.assertEqual(r['a'].returncode, None)
        self.assertEqual(r['a'].stdout, '')
        self.assertIn("The supplied progress must be of type `TestCase.Progress`.", r['a'].stderr)
        self.assertEqual(r['a'].reasons, None)
        self.assertEqual(tc.progress, TestCase.Progress.FINISHED)
        self.assertEqual(tc.state, TestCase.Result.FATAL)

    def testSetState(self):
        tc = TestCase(runner=Runner(name='a'))
        self.assertIsNone(tc.state)

        tc.setState(TestCase.Result.PASS)
        self.assertIsNotNone(tc.state)
        self.assertEqual(tc.state, TestCase.Result.PASS)

        tc.setState("wrong")
        r = tc.results
        self.assertEqual(tc.progress, TestCase.Progress.FINISHED)
        self.assertEqual(tc.state, TestCase.Result.FATAL)
        self.assertEqual(r['a'].state, TestCase.Result.FATAL)
        self.assertEqual(r['a'].returncode, None)
        self.assertEqual(r['a'].stdout, '')
        self.assertIn("The supplied state must be of type `TestCase.Result`.", r['a'].stderr)
        self.assertEqual(r['a'].reasons, None)
        self.assertEqual(tc.state, TestCase.Result.FATAL)

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
        obj.setValue('stdout', True)
        obj.setValue('stderr', True)
        out = tc._executeObject(obj)
        self.assertEqual(out.state, TestCase.Result.PASS)
        self.assertEqual(out.returncode, 2011)
        self.assertEqual(out.stdout, 'runner stdout\n')
        self.assertIn('runner stderr\n', out.stderr)
        self.assertEqual(out.reasons, None)

        # Error
        obj.setValue('error', True)
        out = tc._executeObject(obj)
        self.assertEqual(out.state, TestCase.Result.ERROR)
        self.assertEqual(out.returncode, 2011)
        self.assertEqual(out.stdout, 'runner stdout\n')
        self.assertIn('runner stderr\n', out.stderr)
        self.assertIn('runner error', out.stderr)
        self.assertIn("An error occurred during execution of the 'a' object.", out.stderr)
        self.assertEqual(out.reasons, None)

        # Exception
        obj.setValue('raise', True)
        out = tc._executeObject(obj)
        self.assertEqual(out.state, TestCase.Result.EXCEPTION)
        self.assertEqual(out.returncode, None)
        self.assertEqual(out.stdout, 'runner stdout\n')
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
        self.assertIn("An exception occurred while calling the `reset` method of the 'a' object.",
                      out.stderr)
        self.assertEqual(out.reasons, None)

    def testExecuteObject_Differ(self):
        obj = make_differ(TestDiffer, name='a')
        r = make_runner(TestRunner, name='a', differs=(obj, ))
        tc = TestCase(runner=r)

        # No error, no output
        out = tc._executeObject(obj)
        self.assertEqual(out.state, TestCase.Result.PASS)
        self.assertEqual(out.returncode, 2013)
        self.assertEqual(out.stdout, '')
        self.assertEqual(out.stderr, '')
        self.assertEqual(out.reasons, None)

        # No error, with stdout and stderr
        obj.setValue('stdout', True)
        obj.setValue('stderr', True)
        out = tc._executeObject(obj)
        self.assertEqual(out.state, TestCase.Result.PASS)
        self.assertEqual(out.returncode, 2013)
        self.assertEqual(out.stdout, 'differ stdout\n')
        self.assertIn('differ stderr\n', out.stderr)
        self.assertEqual(out.reasons, None)

        # Error
        obj.setValue('error', True)
        out = tc._executeObject(obj)
        self.assertEqual(out.state, TestCase.Result.DIFF)
        self.assertEqual(out.returncode, 2013)
        self.assertEqual(out.stdout, 'differ stdout\n')
        self.assertIn('differ stderr\n', out.stderr)
        self.assertIn('differ error', out.stderr)
        self.assertIn("An error occurred during execution of the 'a' object.", out.stderr)
        self.assertEqual(out.reasons, None)

        # Exception
        obj.setValue('raise', True)
        out = tc._executeObject(obj)
        self.assertEqual(out.state, TestCase.Result.EXCEPTION)
        self.assertEqual(out.returncode, None)
        self.assertEqual(out.stdout, 'differ stdout\n')
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
        self.assertIn("An exception occurred while calling the `reset` method of the 'a' object.",
                      out.stderr)
        self.assertEqual(out.reasons, None)

    def testExecuteObject_Controller(self):

        ctrl = TestController()
        obj = make_runner(TestRunner, [
            ctrl,
        ], name='a')
        tc = TestCase(runner=obj, controllers=(ctrl, ))

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
        self.assertIn(
            "An exception occurred during execution of the TestController controller with 'a' object.",
            out.stderr)
        self.assertEqual(out.reasons, None)

        ctrl.setValue('raise', True)
        out = tc._executeObject(obj)
        self.assertEqual(out.state, TestCase.Result.FATAL)
        self.assertEqual(out.returncode, None)
        self.assertEqual(out.stdout, '')
        self.assertIn('raise', out.stderr)
        self.assertIn(
            "An exception occurred during execution of the TestController controller with 'a' object.",
            out.stderr)
        self.assertEqual(out.reasons, None)

        ctrl.setValue('raise', False)
        with mock.patch("moosetools.moosetest.base.Controller.status") as func:
            func.return_value = 1
            out = tc._executeObject(obj)
        self.assertEqual(out.state, TestCase.Result.FATAL)
        self.assertEqual(out.returncode, None)
        self.assertEqual(out.stdout, '')
        self.assertIn(
            "An error occurred, on the controller, during execution of the TestController controller with 'a' object.",
            out.stderr)
        self.assertEqual(out.reasons, None)

        with mock.patch("moosetools.moosetest.base.Runner.status") as func:
            func.return_value = 1
            out = tc._executeObject(obj)
        self.assertEqual(out.state, TestCase.Result.FATAL)
        self.assertEqual(out.returncode, None)
        self.assertEqual(out.stdout, '')
        self.assertIn(
            "An error occurred, on the object, during execution of the TestController controller with 'a' object.",
            out.stderr)
        self.assertEqual(out.reasons, None)

        ctrl.setValue('skip', True)
        out = tc._executeObject(obj)
        self.assertEqual(out.state, TestCase.Result.SKIP)
        self.assertEqual(out.returncode, None)
        self.assertEqual(out.stdout, '')
        self.assertEqual(out.stderr, '')
        self.assertEqual(out.reasons, ['a reason'])

    def testExecute(self):
        ct = TestController()
        dr = make_differ(TestDiffer, [ct], name='d')
        rr = make_runner(TestRunner, [ct], differs=(dr, ), name='r')

        tc = TestCase(runner=rr, controllers=(ct, ))

        # No error, no output
        s, r = tc.execute()
        self.assertEqual(s, TestCase.Result.PASS)
        self.assertEqual(list(r.keys()), ['r', 'd'])
        self.assertEqual(r['r'], TestCase.Data(TestCase.Result.PASS, 2011, '', '', None))
        self.assertEqual(r['d'], TestCase.Data(TestCase.Result.PASS, 2013, '', '', None))

        ## RUNNER ################################
        # Reset Exception, Runner
        with mock.patch("moosetools.moosetest.base.Runner.reset") as func:
            func.side_effect = Exception("runner reset raise")
            s, r = tc.execute()
        self.assertEqual(s, TestCase.Result.FATAL)
        self.assertEqual(list(r.keys()), ['r'])
        self.assertEqual(r['r'].state, TestCase.Result.FATAL)
        self.assertEqual(r['r'].returncode, None)
        self.assertEqual(r['r'].stdout, '')
        self.assertIn("An exception occurred while calling the `reset` method of the 'r' object.",
                      r['r'].stderr)
        self.assertIn("runner reset raise", r['r'].stderr)
        self.assertEqual(r['r'].reasons, None)

        # Reset Exception, Controller with Runner
        with mock.patch("moosetools.moosetest.base.Controller.reset") as func:
            func.side_effect = Exception("controller reset raise")
            s, r = tc.execute()
        self.assertEqual(s, TestCase.Result.FATAL)
        self.assertEqual(list(r.keys()), ['r'])
        self.assertEqual(r['r'].state, TestCase.Result.FATAL)
        self.assertEqual(r['r'].returncode, None)
        self.assertEqual(r['r'].stdout, '')
        self.assertIn(
            "An exception occurred during execution of the TestController controller with 'r' object.",
            r['r'].stderr)
        self.assertIn("controller reset raise", r['r'].stderr)
        self.assertEqual(r['r'].reasons, None)

        # Execute Exception, Controller with Runner
        ct.setValue('raise', True)
        s, r = tc.execute()
        self.assertEqual(s, TestCase.Result.FATAL)
        self.assertEqual(list(r.keys()), ['r'])
        self.assertEqual(r['r'].state, TestCase.Result.FATAL)
        self.assertEqual(r['r'].returncode, None)
        self.assertEqual(r['r'].stdout, '')
        self.assertIn(
            "An exception occurred during execution of the TestController controller with 'r' object.",
            r['r'].stderr)
        self.assertIn("controller raise", r['r'].stderr)
        self.assertEqual(r['r'].reasons, None)

        # Error Object, Controller with Runner
        ct.setValue('raise', False)
        with mock.patch("moosetools.moosetest.base.Runner.status") as func:
            func.return_value = 1
            s, r = tc.execute()
        self.assertEqual(s, TestCase.Result.FATAL)
        self.assertEqual(list(r.keys()), ['r'])
        self.assertEqual(r['r'].state, TestCase.Result.FATAL)
        self.assertEqual(r['r'].returncode, None)
        self.assertEqual(r['r'].stdout, '')
        self.assertIn(
            "An error occurred, on the object, during execution of the TestController controller with 'r' object.",
            r['r'].stderr)
        self.assertEqual(r['r'].reasons, None)

        # Skip, Controller with Runner
        ct.setValue('skip', True)
        s, r = tc.execute()
        self.assertEqual(s, TestCase.Result.SKIP)
        self.assertEqual(list(r.keys()), ['r'])
        self.assertEqual(r['r'].state, TestCase.Result.SKIP)
        self.assertEqual(r['r'].returncode, None)
        self.assertEqual(r['r'].stdout, '')
        self.assertEqual(r['r'].stderr, '')
        self.assertEqual(r['r'].reasons, ['a reason'])
        ct.setValue('skip', False)

        # Error on Runner
        rr.setValue('error', True)
        s, r = tc.execute()
        self.assertEqual(s, TestCase.Result.ERROR)
        self.assertEqual(list(r.keys()), ['r'])
        self.assertEqual(r['r'].state, TestCase.Result.ERROR)
        self.assertEqual(r['r'].returncode, 2011)
        self.assertEqual(r['r'].stdout, '')
        self.assertIn("runner error", r['r'].stderr)
        self.assertIn("An error occurred during execution of the 'r' object", r['r'].stderr)
        self.assertEqual(r['r'].reasons, None)
        rr.setValue('error', False)

        # Exception on Runner
        rr.setValue('raise', True)
        s, r = tc.execute()
        self.assertEqual(s, TestCase.Result.EXCEPTION)
        self.assertEqual(list(r.keys()), ['r'])
        self.assertEqual(r['r'].state, TestCase.Result.EXCEPTION)
        self.assertEqual(r['r'].returncode, None)
        self.assertEqual(r['r'].stdout, '')
        self.assertIn("runner raise", r['r'].stderr)
        self.assertIn("An exception occurred during execution of the 'r' object", r['r'].stderr)
        self.assertEqual(r['r'].reasons, None)
        rr.setValue('raise', False)

        ## DIFFER ################################
        # Reset Exception, Differ
        with mock.patch("moosetools.moosetest.base.Differ.reset") as func:
            func.side_effect = Exception("differ reset raise")
            s, r = tc.execute()
        self.assertEqual(s, TestCase.Result.FATAL)
        self.assertEqual(list(r.keys()), ['r', 'd'])
        self.assertEqual(r['r'].state, TestCase.Result.PASS)
        self.assertEqual(r['r'].returncode, 2011)
        self.assertEqual(r['r'].stdout, '')
        self.assertEqual(r['r'].stdout, '')
        self.assertEqual(r['r'].reasons, None)
        self.assertEqual(r['d'].state, TestCase.Result.FATAL)
        self.assertEqual(r['d'].returncode, None)
        self.assertEqual(r['d'].stdout, '')
        self.assertIn("An exception occurred while calling the `reset` method of the 'd' object.",
                      r['d'].stderr)
        self.assertIn("differ reset raise", r['d'].stderr)
        self.assertEqual(r['d'].reasons, None)

        # Reset Exception, Controller with Differ
        with mock.patch("moosetools.moosetest.base.Controller.reset") as func:
            func.side_effect = [None, Exception("controller reset raise")]
            s, r = tc.execute()
        self.assertEqual(list(r.keys()), ['r', 'd'])
        self.assertEqual(r['r'].state, TestCase.Result.PASS)
        self.assertEqual(r['r'].returncode, 2011)
        self.assertEqual(r['r'].stdout, '')
        self.assertEqual(r['r'].stdout, '')
        self.assertEqual(r['r'].reasons, None)
        self.assertEqual(r['d'].state, TestCase.Result.FATAL)
        self.assertEqual(r['d'].returncode, None)
        self.assertEqual(r['d'].stdout, '')
        self.assertIn(
            "An exception occurred during execution of the TestController controller with 'd' object.",
            r['d'].stderr)
        self.assertIn("controller reset raise", r['d'].stderr)
        self.assertEqual(r['d'].reasons, None)

        # Execute Exception, Controller with Differ
        ct.setValue('raise', True)
        ct.setValue('object_name', 'd')
        s, r = tc.execute()
        self.assertEqual(list(r.keys()), ['r', 'd'])
        self.assertEqual(r['r'].state, TestCase.Result.PASS)
        self.assertEqual(r['r'].returncode, 2011)
        self.assertEqual(r['r'].stdout, '')
        self.assertEqual(r['r'].stdout, '')
        self.assertEqual(r['r'].reasons, None)
        self.assertEqual(r['d'].state, TestCase.Result.FATAL)
        self.assertEqual(r['d'].returncode, None)
        self.assertEqual(r['d'].stdout, '')
        self.assertIn(
            "An exception occurred during execution of the TestController controller with 'd' object.",
            r['d'].stderr)
        self.assertIn("controller raise", r['d'].stderr)
        self.assertEqual(r['d'].reasons, None)
        ct.setValue('raise', False)
        ct.setValue('object_name', None)

        # Error Object, Controller with Differ
        with mock.patch("moosetools.moosetest.base.Differ.status") as func:
            func.return_value = 1
            s, r = tc.execute()
        self.assertEqual(list(r.keys()), ['r', 'd'])
        self.assertEqual(r['r'].state, TestCase.Result.PASS)
        self.assertEqual(r['r'].returncode, 2011)
        self.assertEqual(r['r'].stdout, '')
        self.assertEqual(r['r'].stdout, '')
        self.assertEqual(r['r'].reasons, None)
        self.assertEqual(r['d'].state, TestCase.Result.FATAL)
        self.assertEqual(r['d'].returncode, None)
        self.assertEqual(r['d'].stdout, '')
        self.assertIn(
            "An error occurred, on the object, during execution of the TestController controller with 'd' object.",
            r['d'].stderr)
        self.assertEqual(r['d'].reasons, None)

        # Skip, Controller with Differ
        ct.setValue('skip', True)
        ct.setValue('object_name', 'd')
        s, r = tc.execute()
        self.assertEqual(s, TestCase.Result.PASS)
        self.assertEqual(list(r.keys()), ['r', 'd'])
        self.assertEqual(r['r'].state, TestCase.Result.PASS)
        self.assertEqual(r['r'].returncode, 2011)
        self.assertEqual(r['r'].stdout, '')
        self.assertEqual(r['r'].stdout, '')
        self.assertEqual(r['r'].reasons, None)
        self.assertEqual(r['d'].state, TestCase.Result.SKIP)
        self.assertEqual(r['d'].returncode, None)
        self.assertEqual(r['d'].stdout, '')
        self.assertEqual(r['d'].stderr, '')
        self.assertEqual(r['d'].reasons, ['a reason'])
        ct.setValue('skip', False)
        ct.setValue('object_name', None)

        # Error on Differ
        dr.setValue('error', True)
        s, r = tc.execute()
        self.assertEqual(s, TestCase.Result.DIFF)
        self.assertEqual(list(r.keys()), ['r', 'd'])
        self.assertEqual(r['r'].state, TestCase.Result.PASS)
        self.assertEqual(r['r'].returncode, 2011)
        self.assertEqual(r['r'].stdout, '')
        self.assertEqual(r['r'].stdout, '')
        self.assertEqual(r['r'].reasons, None)
        self.assertEqual(r['d'].state, TestCase.Result.DIFF)
        self.assertEqual(r['d'].returncode, 2013)
        self.assertEqual(r['d'].stdout, '')
        self.assertIn("differ error", r['d'].stderr)
        self.assertIn("An error occurred during execution of the 'd' object", r['d'].stderr)
        self.assertEqual(r['d'].reasons, None)
        dr.setValue('error', False)

        # Exception on Differ
        dr.setValue('raise', True)
        s, r = tc.execute()
        self.assertEqual(s, TestCase.Result.EXCEPTION)
        self.assertEqual(list(r.keys()), ['r', 'd'])
        self.assertEqual(r['r'].state, TestCase.Result.PASS)
        self.assertEqual(r['r'].returncode, 2011)
        self.assertEqual(r['r'].stdout, '')
        self.assertEqual(r['r'].stdout, '')
        self.assertEqual(r['r'].reasons, None)
        self.assertEqual(r['d'].state, TestCase.Result.EXCEPTION)
        self.assertEqual(r['d'].returncode, None)
        self.assertEqual(r['d'].stdout, '')
        self.assertIn("differ raise", r['d'].stderr)
        self.assertIn("An exception occurred during execution of the 'd' object", r['d'].stderr)
        self.assertEqual(r['d'].reasons, None)

    def testSetResults(self):
        ct = TestController()
        dr = make_differ(TestDiffer, [ct], name='d')
        rr = make_runner(TestRunner, [ct], differs=(dr, ), name='r')
        tc = TestCase(runner=rr, controllers=(ct, ))

        # Wrong type
        tc.setResults('wrong')
        self.assertEqual(tc.state, TestCase.Result.FATAL)
        r = tc.results
        self.assertEqual(r['r'].state, TestCase.Result.FATAL)
        self.assertEqual(r['r'].returncode, None)
        self.assertEqual(r['r'].stdout, '')
        self.assertIn("The supplied result must be of type `dict`.", r['r'].stderr)
        self.assertEqual(r['r'].reasons, None)

        tc.setResults({'r': 'wrong'})
        self.assertEqual(tc.state, TestCase.Result.FATAL)
        r = tc.results
        self.assertEqual(r['r'].state, TestCase.Result.FATAL)
        self.assertEqual(r['r'].returncode, None)
        self.assertEqual(r['r'].stdout, '')
        self.assertIn("The supplied result values must be of type `TestCase.Data`.", r['r'].stderr)
        self.assertEqual(r['r'].reasons, None)

        tc.setResults({'wrong': TestCase.Data()})
        self.assertEqual(tc.state, TestCase.Result.FATAL)
        r = tc.results
        self.assertEqual(r['r'].state, TestCase.Result.FATAL)
        self.assertEqual(r['r'].returncode, None)
        self.assertEqual(r['r'].stdout, '')
        self.assertIn(
            "The supplied result keys must be the names of the `Runner` or `Differ` object(s).",
            r['r'].stderr)
        self.assertEqual(r['r'].reasons, None)

        tc.setResults({'r': TestCase.Data(TestCase.Result.PASS, None, 'out', 'err', None)})
        self.assertEqual(tc.state, TestCase.Result.FATAL)
        r = tc.results
        self.assertEqual(r['r'].state, TestCase.Result.PASS)
        self.assertEqual(r['r'].returncode, None)
        self.assertEqual(r['r'].stdout, 'out')
        self.assertEqual(r['r'].stderr, 'err')
        self.assertEqual(r['r'].reasons, None)


if __name__ == '__main__':
    unittest.main(module=__name__, verbosity=2, buffer=True)
