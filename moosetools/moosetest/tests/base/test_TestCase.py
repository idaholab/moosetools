#!/usr/bin/env python3
import sys
import io
import time
import multiprocessing
import collections
import logging
import unittest
from unittest import mock
from moosetools.moosetest.base import make_runner, Runner, make_differ, Differ
from moosetools.moosetest.base import Controller, Formatter, TestCase, State, RedirectOutput

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
        self._type = None

    def execute(self, obj, *args):
        if (self._type is None) or isinstance(obj, self._type):
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

        tc.setProgress("wrong")
        self.assertEqual(tc.progress, TestCase.Progress.FINISHED)
        self.assertEqual(tc.state, TestCase.Result.FATAL)
        r = tc.result
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
        r = tc.result
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
        self.assertIn("An exception occurred while calling the `reset` method of the 'r' object.", r['r'].stderr)
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
        self.assertIn("An exception occurred during execution of the TestController controller with 'r' object.", r['r'].stderr)
        self.assertIn("controller reset raise", r['r'].stderr)
        self.assertEqual(r['r'].reasons, None)

        # Execute Exception, Controller with Runner
        ct._raise = True
        s, r = tc.execute()
        self.assertEqual(s, TestCase.Result.FATAL)
        self.assertEqual(list(r.keys()), ['r'])
        self.assertEqual(r['r'].state, TestCase.Result.FATAL)
        self.assertEqual(r['r'].returncode, None)
        self.assertEqual(r['r'].stdout, '')
        self.assertIn("An exception occurred during execution of the TestController controller with 'r' object.", r['r'].stderr)
        self.assertIn("controller raise", r['r'].stderr)
        self.assertEqual(r['r'].reasons, None)

        # Error Object, Controller with Runner
        ct._raise = False
        with mock.patch("moosetools.moosetest.base.Runner.status") as func:
            func.return_value = 1
            s, r = tc.execute()
        self.assertEqual(s, TestCase.Result.FATAL)
        self.assertEqual(list(r.keys()), ['r'])
        self.assertEqual(r['r'].state, TestCase.Result.FATAL)
        self.assertEqual(r['r'].returncode, None)
        self.assertEqual(r['r'].stdout, '')
        self.assertIn("An error occurred, on the object, during execution of the TestController controller with 'r' object.", r['r'].stderr)
        self.assertEqual(r['r'].reasons, None)

        # Skip, Controller with Runner
        ct._skip = True
        s, r = tc.execute()
        self.assertEqual(s, TestCase.Result.SKIP)
        self.assertEqual(list(r.keys()), ['r'])
        self.assertEqual(r['r'].state, TestCase.Result.SKIP)
        self.assertEqual(r['r'].returncode, None)
        self.assertEqual(r['r'].stdout, '')
        self.assertEqual(r['r'].stderr, '')
        self.assertEqual(r['r'].reasons, ['a reason'])
        ct._skip = False

        # Error on Runner
        rr._error = True
        s, r = tc.execute()
        self.assertEqual(s, TestCase.Result.ERROR)
        self.assertEqual(list(r.keys()), ['r'])
        self.assertEqual(r['r'].state, TestCase.Result.ERROR)
        self.assertEqual(r['r'].returncode, 2011)
        self.assertEqual(r['r'].stdout, '')
        self.assertIn("runner error", r['r'].stderr)
        self.assertIn("An error occurred during execution of the 'r' object", r['r'].stderr)
        self.assertEqual(r['r'].reasons, None)
        rr._error = False

        # Exception on Runner
        rr._raise = True
        s, r = tc.execute()
        self.assertEqual(s, TestCase.Result.EXCEPTION)
        self.assertEqual(list(r.keys()), ['r'])
        self.assertEqual(r['r'].state, TestCase.Result.EXCEPTION)
        self.assertEqual(r['r'].returncode, None)
        self.assertEqual(r['r'].stdout, '')
        self.assertIn("runner raise", r['r'].stderr)
        self.assertIn("An exception occurred during execution of the 'r' object", r['r'].stderr)
        self.assertEqual(r['r'].reasons, None)
        rr._raise = False

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
        self.assertIn("An exception occurred while calling the `reset` method of the 'd' object.", r['d'].stderr)
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
        self.assertIn("An exception occurred during execution of the TestController controller with 'd' object.", r['d'].stderr)
        self.assertIn("controller reset raise", r['d'].stderr)
        self.assertEqual(r['d'].reasons, None)

        # Execute Exception, Controller with Differ
        ct._raise = True
        ct._type = Differ
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
        self.assertIn("An exception occurred during execution of the TestController controller with 'd' object.", r['d'].stderr)
        self.assertIn("controller raise", r['d'].stderr)
        self.assertEqual(r['d'].reasons, None)
        ct._raise = False
        ct._type = None

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
        self.assertIn("An error occurred, on the object, during execution of the TestController controller with 'd' object.", r['d'].stderr)
        self.assertEqual(r['d'].reasons, None)

        # Skip, Controller with Differ
        ct._skip = True
        ct._type = Differ
        s, r = tc.execute()
        self.assertEqual(s, TestCase.Result.SKIP)
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
        ct._skip = False
        ct._type = None

        # Error on Differ
        dr._error = True
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
        dr._error = False

        # Exception on Differ
        dr._raise = True
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

    def testSetResult(self):
        ct = TestController()
        dr = make_differ(TestDiffer, [ct], name='d')
        rr = make_runner(TestRunner, [ct], differs=(dr,), name='r')
        tc = TestCase(runner=rr, controllers=(ct,))

        # Wrong type
        tc.setResult('wrong')
        self.assertEqual(tc.state, TestCase.Result.FATAL)
        r = tc.result
        self.assertEqual(r['r'].state, TestCase.Result.FATAL)
        self.assertEqual(r['r'].returncode, None)
        self.assertEqual(r['r'].stdout, '')
        self.assertIn("The supplied result must be of type `dict`.", r['r'].stderr)
        self.assertEqual(r['r'].reasons, None)

        tc.setResult({'r':'wrong'})
        self.assertEqual(tc.state, TestCase.Result.FATAL)
        r = tc.result
        self.assertEqual(r['r'].state, TestCase.Result.FATAL)
        self.assertEqual(r['r'].returncode, None)
        self.assertEqual(r['r'].stdout, '')
        self.assertIn("The supplied result values must be of type `TestCase.Data`.", r['r'].stderr)
        self.assertEqual(r['r'].reasons, None)

        tc.setResult({'wrong':TestCase.Data()})
        self.assertEqual(tc.state, TestCase.Result.FATAL)
        r = tc.result
        self.assertEqual(r['r'].state, TestCase.Result.FATAL)
        self.assertEqual(r['r'].returncode, None)
        self.assertEqual(r['r'].stdout, '')
        self.assertIn("The supplied result keys must be the names of the `Runner` or `Differ` object(s).", r['r'].stderr)
        self.assertEqual(r['r'].reasons, None)

        tc.setResult({'r': TestCase.Data(TestCase.Result.PASS, None, 'out', 'err', None)})
        self.assertEqual(tc.state, TestCase.Result.FATAL)
        r = tc.result
        self.assertEqual(r['r'].state, TestCase.Result.PASS)
        self.assertEqual(r['r'].returncode, None)
        self.assertEqual(r['r'].stdout, 'out')
        self.assertEqual(r['r'].stderr, 'err')
        self.assertEqual(r['r'].reasons, None)

    @mock.patch("moosetools.moosetest.base.TestCase._printResult")
    @mock.patch("moosetools.moosetest.base.TestCase._printState")
    def testReportResults(self, pstate, presult):

        # Runner
        ct = TestController()
        rr = make_runner(TestRunner, [ct], name='r')
        tc = TestCase(runner=rr, controllers=(ct,))

        tc.setResult({'r':TestCase.Data(TestCase.Result.ERROR, None, 'out', 'err', None)})
        tc.setProgress(TestCase.Progress.FINISHED)
        tc.setState(TestCase.Result.PASS)
        tc.reportResult()

        pstate.assert_called_with(rr, tc.state, None)
        presult.assert_called_with(rr, tc.result['r'])

        # Differ
        dr = make_differ(TestDiffer, [ct], name='d')
        rr = make_runner(TestRunner, [ct], differs=(dr,), name='r')
        tc = TestCase(runner=rr, controllers=(ct,))
        tc.setProgress(TestCase.Progress.FINISHED)
        tc.setState(TestCase.Result.PASS)
        tc.setResult({'r':TestCase.Data(TestCase.Result.ERROR, None, 'r_out', 'r_err', None),
                      'd':TestCase.Data(TestCase.Result.TIMEOUT, None, 'd_out', 'd_err', None)})

        tc.reportResult()
        pstate.assert_called_with(dr, tc.result['d'].state, None)
        presult.assert_called_with(dr, tc.result['d'])

        # Errors
        ct = TestController()
        rr = make_runner(TestRunner, [ct], name='r')
        tc = TestCase(runner=rr, controllers=(ct,))
        tc.reportResult()
        self.assertEqual(tc.progress, TestCase.Progress.FINISHED)
        self.assertEqual(tc.state, TestCase.Result.FATAL)
        r = tc.result
        self.assertEqual(r['r'].state, TestCase.Result.FATAL)
        self.assertEqual(r['r'].returncode, None)
        self.assertEqual(r['r'].stdout, '')
        self.assertIn("The state has not been set via the `setState` method.", r['r'].stderr)
        self.assertEqual(r['r'].reasons, None)

        ct = TestController()
        rr = make_runner(TestRunner, [ct], name='r')
        tc = TestCase(runner=rr, controllers=(ct,))
        tc.setState(TestCase.Result.PASS)
        tc.reportResult()
        self.assertEqual(tc.progress, TestCase.Progress.FINISHED)
        self.assertEqual(tc.state, TestCase.Result.FATAL)
        r = tc.result
        self.assertEqual(r['r'].state, TestCase.Result.FATAL)
        self.assertEqual(r['r'].returncode, None)
        self.assertEqual(r['r'].stdout, '')
        self.assertIn("The results have not been set via the `setResults` method.", r['r'].stderr)
        self.assertEqual(r['r'].reasons, None)

        ct = TestController()
        rr = make_runner(TestRunner, [ct], name='r')
        tc = TestCase(runner=rr, controllers=(ct,))
        tc.setState(TestCase.Result.PASS)
        tc.setResult({'r':TestCase.Data(TestCase.Result.ERROR, None, 'r_out', 'r_err', None)})
        tc.reportResult()
        self.assertEqual(tc.progress, TestCase.Progress.FINISHED)
        self.assertEqual(tc.state, TestCase.Result.FATAL)
        r = tc.result
        self.assertEqual(r['r'].state, TestCase.Result.FATAL)
        self.assertEqual(r['r'].returncode, None)
        self.assertEqual(r['r'].stdout, '')
        self.assertIn("The execution has not finished, so results cannot be reported.", r['r'].stderr)
        self.assertEqual(r['r'].reasons, None)


    @mock.patch("moosetools.moosetest.base.TestCase._printState")
    def testReportProgress(self, pstate):

        # Runner
        ct = TestController()
        rr = make_runner(TestRunner, [ct], name='r')
        tc = TestCase(runner=rr, controllers=(ct,))

        tc.reportProgress()
        pstate.assert_called_with(rr, TestCase.Progress.WAITING, None)

        tc.setProgress(TestCase.Progress.RUNNING)
        tc.reportProgress()
        pstate.assert_called_with(rr, TestCase.Progress.RUNNING, None)

        tc.setProgress(TestCase.Progress.FINISHED)
        tc.reportProgress()
        pstate.assert_called_with(rr, TestCase.Progress.FINISHED, None)

        # Error
        tc._TestCase__progress = None
        tc.reportProgress()
        pstate.assert_called_with(rr, TestCase.Progress.FINISHED, None)
        self.assertEqual(tc.progress, TestCase.Progress.FINISHED)
        self.assertEqual(tc.state, TestCase.Result.FATAL)
        r = tc.result
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
        tc = TestCase(runner=rr, controllers=(ct,), formatter=fm)
        tc.setProgress(TestCase.Progress.RUNNING)

        # Runner, progress
        tc._printState(rr, TestCase.Progress.RUNNING, ["all the reasons"])
        kwargs = r_state.call_args.kwargs
        self.assertEqual(kwargs['name'], 'r')
        self.assertEqual(kwargs['state'], TestCase.Progress.RUNNING)
        self.assertEqual(kwargs['reasons'], ["all the reasons"])
        self.assertIsInstance(kwargs['duration'], float) # exact number can't be tested
        self.assertIsInstance(kwargs['percent'], float)

        # Differ, progress
        tc.setProgress(TestCase.Progress.FINISHED) # call this to use execute time
        tc._printState(dr, TestCase.Progress.FINISHED, ["all the reasons"])
        kwargs = d_state.call_args.kwargs
        self.assertEqual(kwargs['name'], 'd')
        self.assertEqual(kwargs['state'], TestCase.Progress.FINISHED)
        self.assertEqual(kwargs['reasons'], ["all the reasons"])
        self.assertIsInstance(kwargs['duration'], float) # exact number can't be tested
        self.assertIsInstance(kwargs['percent'], float)

        # Runner, results
        tc.setProgress(TestCase.Progress.FINISHED)
        tc.setState(TestCase.Result.PASS)
        tc.setResult({'r':TestCase.Data(TestCase.Result.PASS, None, 'r_out', 'r_err', None),
                      'd':TestCase.Data(TestCase.Result.PASS, None, 'd_out', 'd_err', None)})
        tc._printResult(rr, tc.result['r'])
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
        tc.setResult({'r':TestCase.Data(TestCase.Result.PASS, None, 'r_out', 'r_err', None),
                      'd':TestCase.Data(TestCase.Result.PASS, None, 'd_out', 'd_err', None)})
        tc._printResult(dr, tc.result['d'])
        kwargs = d_result.call_args.kwargs
        self.assertEqual(kwargs['name'], 'd')
        self.assertEqual(kwargs['state'], TestCase.Result.PASS)
        self.assertEqual(kwargs['reasons'], None)
        self.assertIsInstance(kwargs['duration'], float) # exact number can't be tested
        self.assertIsInstance(kwargs['percent'], float)
        self.assertEqual(kwargs['stdout'], 'd_out')
        self.assertEqual(kwargs['stderr'], 'd_err')


if __name__ == '__main__':
    unittest.main(module=__name__, verbosity=2)