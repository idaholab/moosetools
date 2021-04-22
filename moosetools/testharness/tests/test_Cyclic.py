#* This file is part of MOOSETOOLS repository
#* https://www.github.com/idaholab/moosetools
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moosetools/blob/main/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html

import subprocess
from TestHarnessTestCase import TestHarnessTestCase


class TestHarnessTester(TestHarnessTestCase):
    def testCyclic(self):
        """
        Test cyclic dependency error.
        """
        with self.assertRaises(subprocess.CalledProcessError) as cm:
            self.runTests('--no-color', '-i', 'cyclic_tests')

        e = cm.exception
        self.assertRegex(
            e.output.decode('utf-8'),
            r'tests/test_harness.testC.*? FAILED \(Cyclic or Invalid Dependency Detected!\)')
        self.assertRegex(e.output.decode('utf-8'),
                         r'tests/test_harness.test[A|B].*? \[SKIPPED DEPENDENCY\] SKIP')
