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
import platform
import sys
import argparse
import unittest
from unittest import mock

from moosetools import pyhit
from moosetools.moosetest import main
from moosetools.moosetest.base import Controller, TestCase, RedirectOutput
from moosetools.moosetest.main import TestHarness, make_harness, make_controllers, make_formatter, _locate_config, _load_config
from moosetools.moosetest.formatters import BasicFormatter


class TestTestHarness(unittest.TestCase):
    def testDefault(self):
        th = TestHarness()
        self.assertTrue(hasattr(th, 'applyCommandLineArguments'))


class TestMakeHarness(unittest.TestCase):
    def testDefault(self):
        root = pyhit.Node(None)
        root['n_threads'] = 1

        th = make_harness('.moosetest', root, None)
        self.assertIsInstance(th, TestHarness)
        self.assertEqual(th.getParam('n_threads'), 1)

    def testExceptions(self):

        with self.assertRaises(RuntimeError) as ex:
            root = pyhit.Node(None)
            root['type'] = 'foo'
            th = make_harness('.moosetest', root, None)
            self.assertIn("The 'type' parameter must NOT be defined", str(ex.exception))

        with mock.patch('moosetools.factory.Factory.status', return_value=1):
            with self.assertRaises(RuntimeError) as ex:
                th = make_harness('.moosetest', pyhit.Node(None), None)
            self.assertIn("An error occurred during registration of the TestHarness",
                          str(ex.exception))

        with mock.patch('moosetools.factory.Parser.status', return_value=1):
            with self.assertRaises(RuntimeError) as ex:
                th = make_harness('.moosetest', pyhit.Node(None), None)
            self.assertIn("An error occurred during parsing of the", str(ex.exception))

        with mock.patch('moosetools.base.MooseObject.status', side_effect=(0, 0, 1)):
            with self.assertRaises(RuntimeError) as ex:
                th = make_harness('.moosetest', pyhit.Node(None), None)
            self.assertIn("An error occurred applying the command line", str(ex.exception))


class TestMakeControllers(unittest.TestCase):
    def testDefault(self):
        root = pyhit.Node(None)
        controllers = make_controllers('.moosetest', root, tuple())
        for c in controllers:
            self.assertIsInstance(c, Controller)
        self.assertEqual(list(controllers)[0].getParam('prefix'), 'env')

    def testOverride(self):
        root = pyhit.Node(None)
        c = root.append('Controllers')
        c.append('env', type='EnvironmentController', prefix='environment')

        controllers = make_controllers('.moosetest', root, tuple())
        for c in controllers:
            self.assertIsInstance(c, Controller)
        self.assertEqual(list(controllers)[0].getParam('prefix'), 'environment')

    def testExceptions(self):
        with mock.patch('moosetools.factory.Factory.status', return_value=1):
            with self.assertRaises(RuntimeError) as ex:
                make_controllers('.moosetest', pyhit.Node(None), tuple())
            self.assertIn("An error occurred registering the Controller type", str(ex.exception))

        with mock.patch('moosetools.factory.Parser.status', return_value=1):
            with self.assertRaises(RuntimeError) as ex:
                make_controllers('.moosetest', pyhit.Node(None), tuple())
            self.assertIn("An error occurred during parsing of the Controller block",
                          str(ex.exception))


class TestMakeFormatter(unittest.TestCase):
    def testDefault(self):
        root = pyhit.Node(None)
        formatter = make_formatter('.moosetest', pyhit.Node(None), tuple())
        self.assertIsInstance(formatter, BasicFormatter)
        self.assertEqual(formatter.getParam('print_state'), TestCase.Result.TIMEOUT)

    def testOverride(self):
        root = pyhit.Node(None)
        root.append('Formatter', type='BasicFormatter', width=1980)
        formatter = make_formatter('.moosetest', root, tuple())
        self.assertIsInstance(formatter, BasicFormatter)
        self.assertEqual(formatter.getParam('width'), 1980)

    def testExceptions(self):
        with mock.patch('moosetools.factory.Factory.status', return_value=1):
            with self.assertRaises(RuntimeError) as ex:
                formatter = make_formatter('.moosetest', pyhit.Node(None), tuple())
            self.assertIn("An error occurred registering the Formatter type", str(ex.exception))

        with mock.patch('moosetools.factory.Parser.status', return_value=1):
            with self.assertRaises(RuntimeError) as ex:
                formatter = make_formatter('.moosetest', pyhit.Node(None), tuple())
            self.assertIn(
                "An error occurred during parsing of the root level parameters for creation of the Formatter object",
                str(ex.exception))


class TestLocateConfig(unittest.TestCase):
    def testDefault(self):
        demo = os.path.join(os.path.dirname(__file__), 'demo', 'tests', 'folder0')
        name = _locate_config(demo)
        self.assertEqual(
            name, os.path.abspath(os.path.join(os.path.dirname(__file__), 'demo', '.moosetest')))

    def testExact(self):
        demo = os.path.join(os.path.dirname(__file__), 'demo', '.moosetest')
        name = _locate_config(demo)
        self.assertEqual(name, demo)

    def testExceptions(self):
        with self.assertRaises(RuntimeError) as ex:
            _locate_config('wrong')
        self.assertIn("The supplied configuration location, 'wrong'", str(ex.exception))

        with mock.patch('os.path.isfile', return_value=0):
            with self.assertRaises(RuntimeError) as ex:
                _locate_config(os.getcwd())
        self.assertIn("Unable to locate a configuration", str(ex.exception))


class TestLoadConfig(unittest.TestCase):
    def testDefault(self):
        demo = os.path.join(os.path.dirname(__file__), 'demo', '.moosetest')
        root = _load_config(demo)
        self.assertIn('timeout', root)

    def testExceptions(self):
        with self.assertRaises(RuntimeError) as ex:
            _load_config('wrong')
        self.assertIn("The configuration file, 'wrong'", str(ex.exception))


@unittest.skipIf(platform.python_version() < '3.7', "Python 3.7 or greater required")
class TestMain(unittest.TestCase):
    @mock.patch('argparse.ArgumentParser.parse_args',
                return_value=argparse.Namespace(demo=False,
                                                config=os.path.join(os.path.dirname(__file__),
                                                                    'demo', '.moosetest')))
    def testDefault(self, mock_cli_args):
        rcode = main()
        self.assertEqual(rcode, 0)


@unittest.skipIf(platform.python_version() < '3.7', "Python 3.7 or greater required")
class TestFuzzer(unittest.TestCase):
    @mock.patch('argparse.ArgumentParser.parse_args', return_value=argparse.Namespace(demo=True))
    def testFuzzer(self, mock_cli_args):
        rcode = main()  # TODO: figure out how to mock the fuzzer function
        self.assertEqual(rcode, 1)


if __name__ == '__main__':
    unittest.main(module=__name__, verbosity=2, buffer=True)
