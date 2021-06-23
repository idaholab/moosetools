#!/usr/bin/env python3
#* This file is part of MOOSETOOLS repository
#* https://www.github.com/idaholab/moosetools
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moosetools/blob/main/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html

import unittest
from moosetools.core import MooseObject
from moosetools.moosetest.base import MooseTestObject


class TestMooseTestObject(unittest.TestCase):
    def testType(self):
        obj = MooseTestObject()
        self.assertIsInstance(obj, MooseObject)

    def test_reason(self):
        obj = MooseTestObject()
        obj.reason('something')
        self.assertEqual(obj.getReasons(), ['something'])
        obj.reason('else')
        self.assertEqual(obj.getReasons(), ['something', 'else'])
        obj.reset()
        self.assertEqual(obj.getReasons(), [])


if __name__ == '__main__':
    unittest.main(module=__name__, verbosity=2)
