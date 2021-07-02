#!/usr/bin/env python3
#* This file is part of MOOSETOOLS repository
#* https://www.github.com/idaholab/moosetools
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moosetools/blob/main/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html

import io
import logging
import unittest
from unittest import mock
from moosetools.parameters import InputParameters
from moosetools.core import MooseException, MooseObject
from moosetools.moosetest.controllers import EnvironmentController
from moosetools.moosetest.base import make_differ, TestCase


class TestObject(MooseObject):
    pass


class TestEnvironmentController(unittest.TestCase):
    def testDefault(self):
        ctrl = EnvironmentController()
        obj = make_differ(TestObject, (ctrl, ))

        self.assertEqual(ctrl.name(), 'EnvironmentController')
        self.assertEqual(ctrl.getParam('prefix'), 'env')

        ctrl.execute(obj, obj.getParam('env'))
        self.assertEqual(ctrl.state(), None)
        self.assertEqual(ctrl.getReasons(), [])

    def testPlatform(self):
        ctrl = EnvironmentController()
        obj = make_differ(TestObject, (ctrl, ), env_platform=('Darwin', ))

        with mock.patch('platform.system', return_value='Darwin'):
            ctrl.execute(obj, obj.getParam('env'))
        self.assertEqual(ctrl.state(), None)
        self.assertEqual(ctrl.getReasons(), [])

        with mock.patch('platform.system', return_value='Linux'):
            ctrl.execute(obj, obj.getParam('env'))
        self.assertEqual(ctrl.state(), TestCase.Result.SKIP)
        self.assertEqual(ctrl.getReasons(), ["'Linux' not in ('Darwin',)"])

    def testMinVersion(self):
        ctrl = EnvironmentController()
        obj = make_differ(TestObject, (ctrl, ), env_python_minimum_version='1980.6.24')

        with mock.patch('platform.python_version', return_value='2013.5.15'):
            ctrl.execute(obj, obj.getParam('env'))
        self.assertEqual(ctrl.state(), None)
        self.assertEqual(ctrl.getReasons(), [])

        with mock.patch('platform.python_version', return_value='1949.8.27'):
            ctrl.execute(obj, obj.getParam('env'))
        self.assertEqual(ctrl.state(), TestCase.Result.SKIP)
        self.assertEqual(ctrl.getReasons(), ['Python 1980.6.24 > 1949.8.27'])

    def testMaxVersion(self):
        ctrl = EnvironmentController()
        obj = make_differ(TestObject, (ctrl, ), env_python_maximum_version='1980.6.24')

        ctrl.execute(obj, obj.getParam('env'))
        self.assertEqual(ctrl.state(), None)
        self.assertEqual(ctrl.getReasons(), [])

        with mock.patch('platform.python_version', return_value='2013.5.15'):
            ctrl.execute(obj, obj.getParam('env'))
        self.assertEqual(ctrl.state(), TestCase.Result.SKIP)
        self.assertEqual(ctrl.getReasons(), ['Python 1980.6.24 < 2013.5.15'])

    def testRequired(self):
        ctrl = EnvironmentController()
        obj = make_differ(TestObject, (ctrl, ),
                          env_python_required_packages=('sys', 'io', 'unittest'))

        ctrl.execute(obj, obj.getParam('env'))
        self.assertEqual(ctrl.state(), None)
        self.assertEqual(ctrl.getReasons(), [])

        with mock.patch('moosetools.mooseutils.check_configuration', return_value=['sys', 'io']):
            ctrl.execute(obj, obj.getParam('env'))
        self.assertEqual(ctrl.state(), TestCase.Result.SKIP)
        self.assertEqual(ctrl.getReasons(), ['missing python package(s)'])


if __name__ == '__main__':
    unittest.main(module=__name__, verbosity=2)
