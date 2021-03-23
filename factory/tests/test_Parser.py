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

class TestParser(unittest.TestCase):
    def testDefault(self):
        f = factory.Factory()
        w = factory.Warehouse()
        p = factory.Parser(f, w, filename='inputs/test.hit')
        p.parse()

        self.assertEqual(len(w.objects), 2)
        self.assertEqual(w.objects[0].name(), 'obj0')
        self.assertEqual(w.objects[1].name(), 'obj1')


    def testConstruction(self):
        root = pyhit.Node(None)
        tests = pyhit.Node(root, 'Tests')
        tests.append('obj0', type='TestObject')
        tests.append('obj1', type='TestObject')
        sub = tests.append('sub')
        sub.append('obj2', type='TestObject')
        sub.append('obj3', type='TestObject')

        f = factory.Factory()
        w = factory.Warehouse()
        p = factory.Parser(f, w, filename='inputs/test.hit')

        with mock.patch('pyhit.load') as load:
            load.return_value = root
            p.parse()

        self.assertEqual(w.objects[0].name(), 'obj0')
        self.assertEqual(w.objects[1].name(), 'obj1')
        self.assertEqual(w.objects[2].name(), 'obj2')
        self.assertEqual(w.objects[3].name(), 'obj3')







if __name__ == '__main__':
    unittest.main(module=__name__, verbosity=2)
