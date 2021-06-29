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
import unittest
from moosetools import moosetest


class TestFuzzer(unittest.TestCase):
    @unittest.skipIf(platform.python_version() < '3.7', "Python 3.7 or greater required")
    def testFuzzer0(self):
        rcode = moosetest.fuzzer()
        self.assertIn(rcode, (0, 1))

    @unittest.skipIf(platform.python_version() < '3.7', "Python 3.7 or greater required")
    def testFuzzer(self):
        rcode = moosetest.fuzzer()
        self.assertIn(rcode, (0, 1))


if __name__ == '__main__':
    unittest.main(module=__name__, verbosity=2, buffer=True)
