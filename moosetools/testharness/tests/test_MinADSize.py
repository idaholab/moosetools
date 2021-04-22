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
    def testMinADSize(self):
        """
        Test AD vector size
        """
        output = self.runTests('-i', 'ad_size', '--no-color').decode('utf-8')
        self.assertRegex(output, r'tests/test_harness.enough \.* OK')
        self.assertRegex(
            output,
            r'tests/test_harness\.too_few \.* \[MINIMUM AD SIZE 1000 NEEDED, BUT MOOSE IS CONFIGURED WITH \d+\] SKIP'
        )
