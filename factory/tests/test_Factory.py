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
import parameters
import factory

class TestFactory(unittest.TestCase):
    def testDefault(self):
        f = factory.Factory()
        obj = f.create('CustomObject', name='Andrew')
        self.assertEqual(obj.name(), 'Andrew')

        obj = f.create('CustomCustomObject', name='Andrew')
        self.assertEqual(obj.name(), 'Andrew')

    def testBadLoad(self):
        with self.assertLogs(level='CRITICAL') as log:
            f = factory.Factory(plugin_dirs=(os.path.join(os.path.dirname(__file__), 'plugins2'),))
        self.assertEqual(len(log.output), 1)
        self.assertIn('NameError: name \'NotABaseClass\' is not defined', log.output[0])

    def testPrint(self):
        f = factory.Factory()
        out = str(f)
        self.assertIn('CustomCustomObject', out)

if __name__ == '__main__':
    unittest.main(module=__name__, verbosity=2)
