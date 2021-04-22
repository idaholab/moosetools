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
    def testDeleted(self):
        """
        Test that deleted tests returns a failed deleted test when extra info argument is supplied
        """
        with self.assertRaises(subprocess.CalledProcessError) as cm:
            self.runTests('--no-color', '-i', 'deleted', '-e')

        e = cm.exception
        self.assertRegex(e.output.decode('utf-8'),
                         r'test_harness\.deleted.*? \[TEST DELETED TEST\] FAILED \(DELETED\)')

        # Verify return code is DELETED related (0x83)
        self.assertIs(0x83, e.returncode)

    def testNoExtraInfo(self):
        """
        Test that deleted tests do not run without -e (extra) option
        """
        output = self.runTests('--no-color', '-i', 'deleted').decode('utf-8')
        self.assertNotIn('tests/test_harness.deleted', output)
