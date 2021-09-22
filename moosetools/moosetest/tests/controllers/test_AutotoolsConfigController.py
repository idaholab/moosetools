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
import unittest
from unittest import mock
from moosetools.core import MooseObject
from moosetools.moosetest.base import make_differ, TestCase
from moosetools.moosetest.controllers import AutotoolsConfigController, AutotoolsConfigItem


class TestConfig(AutotoolsConfigController):
    @staticmethod
    def validParams():
        params = AutotoolsConfigController.validParams()
        params.setValue('prefix', 'moose')
        return params

    @staticmethod
    def validObjectParams():
        params = AutotoolsConfigController.validObjectParams()
        params.add('ad_mode',
                   allow=('SPARSE', 'NONSPARSE'),
                   user_data=AutotoolsConfigItem('MOOSE_SPARSE_AD', '0', {
                       '0': 'NONSPARSE',
                       '1': 'SPARSE'
                   }))
        params.add('not_in_config',
                   user_data=AutotoolsConfigItem('MOOSE_NOT_CONFIGURED', '1', {
                       '0': 'NO',
                       '1': 'YES'
                   }))
        params.add('no_map',
                   user_data=AutotoolsConfigItem('MOOSE_NO_MAP', '1', {
                       '0': 'NO',
                       '1': 'YES'
                   }))
        params.add('value_from_func',
                   vtype=int,
                   user_data=AutotoolsConfigItem('MOOSE_VALUE', '50', int))
        params.add('no_user_data')
        return params


class TestDiffer(MooseObject):
    pass


class Test(unittest.TestCase):
    def testBasic(self):
        config_file = os.path.join(os.path.dirname(__file__), 'TestConfig.h')
        ctrl = TestConfig(config_files=(config_file, ), log_level='DEBUG')
        obj = make_differ(TestDiffer, (ctrl, ))

        ctrl.execute(obj, obj.getParam('moose'))
        self.assertEqual(ctrl.state(), None)

        obj.parameters().setValue('moose', 'ad_mode', 'NONSPARSE')
        ctrl.reset()
        with self.assertLogs(level='DEBUG') as log:
            ctrl.execute(obj, obj.getParam('moose'))
        self.assertEqual(ctrl.state(), TestCase.Result.SKIP)
        self.assertEqual(len(log.output), 1)
        self.assertIn(
            "The application is configured with 'MOOSE_SPARSE_AD' equal to '1', which maps to a value of 'SPARSE'. However, the associated 'ad_mode' parameter for this test requires 'NONSPARSE'.",
            log.output[0])

    def test_loadConfig(self):
        config_file = os.path.join(os.path.dirname(__file__), 'TestConfig.h')
        out = AutotoolsConfigController.loadConfig(config_file)
        self.assertEqual(out['MOOSE_SPARSE_AD'], '1')
        self.assertEqual(out['MOOSE_PACKAGE_NAME'], 'moose')

        with self.assertRaises(IOError) as e:
            out = AutotoolsConfigController.loadConfig('wrong')
        self.assertEqual("The supplied file name, 'wrong', does not exist.", str(e.exception))

    def test_isFile(self):
        config_file = os.path.join(os.path.dirname(__file__), 'TestConfig.h')
        with mock.patch('os.path.isfile', return_value=True):
            self.assertTrue(AutotoolsConfigController.isFile(('file0', 'file1')))

        with mock.patch('os.path.isfile', side_effect=[True, False]):
            self.assertFalse(AutotoolsConfigController.isFile(('file0', 'file1')))

    def test_getConfigItem(self):
        config_file = os.path.join(os.path.dirname(__file__), 'TestConfig.h')
        ctrl = TestConfig(config_files=(config_file, ), log_level='DEBUG')
        obj = make_differ(TestDiffer, (ctrl, ))

        m_value, r_value, r_name = ctrl.getConfigItem(obj.getParam('moose'), 'ad_mode')
        self.assertEqual(m_value, 'SPARSE')
        self.assertEqual(r_value, '1')
        self.assertEqual(r_name, 'MOOSE_SPARSE_AD')

        m_value, r_value, r_name = ctrl.getConfigItem(obj.getParam('moose'), 'not_in_config')
        self.assertEqual(m_value, 'YES')
        self.assertEqual(r_value, '1')
        self.assertEqual(r_name, 'MOOSE_NOT_CONFIGURED')

        with self.assertRaises(RuntimeError) as e:
            ctrl.getConfigItem(obj.getParam('moose'), 'no_user_data')
        self.assertEqual(
            "The parameter 'no_user_data' does not contain a `AutotoolsConfigItem` object within the parameter 'user_data'.",
            str(e.exception))

        ctrl._AutotoolsConfigController__config_items['MOOSE_NO_MAP'] = '42'
        with self.assertRaises(RuntimeError) as e:
            ctrl.getConfigItem(obj.getParam('moose'), 'no_map')
        self.assertEqual(
            "The value of 'no_map' in the loaded file does not have a registered value in the mapping for '42'. The available mapping values are: 0, 1",
            str(e.exception))

        m_value, r_value, r_name = ctrl.getConfigItem(obj.getParam('moose'), 'value_from_func')
        self.assertEqual(m_value, 1980)
        self.assertEqual(r_value, '1980')
        self.assertEqual(r_name, 'MOOSE_VALUE')

    def test_checkConfig(self):
        config_file = os.path.join(os.path.dirname(__file__), 'TestConfig.h')
        ctrl = TestConfig(config_files=(config_file, ), log_level='DEBUG')
        obj = make_differ(TestDiffer, (ctrl, ))
        ctrl.checkConfig(obj.getParam('moose'), 'ad_mode')

        obj.parameters().setValue('moose', 'ad_mode', 'NONSPARSE')
        with self.assertLogs(level='DEBUG') as log:
            ctrl.execute(obj, obj.getParam('moose'))
        self.assertEqual(len(log.output), 1)
        self.assertIn(
            "The application is configured with 'MOOSE_SPARSE_AD' equal to '1', which maps to a value of 'SPARSE'. However, the associated 'ad_mode' parameter for this test requires 'NONSPARSE'.",
            log.output[0])

    def test_compare(self):
        compare = AutotoolsConfigController._compare
        self.assertEqual(compare(1980, 1980), (True, '1980==1980'))
        self.assertEqual(compare(1980, 1981), (False, '1980==1981'))
        self.assertEqual(compare('1980', 1980), (False, "'1980'==1980"))
        self.assertEqual(compare(1980, '1980'), (False, "1980=='1980'"))
        self.assertEqual(compare('1980', '1980'), (True, "'1980'=='1980'"))
        self.assertEqual(compare('1980', '1981'), (False, "'1980'=='1981'"))

        self.assertEqual(compare('1980', '<1980'), (False, "'1980'<'1980'"))
        self.assertEqual(compare('1979', '<1980'), (True, "'1979'<'1980'"))

        self.assertEqual(compare('1980', '<=1980'), (True, "'1980'<='1980'"))
        self.assertEqual(compare('1979', '<=1980'), (True, "'1979'<='1980'"))
        self.assertEqual(compare('1981', '<=1980'), (False, "'1981'<='1980'"))

        self.assertEqual(compare('1980', '>1980'), (False, "'1980'>'1980'"))
        self.assertEqual(compare('1981', '>1980'), (True, "'1981'>'1980'"))

        self.assertEqual(compare('1980', '>=1980'), (True, "'1980'>='1980'"))
        self.assertEqual(compare('1981', '>=1980'), (True, "'1981'>='1980'"))
        self.assertEqual(compare('1979', '>=1980'), (False, "'1979'>='1980'"))

        self.assertEqual(compare('1980', '!=1980'), (False, "'1980'!='1980'"))
        self.assertEqual(compare('1981', '!=1980'), (True, "'1981'!='1980'"))

        self.assertEqual(compare('1980', '!1980'), (False, "'1980'!='1980'"))
        self.assertEqual(compare('1981', '!1980'), (True, "'1981'!='1980'"))

        self.assertEqual(compare('1980', '==1980'), (True, "'1980'=='1980'"))
        self.assertEqual(compare('1981', '==1980'), (False, "'1981'=='1980'"))

    def test_compareVersions(self):
        compare = AutotoolsConfigController._compareVersions
        self.assertEqual(compare('1.2.1', '1.2.1'), (True, "1.2.1==1.2.1"))
        self.assertEqual(compare('1.2', '1.12'), (False, "1.2==1.12"))

        self.assertEqual(compare('1.1.2', '<1.12'), (True, "1.1.2<1.12"))
        self.assertEqual(compare('1.12', '<1.2'), (False, "1.12<1.2"))

        self.assertEqual(compare('1.12', '<=1.12.1'), (True, "1.12<=1.12.1"))
        self.assertEqual(compare('1.12', '<=1.12'), (True, "1.12<=1.12"))
        self.assertEqual(compare('1.1.2', '<=1.1.1'), (False, "1.1.2<=1.1.1"))

        self.assertEqual(compare('1.20', '>1.12'), (True, "1.20>1.12"))
        self.assertEqual(compare('1.2', '>1.12'), (False, "1.2>1.12"))

        self.assertEqual(compare('1.12.1', '>=1.12'), (True, "1.12.1>=1.12"))
        self.assertEqual(compare('1.12', '>=1.12'), (True, "1.12>=1.12"))
        self.assertEqual(compare('1.1.1', '>=1.1.2'), (False, "1.1.1>=1.1.2"))

        self.assertEqual(compare('1.2.1', '==1.2.1'), (True, "1.2.1==1.2.1"))
        self.assertEqual(compare('1.2', '==1.12'), (False, "1.2==1.12"))

        self.assertEqual(compare('1.2.1', '!=1.2.1'), (False, "1.2.1!=1.2.1"))
        self.assertEqual(compare('1.2', '!=1.12'), (True, "1.2!=1.12"))

        self.assertEqual(compare('1.2.1', '!1.2.1'), (False, "1.2.1!=1.2.1"))
        self.assertEqual(compare('1.2', '!1.12'), (True, "1.2!=1.12"))


if __name__ == '__main__':
    unittest.main(module=__name__, verbosity=2)
