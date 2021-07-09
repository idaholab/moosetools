#* This file is part of MOOSETOOLS repository
#* https://www.github.com/idaholab/moosetools
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moosetools/blob/main/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html

import os
import re
import difflib
from moosetools.moosetest.base import FileDiffer


class TextFileDiffer(FileDiffer):
    """
    A tool for comparing the complete content of text files.
    """
    @staticmethod
    def validParams():
        params = FileDiffer.validParams()
        return params

    def execute(self, rcode, stdout, stderr):
        """
        Check all files for desired content.
        """
        for file_name, gold_name in self.pairs():
            self._compare(file_name, gold_name)

    def _compare(self, file_name, gold_name):
        """
        Compare the text file in *file_name* with the "gold standard" in *gold_name*.
        """
        if not os.path.isfile(file_name):
            self.critical("The file '{}' does not exist.", file_name)
            return
        if not os.path.isfile(gold_name):
            self.critical("The 'gold' file '{}' does not exist.", gold_name)
            return

        with open(file_name, 'r') as fid:
            f_content = fid.readlines()

        with open(gold_name, 'r') as fid:
            g_content = fid.readlines()

        diff = list(difflib.unified_diff(f_content, g_content, fromfile=gold_name,
                                         tofile=file_name))
        if len(diff) > 0:
            self.error("The file '{}' does not match '{}'.", file_name, gold_name)
            print('\n'.join(diff))
        else:
            print("Files are the same: {} == {}".format(file_name, gold_name))
