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
from moosetools.moosetest.base import Controller, TestCase, RedirectOutput, TestHarness
from moosetools.moosetest.main import _make_harness, _make_controllers, _make_formatter, _setup_environment, _locate_config, _load_config
from moosetools.moosetest.formatters import BasicFormatter


class TestMakeHarness(unittest.TestCase):
    def testDefault(self):
        root = pyhit.Node(None)

        with mock.patch('os.path.isdir', return_value=True), mock.patch('os.chdir') as mock_chdir:
            th = _make_harness('.moosetest', root, tuple(), None)
        self.assertEqual(mock_chdir.call_count, 2)
        mock_chdir.assert_called_with(os.getcwd())
        self.assertIsInstance(th, TestHarness)
        self.assertEqual(th.getParam('n_threads'), os.cpu_count())

    def testWithBlock(self):
        root = pyhit.Node(None)
        root.append('TestHarness', type='TestHarness', n_threads=1)
        with mock.patch('os.path.isdir', return_value=True), mock.patch('os.chdir') as mock_chdir:
            th = _make_harness('.moosetest', root, tuple(), None)
        self.assertEqual(mock_chdir.call_count, 2)
        mock_chdir.assert_called_with(os.getcwd())
        self.assertIsInstance(th, TestHarness)
        self.assertEqual(th.getParam('n_threads'), 1)

    def testExceptions(self):
        with mock.patch('moosetools.factory.Factory.status', return_value=1):
            with self.assertRaises(RuntimeError) as ex, mock.patch(
                    'os.path.isdir', return_value=True), mock.patch('os.chdir'):
                th = _make_harness('.moosetest', pyhit.Node(None),tuple(),  None)
            self.assertIn("An error occurred during registration of the TestHarness",
                          str(ex.exception))

        with mock.patch('moosetools.factory.Parser.status', return_value=1):
            with self.assertRaises(RuntimeError) as ex, mock.patch(
                    'os.path.isdir', return_value=True), mock.patch('os.chdir'):
                th = _make_harness('.moosetest', pyhit.Node(None), tuple(), None)
            self.assertIn("An error occurred during parsing of the", str(ex.exception))


class TestMakeControllers(unittest.TestCase):
    def testDefault(self):
        root = pyhit.Node(None)
        with mock.patch('os.path.isdir', return_value=True), mock.patch('os.chdir') as mock_chdir:
            controllers = _make_controllers('.moosetest', root, tuple())
        self.assertEqual(mock_chdir.call_count, 2)
        mock_chdir.assert_called_with(os.getcwd())
        for c in controllers:
            self.assertIsInstance(c, Controller)
        self.assertEqual(list(controllers)[0].getParam('prefix'), 'env')

    def testOverride(self):
        root = pyhit.Node(None)
        c = root.append('Controllers')
        c.append('env', type='EnvironmentController', prefix='environment')

        with mock.patch('os.path.isdir', return_value=True), mock.patch('os.chdir'):
            controllers = _make_controllers('.moosetest', root, tuple())
        for c in controllers:
            self.assertIsInstance(c, Controller)
        self.assertEqual(list(controllers)[0].getParam('prefix'), 'environment')

    def testExceptions(self):
        with mock.patch('moosetools.factory.Factory.status', return_value=1):
            with self.assertRaises(RuntimeError) as ex, mock.patch(
                    'os.path.isdir', return_value=True), mock.patch('os.chdir'):
                _make_controllers('.moosetest', pyhit.Node(None), tuple())
            self.assertIn("An error occurred registering the Controller type", str(ex.exception))

        with mock.patch('moosetools.factory.Parser.status', return_value=1):
            with self.assertRaises(RuntimeError) as ex, mock.patch(
                    'os.path.isdir', return_value=True), mock.patch('os.chdir'):
                _make_controllers('.moosetest', pyhit.Node(None), tuple())
            self.assertIn("An error occurred during parsing of the Controller block",
                          str(ex.exception))


class TestMakeFormatter(unittest.TestCase):
    def testDefault(self):
        root = pyhit.Node(None)
        with mock.patch('os.path.isdir', return_value=True), mock.patch('os.chdir') as mock_chdir:
            formatter = _make_formatter('.moosetest', pyhit.Node(None))
        self.assertEqual(mock_chdir.call_count, 2)
        mock_chdir.assert_called_with(os.getcwd())
        self.assertIsInstance(formatter, BasicFormatter)
        self.assertEqual(formatter.getParam('print_state'), TestCase.Result.DIFF)

    def testOverride(self):
        root = pyhit.Node(None)
        root.append('Formatter', type='BasicFormatter', width=1980)
        with mock.patch('os.path.isdir', return_value=True), mock.patch('os.chdir'):
            formatter = _make_formatter('.moosetest', root)
        self.assertIsInstance(formatter, BasicFormatter)
        self.assertEqual(formatter.getParam('width'), 1980)

    def testExceptions(self):
        with mock.patch('moosetools.factory.Factory.status', return_value=1):
            with self.assertRaises(RuntimeError) as ex, mock.patch(
                    'os.path.isdir', return_value=True), mock.patch('os.chdir'):
                formatter = _make_formatter('.moosetest', pyhit.Node(None))
            self.assertIn("An error occurred registering the Formatter type", str(ex.exception))

        with mock.patch('moosetools.factory.Parser.status', return_value=1):
            with self.assertRaises(RuntimeError) as ex, mock.patch(
                    'os.path.isdir', return_value=True), mock.patch('os.chdir'):
                formatter = _make_formatter('.moosetest', pyhit.Node(None))
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

    def testNone(self):
        self.assertIsNone(_locate_config(os.path.dirname(__file__)))

    def testExceptions(self):
        with self.assertRaises(RuntimeError) as ex:
            _locate_config('wrong')
        self.assertIn("The supplied configuration location, 'wrong'", str(ex.exception))


class TestLoadConfig(unittest.TestCase):
    def testDefault(self):
        demo = os.path.join(os.path.dirname(__file__), 'demo', '.moosetest')
        root = _load_config(demo)
        self.assertEqual(root.children[0].fullpath, '/TestHarness')
        self.assertIn('timeout', root.children[0])

    def testNone(self):
        root = _load_config(None)
        self.assertEqual(len(root), 1)
        self.assertEqual(root.children[0].fullpath, '/TestHarness')
        self.assertEqual(dict(root.children[0].params()), {'type':'TestHarness'})

    def testExceptions(self):
        with self.assertRaises(RuntimeError) as ex:
            _load_config('wrong')
        self.assertIn("The configuration file, 'wrong'", str(ex.exception))


@unittest.skipIf(platform.python_version() < '3.7', "Python 3.7 or greater required")
class TestMain(unittest.TestCase):
    @mock.patch('argparse.ArgumentParser.parse_known_args')
    def testDefault(self, mock_cli_args):

        args = argparse.Namespace(config=os.path.join(os.path.dirname(__file__), 'demo', '.moosetest'),
                                  timeout=None,
                                  n_threads=None,
                                  max_failures=None,
                                  spec_file_blocks=None,
                                  spec_file_names = None)
        mock_cli_args.return_value = (args, None)

        rcode = main()
        self.assertEqual(rcode, 0)


class TestSetupEnvironment(unittest.TestCase):
    @mock.patch('moosetools.moosetree.find')
    def test(self, mock_find):
        root = pyhit.Node()
        root['SOME_DIR'] = os.getcwd()
        mock_find.return_value = root
        _setup_environment(None, root)
        self.assertIn('SOME_DIR', os.environ)
        self.assertEqual(os.environ['SOME_DIR'], os.getcwd())


if __name__ == '__main__':
    unittest.main(module=__name__, verbosity=2, buffer=True)
