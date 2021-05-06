#!/usr/bin/env python3
import io
import logging
import unittest
from moosetools.parameters import InputParameters
from moosetools.base import MooseException
from moosetools import moosetest

class TestRunner(unittest.TestCase):
    def testDefault(self):

        # name is required
        with self.assertRaises(MooseException) as ex:
            runner = moosetest.base.Runner()
        self.assertIn("The parameter 'name' is marked as required", str(ex.exception))

        runner = moosetest.base.Runner(name='name')
        self.assertIsNone(runner.getParam('differs'))

        with self.assertRaises(NotImplementedError) as ex:
            runner.execute()
        self.assertIn("The 'execute' method must be overridden.", str(ex.exception))

    def testControllers(self):
        class ProxyController(object):

            @staticmethod
            def validObjectParams():
                params = InputParameters()
                params.add('platform')
                return params

            def getParam(self, value):
                return 'test'

        runner = moosetest.base.make_runner(moosetest.base.Runner, [ProxyController(),], name='name', test_platform='TempleOS')
        self.assertIn('test', runner.parameters())
        self.assertIn('platform', runner.getParam('test'))
        self.assertEqual(runner.getParam('test_platform'), 'TempleOS')

if __name__ == '__main__':
    unittest.main(module=__name__, verbosity=2)
