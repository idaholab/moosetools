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
import parameters
import pyhit
import factory

from plugins import TestObject


class TestParser(unittest.TestCase):
    def setUp(self):
        self._cwd = os.getcwd()
        os.chdir(os.path.dirname(__file__))

    def tearDown(self):
        os.chdir(self._cwd)

    def assertConvert(self, vtypes, str_value, gold):
        if not isinstance(vtypes, tuple): vtypes = (vtypes, )
        v = factory.Parser._getValueFromStr(vtypes, str_value, False)
        self.assertIsInstance(v, vtypes)
        self.assertEqual(v, gold)

    def assertConvertArray(self, vtypes, str_value, gold):
        if not isinstance(vtypes, tuple): vtypes = (vtypes, )
        value = factory.Parser._getValueFromStr(vtypes, str_value, True)
        self.assertTrue(all(isinstance(v, vtypes) for v in value))
        self.assertEqual(value, gold)

    def testGetValueFromStr(self):
        self.assertConvert(int, '1980', 1980)
        self.assertConvert(float, '1980', 1980)
        self.assertConvert(float, '1980.', 1980)
        self.assertConvert(float, '1980.', 1980)

        self.assertConvert((int, float), '1980', 1980)
        self.assertConvert((int, float), '1980.', 1980)

        self.assertConvert(bool, '0', False)
        self.assertConvert(bool, 'False', False)
        self.assertConvert(bool, 'false', False)
        self.assertConvert(bool, '1', True)
        self.assertConvert(bool, 'True', True)
        self.assertConvert(bool, 'true', True)

        self.assertConvert((bool, int), '0', False)
        self.assertConvert((int, bool), '0', 0)

        self.assertConvertArray(int, '1949 1954 1977 1980', (1949, 1954, 1977, 1980))
        self.assertConvertArray(float, '1949. 1954 1977. 1980', (1949, 1954, 1977, 1980))
        self.assertConvertArray((int, float), '1949 1954 1977 1980', (1949, 1954, 1977, 1980))
        self.assertConvertArray(str, 'a b c', ('a', 'b', 'c'))
        self.assertConvertArray(bool, '0 1 false true False True',
                                (False, True, False, True, False, True))

    def testSimple(self):
        f = factory.Factory()
        f.load()
        w = factory.Warehouse()
        p = factory.Parser(f, w)
        p.parse('test0.hit')

        self.assertEqual(len(w.objects), 2)
        self.assertEqual(w.objects[0].name(), 'object0')
        self.assertEqual(w.objects[1].name(), 'object1')

    def testTypes(self):

        f = factory.Factory()
        f.load()
        w = factory.Warehouse()
        p = factory.Parser(f, w)
        p.parse('test1.hit')

        self.assertEqual(len(w.objects), 4)
        self.assertEqual(w.objects[0].name(), 'scalar')
        self.assertEqual(w.objects[0].getParam('par_int'), 1980)
        self.assertEqual(w.objects[0].getParam('par_float'), 1.2345)
        self.assertEqual(w.objects[0].getParam('par_str'), "string with space")
        self.assertEqual(w.objects[0].getParam('par_bool'), True)

        self.assertEqual(w.objects[1].name(), 'vector')
        self.assertEqual(w.objects[1].getParam('vec_int'), (1949, 1954, 1977, 1980))
        self.assertEqual(w.objects[1].getParam('vec_float'), (1.1, 1.2, 1.3))
        self.assertEqual(w.objects[1].getParam('vec_str'), ("s0", "s1", "s2"))
        self.assertEqual(w.objects[1].getParam('vec_bool'), (True, False, True, False, True, False))

        self.assertEqual(w.objects[2].name(), 'any')
        self.assertEqual(w.objects[2].getParam('par'), "this is something")

        self.assertEqual(w.objects[3].name(), 'scalar_with_quote')
        self.assertEqual(w.objects[3].getParam('par_int'), 1980)
        self.assertEqual(w.objects[3].getParam('par_float'), 1.2345)
        self.assertEqual(w.objects[3].getParam('par_str'), "string with 'quote'")
        self.assertEqual(w.objects[3].getParam('par_bool'), True)

    def testSubBlocks(self):
        root = pyhit.Node(None, 'Tests')
        root.append('obj0', type='TestObject')
        root.append('obj1', type='TestObject')
        sub = root.append('sub')
        sub.append('obj2', type='TestObject')
        sub.append('obj3', type='TestObject')

        f = factory.Factory()
        f.load()
        w = factory.Warehouse()
        p = factory.Parser(f, w)

        with mock.patch('pyhit.load') as load:
            load.return_value = root
            p.parse('test0.hit')

        self.assertEqual(len(w.objects), 4)
        self.assertEqual(w.objects[0].name(), 'obj0')
        self.assertEqual(w.objects[1].name(), 'obj1')
        self.assertEqual(w.objects[2].name(), 'obj2')
        self.assertEqual(w.objects[3].name(), 'obj3')

    def testErrors(self):

        f = factory.Factory()
        f.load()
        w = factory.Warehouse()
        p = factory.Parser(f, w)

        # INVALID FILENAME
        with self.assertLogs(level='ERROR') as log:
            p.parse('wrong')
        self.assertEqual(len(log.output), 1)
        self.assertIn("The filename 'wrong' does not exist.", log.output[0])

        # FAIL PYHIT.LOAD
        with mock.patch('pyhit.load') as load:
            load.side_effect = Exception()
            with self.assertLogs(level='ERROR') as log:
                p.parse('test0.hit')
            self.assertEqual(p.status(), 1)
            self.assertEqual(len(log.output), 1)
            self.assertIn("Failed to load filename with pyhit: test0.hit", log.output[0])

        # MISSING TYPE
        root = pyhit.Node(None, 'Tests')
        root.append('obj0', raise_on_init='True')
        with mock.patch('pyhit.load') as load:
            load.return_value = root
            with self.assertLogs(level='ERROR') as log:
                p.parse('test0.hit')
            self.assertEqual(p.status(), 1)
            self.assertEqual(len(log.output), 1)
            self.assertIn("Missing 'type' in block 'Tests/obj0'", log.output[0])

        # OBJECT FAILS VALIDPARAMS
        root = pyhit.Node(None, 'Tests')
        root.append('obj0', type='TestObjectBadParams')
        with mock.patch('pyhit.load') as load:
            load.return_value = root
            with self.assertLogs(level='ERROR') as log:
                p.parse('test0.hit')
            self.assertEqual(p.status(), 1)
            self.assertEqual(len(log.output), 2)
            self.assertIn("Failed to evaluate validParams function of 'TestObjectBadParams'",
                          log.output[0])
            self.assertIn("Failed to extract parameters from 'TestObjectBadParams'", log.output[1])

        # PARAM NO EXISTY
        root = pyhit.Node(None, 'Tests')
        root.append('obj0', type='TestObject', nope='1')
        with mock.patch('pyhit.load') as load:
            load.return_value = root
            with self.assertLogs(level='ERROR') as log:
                p.parse('test0.hit')
            self.assertEqual(p.status(), 1)
            self.assertEqual(len(log.output), 1)
            self.assertIn("he parameter 'nope' does not exist", log.output[0])

        # PARAM WRONG TYPE
        root = pyhit.Node(None, 'Tests')
        root.append('obj0', type='TestObject', par_int='abc')
        with mock.patch('pyhit.load') as load:
            load.return_value = root
            with self.assertLogs(level='ERROR') as log:
                p.parse('test0.hit')
            self.assertEqual(p.status(), 1)
            self.assertEqual(len(log.output), 1)
            self.assertIn(
                "Failed to convert 'None' to the correct type(s) of '(<class 'int'>,)' for 'par_int' parameter",
                log.output[0])

        # OBJECT FAILS __INIT__
        root = pyhit.Node(None, 'Tests')
        root.append('obj0', type='TestObjectBadInit')
        with mock.patch('pyhit.load') as load:
            load.return_value = root
            with self.assertLogs(level='ERROR') as log:
                p.parse('test0.hit')
            self.assertEqual(p.status(), 1)
            self.assertEqual(len(log.output), 2)
            self.assertIn("Failed to create 'TestObjectBadInit' object.", log.output[0])
            self.assertIn(
                "Failed to create object of type 'TestObjectBadInit' in block 'Tests/obj0'",
                log.output[1])

        # DUPLICATE BLOCKS/PARAMS
        root = pyhit.Node(None, 'Tests')
        root.append('obj0', type='TestObject')
        root.append('obj0', type='TestObject')
        with mock.patch('pyhit.load') as load:
            load.return_value = root
            with self.assertLogs(level='ERROR') as log:
                p.parse('test0.hit')
            self.assertEqual(p.status(), 1)
            self.assertEqual(len(log.output), 2)
            self.assertIn("Duplicate section 'Tests/obj0'", log.output[0])
            self.assertIn("Duplicate parameter 'Tests/obj0/type'", log.output[1])


if __name__ == '__main__':
    unittest.main(module=__name__, verbosity=2)
