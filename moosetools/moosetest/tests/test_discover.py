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
import unittest
from unittest import mock
import queue
import platform
import uuid
import logging
import concurrent.futures

from moosetools import pyhit
from moosetools.parameters import InputParameters
from moosetools.moosetest import discover
from moosetools.moosetest.controllers import TagController
from moosetools.moosetest.discover import MooseTestFactory

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

    def testWithDefaults(self):
        f = MooseTestFactory(object_defaults={'_helpers.TestController': {'remove': 'true'}})
        f.load()
        params = f.params('TestController')
        self.assertEqual(params['remove'], 'true')

        f = MooseTestFactory(object_defaults={'_helpers.TestController': {'remove': True}})
        f.load()
        params = f.params('TestController')
        self.assertEqual(params['remove'], True)

        f = MooseTestFactory(object_defaults={'_helpers.TestController': {'sleep': '1'}})
        f.load()
        params = f.params('TestController')
        self.assertEqual(params['sleep'], 1)

        f = MooseTestFactory(object_defaults={'_helpers.TestController': {'sleep': 1}})
        f.load()
        params = f.params('TestController')
        self.assertEqual(params['sleep'], 1)


class TestDiscover(unittest.TestCase):
    def test(self):

        start = os.path.abspath(os.path.join(os.path.dirname(__file__), 'demo'))
        plugin_dirs = [os.path.abspath(os.path.join(os.path.dirname(__file__), 'demo', 'plugins'))]

        groups = discover(start, (TagController(), ), ['tests'], plugin_dirs=plugin_dirs)
        print(groups)
        self.assertEqual(len(groups), 3)
        self.assertEqual(groups[0][0].name(), "tests/tests:Tests/runner0")
        self.assertEqual(groups[0][0].getParam('differs'), None)
        self.assertEqual(groups[0][1].name(), "tests/tests:Tests/runner1")
        self.assertEqual(groups[0][1].getParam('differs'), None)
        self.assertEqual(groups[0][2].name(), "tests/tests:Tests/group/runner1")
        differs = groups[0][2].getParam('differs')


if __name__ == '__main__':
    unittest.main(module=__name__, verbosity=2, buffer=True)
