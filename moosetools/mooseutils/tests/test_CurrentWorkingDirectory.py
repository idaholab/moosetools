#!/usr/bin/env python3
#* This file is part of MOOSETOOLS repository
#* https://www.github.com/idaholab/moosetools
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moosetools/blob/main/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html

import platform
import os
import unittest
import pickle
import multiprocessing
from moosetools import mooseutils


class Test(unittest.TestCase):
    def testChange(self):
        home = os.getenv('HOME')
        self.assertNotEqual(home, os.getcwd(), "Test does not work from 'HOME' directory.")

        obj = mooseutils.CurrentWorkingDirectory(home)
        self.assertEqual(obj.external, os.getcwd())
        self.assertEqual(obj.internal, home)

        with mooseutils.CurrentWorkingDirectory(home) as cwd:
            self.assertEqual(os.getcwd(), home)
            self.assertEqual(cwd.internal, os.getcwd())

        self.assertNotEqual(home, os.getcwd())
        self.assertEqual(cwd.external, os.getcwd())

    def testException(self):
        home = os.getenv('HOME')
        self.assertNotEqual(home, os.getcwd(), "Test does not work from 'HOME' directory.")

        with self.assertRaises(Exception) as e:
            with mooseutils.CurrentWorkingDirectory(home) as cwd:
                self.assertEqual(os.getcwd(), home)
                self.assertEqual(cwd.internal, os.getcwd())
                raise Exception('foo')

            self.assertNotEqual(home, os.getcwd())
            self.assertEqual(cwd.external, os.getcwd())

        self.assertIn('foo', str(e.exception))


if __name__ == '__main__':
    unittest.main(module=__name__, verbosity=2)
