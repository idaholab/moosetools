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
from moosetools.moosetest.filters import NameFilter


class RunnerProxy(object):
    def name(self):
        return 'the_runner'

    def status(self):
        return 0


class TestNameFilter(unittest.TestCase):
    def testDefault(self):
        f = NameFilter()
        r = RunnerProxy()

        self.assertFalse(f.apply(r))

        f.parameters().setValue('in_name', 'the_')
        self.assertFalse(f.apply(r))

        f.parameters().setValue('in_name', 'not_this')
        self.assertTrue(f.apply(r))


if __name__ == '__main__':
    unittest.main(module=__name__, verbosity=2)
