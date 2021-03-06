#* This file is part of MOOSETOOLS repository
#* https://www.github.com/idaholab/moosetools
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moosetools/blob/main/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html

from TestHarnessTestCase import TestHarnessTestCase


class TestHarnessTester(TestHarnessTestCase):
    def testRequiredObjects(self):
        """
        Test that the required_objects check works
        """
        output = self.runTests('--no-color', '-i', 'required_objects')
        self.assertRegex(
            output.decode('utf-8'),
            r'test_harness\.bad_object.*? \[DOESNOTEXIST NOT FOUND IN EXECUTABLE\] SKIP')
        self.assertRegex(output.decode('utf-8'), r'test_harness\.good_objects.*? OK')
        self.checkStatus(output.decode('utf-8'), passed=1, skipped=1)
