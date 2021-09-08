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
import enum
import time
import multiprocessing
import math
from unittest import mock
from moosetools import parameters
from moosetools import pyhit
from moosetools import factory

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

        class Name(enum.Enum):
            ALLISON = 8
            ISAAC = 10

        self.assertConvert(Name, 'ALLISON', Name.ALLISON)
        self.assertConvert(Name, 'ISAAC', Name.ISAAC)
        value = factory.Parser._getValueFromStr((Name, ), 'ANDREW', False)  # handles wrong name
        self.assertEqual(value, None)

    def testSimple(self):
        f = factory.Factory()
        f.load()
        p = factory.Parser(f)
        objects = p.parseFile('test0.hit')

        self.assertEqual(len(objects), 2)
        self.assertEqual(objects[0].name(), 'object0')
        self.assertEqual(objects[1].name(), 'object1')

    def testTypes(self):

        f = factory.Factory()
        f.load()
        p = factory.Parser(f)
        objects = p.parseFile('test1.hit')

        self.assertEqual(len(objects), 4)
        self.assertEqual(objects[0].name(), 'scalar')
        self.assertEqual(objects[0].getParam('par_int'), 1980)
        self.assertEqual(objects[0].getParam('par_float'), 1.2345)
        self.assertEqual(objects[0].getParam('par_str'), "string with space")
        self.assertEqual(objects[0].getParam('par_bool'), True)

        self.assertEqual(objects[1].name(), 'vector')
        self.assertEqual(objects[1].getParam('vec_int'), (1949, 1954, 1977, 1980))
        self.assertEqual(objects[1].getParam('vec_float'), (1.1, 1.2, 1.3))
        self.assertEqual(objects[1].getParam('vec_str'), ("s0", "s1", "s2"))
        self.assertEqual(objects[1].getParam('vec_bool'), (True, False, True, False, True, False))

        self.assertEqual(objects[2].name(), 'any')
        self.assertEqual(objects[2].getParam('par'), "this is something")

        self.assertEqual(objects[3].name(), 'scalar_with_quote')
        self.assertEqual(objects[3].getParam('par_int'), 1980)
        self.assertEqual(objects[3].getParam('par_float'), 1.2345)
        self.assertEqual(objects[3].getParam('par_str'), "string with 'quote'")
        self.assertEqual(objects[3].getParam('par_bool'), True)

    def testSubBlocks(self):
        root = pyhit.Node(None, 'Tests')
        root.append('obj0', type='TestObject')
        root.append('obj1', type='TestObject')
        sub = root.append('sub')
        sub.append('obj2', type='TestObject')
        sub.append('obj3', type='TestObject')

        f = factory.Factory()
        f.load()
        p = factory.Parser(f)

        with mock.patch('moosetools.pyhit.parse') as load:
            load.return_value = root
            objects = p.parseFile('test0.hit')

        self.assertEqual(len(objects), 4)
        self.assertEqual(objects[0].name(), 'obj0')
        self.assertEqual(objects[1].name(), 'obj1')
        self.assertEqual(objects[2].name(), 'obj2')
        self.assertEqual(objects[3].name(), 'obj3')

    def testErrors(self):

        f = factory.Factory()
        f.load()
        p = factory.Parser(f)

        # INVALID FILENAME
        with self.assertLogs(level='ERROR') as log:
            p.parseFile('wrong')
        self.assertEqual(len(log.output), 1)
        self.assertIn("The file 'wrong' does not exist.", log.output[0])

        # MISSING TYPE
        root = pyhit.Node(None, 'Tests')
        root.append('obj0')
        with self.assertLogs(level='ERROR') as log:
            p.parseNode('test0.hit', root)
        self.assertEqual(p.status(), 1)
        self.assertEqual(len(log.output), 1)
        self.assertIn("Missing 'type' in block", log.output[0])

        # FAIL PYHIT.LOAD
        with mock.patch('moosetools.pyhit.parse') as load:
            load.side_effect = Exception()
            with self.assertLogs(level='CRITICAL') as log:
                p.parseFile('test0.hit')
            self.assertEqual(p.status(), 1)
            self.assertEqual(len(log.output), 1)
            self.assertIn("Failed to parse file 'test0.hit' with pyhit.", log.output[0])

        # OBJECT FAILS VALIDPARAMS
        root = pyhit.Node(None, 'Tests')
        root.append('obj0', type='TestObjectBadParams')
        with mock.patch('moosetools.pyhit.parse') as load:
            load.return_value = root
            with self.assertLogs(level='ERROR') as log:
                p.parseFile('test0.hit')
            self.assertEqual(p.status(), 1)
            self.assertEqual(len(log.output), 2)
            self.assertIn("Failed to evaluate validParams function of 'TestObjectBadParams'",
                          log.output[0])
            self.assertIn("Failed to extract parameters from 'TestObjectBadParams'", log.output[1])

        # PARAM NO EXISTY
        root = pyhit.Node(None, 'Tests')
        root.append('obj0', type='TestObject', nope='1')
        with mock.patch('moosetools.pyhit.parse') as load:
            load.return_value = root
            with self.assertLogs(level='ERROR') as log:
                p.parseFile('test0.hit')
            self.assertEqual(p.status(), 1)
            self.assertEqual(len(log.output), 1)
            self.assertIn("he parameter 'nope' does not exist", log.output[0])

        # PARAM WRONG TYPE
        root = pyhit.Node(None, 'Tests')
        root.append('obj0', type='TestObject', par_int='abc')
        with mock.patch('moosetools.pyhit.parse') as load:
            load.return_value = root
            with self.assertLogs(level='ERROR') as log:
                p.parseFile('test0.hit')
            self.assertEqual(p.status(), 1)
            self.assertEqual(len(log.output), 1)
            self.assertIn(
                "Failed to convert 'abc' to the correct type(s) of '(<class 'int'>,)' for 'par_int' parameter",
                log.output[0])

        # OBJECT FAILS __INIT__
        root = pyhit.Node(None, 'Tests')
        root.append('obj0', type='TestObjectBadInit')
        with mock.patch('moosetools.pyhit.parse') as load:
            load.return_value = root
            with self.assertLogs(level='ERROR') as log:
                p.parseFile('test0.hit')
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
        with mock.patch('moosetools.pyhit.parse') as load:
            load.return_value = root
            with self.assertLogs(level='ERROR') as log:
                p.parseFile('test0.hit')
            self.assertEqual(p.status(), 1)
            self.assertEqual(len(log.output), 2)
            self.assertIn("Duplicate section 'Tests/obj0'", log.output[0])
            self.assertIn("Duplicate parameter 'Tests/obj0/type'", log.output[1])

    def testMultiple(self):

        filenames = ['test0.hit', 'test1.hit']

        f = factory.Factory()
        f.load()
        p = factory.Parser(f)
        objects = p.parse(filenames)

        self.assertEqual(len(objects), 6)
        self.assertEqual(objects[0].name(), 'object0')
        self.assertEqual(objects[1].name(), 'object1')
        self.assertEqual(objects[2].name(), 'scalar')
        self.assertEqual(objects[3].name(), 'vector')
        self.assertEqual(objects[4].name(), 'any')
        self.assertEqual(objects[5].name(), 'scalar_with_quote')

    def testPerformance(self):
        # test2.hit created with this
        #root = pyhit.Node(None, 'Tests')
        #for i in range(100):
        #    root.append('obj{:04d}'.format(i), type='TestObject')
        #pyhit.write('test2.hit', root)

        n = 5000  # 100 items per file
        filenames = ['test2.hit'] * 50

        f = factory.Factory()
        f.load()
        p = factory.Parser(f)

        w = list()
        t0 = time.perf_counter()
        for f in filenames:
            w += p.parseFile(f)
        self.assertEqual(len(w), n)
        t1 = time.perf_counter() - t0

        t0 = time.perf_counter()
        w = p.parse(filenames, max_workers=3)
        self.assertEqual(len(w), n)
        t2 = time.perf_counter() - t0

        self.assertTrue(t2 < t1, 'Serial: {}; Thread: {}'.format(t1, t2))


if __name__ == '__main__':
    unittest.main(module=__name__, verbosity=2, buffer=True)
