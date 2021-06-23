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
from moosetools import core


class TestMooseException(unittest.TestCase):
    def testRaise(self):
        with self.assertRaises(core.MooseException) as me:
            raise core.MooseException("Something {} {word}", "is", word="wrong")
        self.assertEqual(me.exception.message, "Something is wrong")


if __name__ == '__main__':
    unittest.main(module=__name__, verbosity=2)
