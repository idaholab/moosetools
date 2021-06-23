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
import io
import logging
import unittest
from unittest import mock
from moosetools.parameters import InputParameters
from moosetools.core import MooseException
from moosetools import moosetest


class TestRunner(unittest.TestCase):
    def testInit(self):

        # name is required
        with self.assertRaises(MooseException) as ex:
            runner = moosetest.base.Runner()
        self.assertIn("The parameter 'name' is marked as required", str(ex.exception))

    def testExecute(self):
        runner = moosetest.base.Runner(name='name')
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

        runner = moosetest.base.make_runner(moosetest.base.Runner, [
            ProxyController(),
        ],
                                            name='name',
                                            test_platform='TempleOS')
        self.assertIn('test', runner.parameters())
        self.assertIn('platform', runner.getParam('test'))
        self.assertEqual(runner.getParam('test_platform'), 'TempleOS')

    def testDiffers(self):
        d = moosetest.base.make_differ(moosetest.base.Differ, name='a')
        runner = moosetest.base.make_runner(moosetest.base.Runner, differs=(d, ), name='name')
        self.assertIs(runner.getParam('differs')[0], d)

    def test_preExecute(self):
        runner = moosetest.base.Runner(name='run', file_names=('/runner_0', 'runner_1'))
        with self.assertLogs(level='ERROR') as log:
            runner.preExecute()
        self.assertEqual(len(log.output), 1)
        self.assertIn("The following file(s) were not defined as an absolute", log.output[0])
        self.assertIn("\n  runner_1", log.output[0])

        runner = moosetest.base.Runner(name='run', file_names=(os.path.abspath(__file__), ))
        with self.assertLogs(level='ERROR') as log:
            runner.preExecute()
        self.assertEqual(len(log.output), 1)
        self.assertIn("The following file(s) are being tracked with 'git'", log.output[0])

        runner = moosetest.base.Runner(name='run', file_names=('/file.e', ))
        with mock.patch('os.path.isfile',
                        side_effect=[True, False]), mock.patch('os.remove') as mock_remove:
            runner.preExecute()
        mock_remove.assert_called_once_with('/file.e')

        runner = moosetest.base.Runner(name='run', file_names=('/file.e', ))
        with self.assertLogs(level='ERROR') as log, mock.patch('os.path.isfile',
                                                               side_effect=[False, True]):
            runner.preExecute()
        self.assertEqual(len(log.output), 1)
        self.assertIn("The following files(s) are expected to be created, but they already exist",
                      log.output[0])
        self.assertIn("\n  /file.e", log.output[0])

        runner = moosetest.base.Runner(name='run', file_check_created=True)
        with self.assertLogs(level='ERROR') as log:
            runner.preExecute()
        self.assertEqual(len(log.output), 1)
        self.assertIn("When 'file_check_created' is enabled, the 'file_base'", log.output[0])
        self.assertIsNone(runner.getParam('differs'))

        runner = moosetest.base.Runner(name='run',
                                       file_base=os.path.abspath(os.path.dirname(__file__)))
        with mock.patch('os.listdir', return_value=['/foo/file']):
            runner.preExecute()
        self.assertEqual(runner._Runner__pre_execute_files, set(['/foo/file']))

    def test_postExecute(self):
        runner = moosetest.base.Runner(name='run', file_names=('/runner_0', '/runner_1'))
        runner.preExecute()
        with mock.patch('os.path.isfile',
                        side_effect=[False, True]), self.assertLogs(level='ERROR') as log:
            runner.postExecute()

        self.assertEqual(len(log.output), 1)
        self.assertIn("The following file(s) were not created as expected:", log.output[0])

        runner = moosetest.base.Runner(name='run',
                                       file_base=os.path.abspath(os.path.dirname(__file__)))
        with mock.patch('os.listdir',
                        side_effect=[['/foo/file'],
                                     ['/foo/file',
                                      '/bar/file']]), self.assertLogs(level='ERROR') as log:
            runner.preExecute()
            runner.postExecute()

        self.assertEqual(len(log.output), 1)
        self.assertIn("The following file(s) were created but not expected:\n  /bar/file",
                      log.output[0])

        runner.parameters().setValue('file', 'ignore_patterns', ('/bar/*', ))
        with mock.patch('os.listdir', side_effect=[['/foo/file'], ['/foo/file', '/bar/file']]):
            runner.preExecute()
            runner.postExecute()

    def test_getExpectedFiles(self):
        d0 = moosetest.base.make_differ(moosetest.base.Differ, name='a', file_names=('/differ_a', ))
        d1 = moosetest.base.make_differ(moosetest.base.Differ, name='b', file_names=('differ_b', ))
        runner = moosetest.base.Runner(name='run',
                                       differs=(d0, d1),
                                       file_names=('/runner_0', 'runner_1'))

        expected = runner._getExpectedFiles()
        self.assertEqual(expected, ['/runner_0', 'runner_1', '/differ_a', 'differ_b'])

        with mock.patch('os.path.isdir', return_value=True):
            runner.parameters().setValue('file', 'base', '/base')
            d0.parameters().setValue('file', 'base', '/base')
            d1.parameters().setValue('file', 'base', '/base')

        expected = runner._getExpectedFiles()
        self.assertEqual(expected, ['/runner_0', '/base/runner_1', '/differ_a', '/base/differ_b'])


if __name__ == '__main__':
    unittest.main(module=__name__, verbosity=2, buffer=True)
