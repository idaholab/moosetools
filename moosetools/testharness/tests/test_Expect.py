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
    def testExpect(self):
        """
        Test that Expect Err/Out tests report if the message they are supposed to look for is missing
        """
        with self.assertRaises(subprocess.CalledProcessError) as cm:
            self.runTests('-i', 'expect')

        e = cm.exception
        self.assertRegex(
            e.output.decode('utf-8'),
            r'test_harness\.no_expect_err_pattern.*?FAILED \(EXPECTED ERROR MISSING\)')
        self.assertRegex(
            e.output.decode('utf-8'),
            r'test_harness\.no_expect_out_pattern.*?FAILED \(EXPECTED OUTPUT MISSING\)')
        self.assertRegex(e.output.decode('utf-8'),
                         r'test_harness\.absent_out_pattern.*?FAILED \(OUTPUT NOT ABSENT\)')

        self.assertRegex(
            e.output.decode('utf-8'),
            r'test_harness\.no_expect_err_literal.*?FAILED \(EXPECTED ERROR MISSING\)')
        self.assertRegex(
            e.output.decode('utf-8'),
            r'test_harness\.no_expect_out_literal.*?FAILED \(EXPECTED OUTPUT MISSING\)')
        self.assertRegex(e.output.decode('utf-8'),
                         r'test_harness\.absent_out_literal.*?FAILED \(OUTPUT NOT ABSENT\)')

    def testExpectMissing(self):
        """
        Test that Expect Err/Out tests report an error if both expect_err and expect_assert are missing.
        """
        with self.assertRaises(subprocess.CalledProcessError) as cm:
            self.runTests('-i', 'expect_missing_params')

        e = cm.exception
        self.assertRegex(e.output.decode('utf-8'),
                         r'Either "expect_err" or "expect_assert" must be supplied')
