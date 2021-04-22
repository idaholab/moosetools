#* This file is part of MOOSETOOLS repository
#* https://www.github.com/idaholab/moosetools
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moosetools/blob/main/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html

from moosetools.testharness.testers.Tester import Tester


class RunCommand(Tester):
    @staticmethod
    def validParams():
        params = Tester.validParams()
        params.addRequiredParam('command', "The command line to execute for this test.")
        params.addParam('test_name', "The name of the test - populated automatically")
        return params

    def __init__(self, *args, **kwargs):
        Tester.__init__(self, *args, **kwargs)
        self.command = self.specs['command']

    def getCommand(self, options):
        # Create the command line string to run
        return self.command

    def processResults(self, moose_dir, options, output):
        if self.exit_code != 0:
            self.setStatus(self.fail, 'CODE %d' % self.exit_code)

        return output
