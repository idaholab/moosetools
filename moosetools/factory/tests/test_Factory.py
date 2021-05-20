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
import importlib
import unittest
import tempfile
from unittest import mock
from moosetools import parameters
from moosetools import factory


class TestFactory(unittest.TestCase):
    def setUp(self):
        self._cwd = os.getcwd()
        os.chdir(os.path.dirname(__file__))
        self._tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        os.chdir(self._cwd)
        os.rmdir(self._tmpdir)

    def testInit(self):
        f = factory.Factory()
        self.assertEqual(f.status(), 0)
        f.load()
        self.assertEqual(f.status(), 0)

    def testLoad(self):
        f = factory.Factory(plugin_dirs=('./plugins', ))
        f.load()
        self.assertIn('CustomObject', f._registered_types)

    def testRegister(self):
        f = factory.Factory()
        f.load()
        self.assertEqual(f.status(), 0)

        plugins2 = os.path.join('plugins2', 'CustomObject2.py')
        spec = importlib.util.spec_from_file_location('CustomObject2', plugins2)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        otype = module.CustomObject2

        f.register('CO2', otype)
        self.assertEqual(f.status(), 0)

        obj = f.create('CO2', name='Andrew')
        self.assertEqual(f.status(), 0)
        self.assertIsInstance(obj, otype)
        self.assertEqual(obj.name(), 'Andrew')

        with self.assertLogs(level='ERROR') as log:
            f.register('CO2', otype)
        self.assertEqual(f.status(), 1)
        self.assertEqual(len(log.output), 1)
        self.assertIn("The 'CO2' name is already", log.output[0])

    def testParams(self):
        f = factory.Factory(plugin_dirs=('./plugins', ))
        f.load()
        self.assertEqual(f.status(), 0)

        params = f.params('TestObject')
        self.assertEqual(f.status(), 0)
        self.assertIn('par', params)

        with self.assertLogs(level='CRITICAL') as log:
            f.params('TestObjectBadParams')
        self.assertEqual(f.status(), 1)
        self.assertEqual(len(log.output), 1)
        self.assertIn('Failed to evaluate validParams', log.output[0])

        with self.assertLogs(level='ERROR') as log:
            f.params('Unknown')
        self.assertEqual(f.status(), 1)
        self.assertEqual(len(log.output), 1)
        self.assertIn("The supplied name 'Unknown' is not associated", log.output[0])

    def testCreate(self):
        f = factory.Factory(plugin_dirs=('./plugins', ))
        f.load()
        self.assertEqual(f.status(), 0)

        obj = f.create('CustomObject', name='Andrew')
        self.assertEqual(obj.name(), 'Andrew')
        self.assertEqual(f.status(), 0)

        obj = f.create('CustomCustomObject', name='Andrew')
        self.assertEqual(obj.name(), 'Andrew')
        self.assertEqual(f.status(), 0)

        with self.assertLogs(level='CRITICAL') as log:
            f.create('TestObjectBadInit', name='Andrew')
        self.assertEqual(f.status(), 1)
        self.assertEqual(len(log.output), 1)
        self.assertIn("Failed to create 'TestObjectBadInit'", log.output[0])

        with self.assertLogs(level='ERROR') as log:
            f.create('Unknown')
        self.assertEqual(f.status(), 1)
        self.assertEqual(len(log.output), 1)
        self.assertIn("The supplied name 'Unknown' is not associated", log.output[0])

    def testLoadError(self):
        f = factory.Factory(plugin_dirs=('./plugins', ))
        self.assertEqual(f.status(), 0)

        with mock.patch('importlib.import_module') as loader:
            loader.side_effect = Exception()
            with self.assertLogs(level='CRITICAL') as log:
                f.load()
            self.assertEqual(f.status(), 1)
            for out in log.output:
                self.assertIn("Failed to load module", out)

    def testPrint(self):
        f = factory.Factory(plugin_dirs=('./plugins', ))
        f.load()
        f._registered_types.pop('TestObjectBadParams')  # avoid error
        out = str(f)
        self.assertIn('CustomObject', out)
        self.assertIn('CustomCustomObject', out)

    def testPackageError(self):
        f = factory.Factory(plugin_dirs=(self._tmpdir, ))
        with self.assertLogs(level='ERROR') as log:
            f.load()
        self.assertEqual(f.status(), 1)
        self.assertEqual(len(log.output), 1)
        self.assertIn("the 'plugin_dirs' parameter is not a python package", log.output[0])


if __name__ == '__main__':
    unittest.main(module=__name__, verbosity=2)
