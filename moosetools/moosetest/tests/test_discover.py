#!/usr/bin/env python3
import os
import sys
import unittest
from unittest import mock
import queue
import dataclasses
import uuid
import logging
import concurrent.futures

from moosetools import pyhit
from moosetools.parameters import InputParameters
from moosetools.moosetest import discover
from moosetools.moosetest.discover import MooseTestFactory, MooseTestWarehouse, _create_runners

# I do not want the tests directory to be packages with __init__.py, so load from file
sys.path.append(os.path.join(os.path.dirname(__file__)))
from _helpers import TestController, TestRunner, TestDiffer


class TestMooseTestFactory(unittest.TestCase):
    def testDefault(self):
        f = MooseTestFactory()
        f.load()
        params = f.params('TestDiffer')
        self.assertIsInstance(params, InputParameters)

    def testWithController(self):
        f = MooseTestFactory(controllers=(TestController(), ))
        f.load()
        params = f.params('TestDiffer')
        self.assertIn('ctrl', params)
        self.assertIsInstance(params.getValue('ctrl'), InputParameters)


class TestMooseTesWarehouse(unittest.TestCase):
    def testAppend(self):
        w = MooseTestWarehouse(root_dir='foo/bar', specfile='foo/bar/testing/tests')

        with self.assertLogs(level='CRITICAL') as log:
            w.append(TestDiffer(name='diff'))
        self.assertEqual(len(log.output), 1)
        self.assertIn("The `Differ` object 'diff' is being added without", log.output[0])

        obj = TestRunner(name='N/A')
        obj.parameters().add('_hit_path', default='Tests/run')
        w.append(obj)
        print(w.objects)
        self.assertEqual(obj.name(), 'testing/tests:Tests/run')
        self.assertIs(w.objects[0], obj)

        obj = TestDiffer(name='thename')
        w.append(obj)
        self.assertEqual(obj.name(), 'thename')
        self.assertIs(w.objects[-1].getParam('differs')[0], obj)


@mock.patch('moosetools.pyhit.load')
class TestCreateRunners(unittest.TestCase):
    def testDifferError(self, pyhit_load):
        root = pyhit.Node(None)
        root.append('Tests')
        root(0).append('differ', type='TestDiffer')
        pyhit_load.return_value = root

        f = MooseTestFactory()
        f.load()
        with self.assertLogs(level='CRITICAL') as log:
            objs, status = _create_runners('foo/bar', 'foo/bar/testing/tests', ['Tests'], f)
        self.assertEqual(status, 1)
        self.assertEqual(len(log.output), 1)
        self.assertIn("The `Differ` object 'differ' is being added without", log.output[0])

    def testRunnerWithDiffers(self, pyhit_load):
        root = pyhit.Node(None)
        root.append('Tests')
        root(0).append('run0', type='TestRunner')
        root(0, 0).append('diff0-0', type='TestDiffer')
        root(0, 0).append('diff0-1', type='TestDiffer')

        root(0).append('run1', type='TestRunner')
        root(0, 1).append('diff1-0', type='TestDiffer')
        root(0, 1).append('diff1-1', type='TestDiffer')

        pyhit_load.return_value = root

        f = MooseTestFactory()
        f.load()
        with mock.patch('os.path.isfile', return_value=True):
            objs, status = _create_runners('foo/bar', 'foo/bar/testing/tests', ['Tests'], f)

        self.assertEqual(status, 0)
        self.assertIsInstance(objs[0], TestRunner)
        self.assertEqual(objs[0].name(), 'testing/tests:Tests/run0')
        differs = objs[0].getParam('differs')
        self.assertEqual(len(differs), 2)
        self.assertIsInstance(differs[0], TestDiffer)
        self.assertEqual(differs[0].name(), 'diff0-0')
        self.assertIsInstance(differs[1], TestDiffer)
        self.assertEqual(differs[1].name(), 'diff0-1')

        self.assertIsInstance(objs[1], TestRunner)
        self.assertEqual(objs[1].name(), 'testing/tests:Tests/run1')
        differs = objs[1].getParam('differs')
        self.assertEqual(len(differs), 2)
        self.assertIsInstance(differs[0], TestDiffer)
        self.assertEqual(differs[0].name(), 'diff1-0')
        self.assertIsInstance(differs[1], TestDiffer)
        self.assertEqual(differs[1].name(), 'diff1-1')


class TestDiscover(unittest.TestCase):
    def test(self):

        start = os.path.abspath(os.path.join(os.path.dirname(__file__), 'demo'))
        plugin_dirs = [os.path.abspath(os.path.join(os.path.dirname(__file__), 'demo', 'plugins'))]

        groups = discover(start, ['tests'], ['Tests'], plugin_dirs)
        self.assertEqual(len(groups), 3)
        self.assertEqual(groups[0][0].name(), "tests/tests:Tests/runner0")
        self.assertEqual(groups[0][0].getParam('differs'), None)
        self.assertEqual(groups[0][1].name(), "tests/tests:Tests/runner1")
        self.assertEqual(groups[0][1].getParam('differs'), None)
        self.assertEqual(groups[0][2].name(), "tests/tests:Tests/group/runner1")
        differs = groups[0][2].getParam('differs')

    @mock.patch('moosetools.factory.Parser.status', return_value=1)
    def testRuntimeError(self, mock_status):

        start = os.path.abspath(os.path.join(os.path.dirname(__file__), 'demo'))
        plugin_dirs = [os.path.abspath(os.path.join(os.path.dirname(__file__), 'demo', 'plugins'))]
        with self.assertRaises(RuntimeError) as ex:
            discover(start, ['tests'], ['Tests'], plugin_dirs)
        self.assertIn('Errors occurred during parsing', str(ex.exception))


if __name__ == '__main__':
    unittest.main(module=__name__, verbosity=2, buffer=True)
