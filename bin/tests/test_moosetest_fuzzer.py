#!/usr/bin/env python3
#* This file is part of MOOSETOOLS repository
#* https://www.github.com/idaholab/moosetools
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moosetools/blob/main/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html

import sys
import os
import unittest
import subprocess
from moosetools import mooseutils

class TestMooseTestFuzzerExe(unittest.TestCase):
    def test(self):
        working_dir = os.path.join(os.path.dirname(__file__))
        exe = os.path.relpath('../moosetest-fuzzer', working_dir)
        cmd = [exe, '--group_num', '2', '6', '--runner_num', '1', '3', '--runner_sleep', '0.1', '2']
        with mooseutils.CurrentWorkingDirectory(working_dir):
            out = subprocess.run(cmd, check=False, text=True, capture_output=True)

        self.assertEqual(out.returncode, 1)

if __name__ == '__main__':
    unittest.main(module=__name__, verbosity=2, buffer=True)
