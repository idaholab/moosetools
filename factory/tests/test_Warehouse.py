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
from unittest import mock
import parameters
import factory

class TestWarehouse(unittest.TestCase):
    def testInit(self):
        w = factory.Warehouse()
        w.append(1980)
        w.append(1980)
        w.append(2011)
        w.append(2013)
        self.assertEqual(len(w), 4)
        self.assertEqual(w.objects, [1980, 1980, 2011, 2013])
        self.assertEqual([o for o in w], [1980, 1980, 2011, 2013])

        w.clear()
        self.assertEqual(len(w), 0)

if __name__ == '__main__':
    unittest.main(module=__name__, verbosity=2)
