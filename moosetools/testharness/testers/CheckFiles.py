#* This file is part of the MOOSE framework
#* https://www.mooseframework.org
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moose/blob/master/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html

from moosetools.testharness.testers.FileTester import FileTester
from moosetools.testharness import util
import os

class CheckFiles(FileTester):

    @staticmethod
    def validParams():
        params = FileTester.validParams()
        params.add('check_files', vtype=str, array=True, doc="A list of files that MUST exist.")
        params.add('check_not_exists', vtype=str, array=True, doc="A list of files that must NOT exist.")
        params.addParam('file_expect_out', "A regular expression that must occur in all of the check files in order for the test to be considered passing.")
        return params

    def __init__(self, *args, **kwargs):
        FileTester.__init__(self, *args, **kwargs)

        # Make sure that either input or command is supplied
        if not (self.specs.isValid('check_files') or self.specs.isValid('check_not_exists')):
            raise Exception('Either "check_files" or "check_not_exists" must be supplied for a CheckFiles test')

    def getOutputFiles(self):
        out = list()
        for key in ['check_files', 'check_not_exists']:
            files = self.specs[key]
            if files is not None:
                out += list(files)

        return out

    def processResults(self, moose_dir, options, output):
        output += FileTester.processResults(self, moose_dir, options, output)

        specs = self.specs

        if self.isFail() or specs['skip_checks']:
            return output
        else:
            reason = ''
            # if still no errors, check other files (just for existence)
            for file in (self.specs['check_files'] or []):
                if not os.path.isfile(os.path.join(self.getTestDir(), file)):
                    reason = 'MISSING FILES'
                    break
            for file in (self.specs['check_not_exists'] or []):
                if os.path.isfile(os.path.join(self.getTestDir(), file)):
                    reason = 'UNEXPECTED FILES'
                    break

            # if still no errors, check that all the files contain the file_expect_out expression
            if reason == '':
                if self.specs.isValid('file_expect_out'):
                    for file in self.specs['check_files']:
                        fid = open(os.path.join(self.getTestDir(), file), 'r')
                        contents = fid.read()
                        fid.close()
                        if not util.checkOutputForPattern(contents, self.specs['file_expect_out']):
                            reason = 'NO EXPECTED OUT IN FILE'
                            break

        # populate status bucket
        if reason != '':
            self.setStatus(self.fail, reason)

        return output
