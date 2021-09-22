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
from moosetools.moosetest.base import Differ


class TextFileContentDiffer(Differ):
    """
    A tool for testing for the existence of text within the content of the text file(s).
    """
    @staticmethod
    def validParams():
        params = Differ.validParams()
        params.add('text_in',
                   vtype=str,
                   doc="Checks that the supplied text exists in the content of the text file(s).")
        params.add(
            'text_not_in',
            vtype=str,
            doc="Checks that the supplied text does not exist in the content of the text file(s).")
        params.add(
            're_match',
            vtype=str,
            doc=
            "Checks that the supplied regular expression returns a match in the content of the text file(s)."
        )
        params.add(
            're_not_match',
            vtype=str,
            doc=
            "Checks that the supplied regular expression does not return a match in the content of the text file(s)."
        )
        params.add('re_flags',
                   vtype=str,
                   array=True,
                   default=('MULTILINE', 'DOTALL', 'UNICODE'),
                   allow=('MULTILINE', 'DOTALL', 'UNICODE', 'IGNORECASE', 'VERBOSE', 'LOCALE',
                          'DEBUG', 'ASCII'),
                   doc="The names of the flags to pass to regular expression `match` function.")
        return params

    def execute(self, *args):
        """
        Check all files for desired content.
        """
        filenames = list(self.getParam('file', 'names_created') or tuple())
        filenames += list(self.getParam('file', 'names_modified') or tuple())
        for fname in filenames:
            self._checkFile(fname)

    def _checkFile(self, filename):
        """
        Perform checks on the content of the text file provided in *filename*.
        """
        if not os.path.isfile(filename):
            self.error("The file '{}' does not exist.", filename)
            return

        text_in = self.getParam('text_in')
        text_not_in = self.getParam('text_not_in')
        re_match = self.getParam('re_match')
        re_not_match = self.getParam('re_not_match')

        if not any([text_in, text_not_in, re_match, re_not_match]):
            return

        with open(filename, 'r') as fid:
            content = fid.read()

        if (text_in is not None) and (text_in not in content):
            msg = "The content of 'text_in' parameter, '{}', was not located in the content of '{}'."
            self.error(msg, text_in, filename)

        if (text_not_in is not None) and (text_not_in in content):
            msg = "The content of 'text_not_in' parameter, '{}', was located in the content of '{}'."
            self.error(msg, text_not_in, filename)

        # RE
        flags = 0
        for flag in self.getParam('re_flags'):
            flags |= eval(f're.{flag}')

        if re_match is not None:
            match = re.search(re_match, content, flags=flags)
            if not match:
                msg = "The regular expression of 're_match' parameter, '{}', did not produce a match in the content of '{}'."
                self.error(msg, re_match, filename)

        if re_not_match is not None:
            match = re.search(re_not_match, content, flags=flags)
            if match:
                msg = "The regular expression of 're_not_match' parameter, '{}', did produce a match in the content of '{}'."
                self.error(msg, re_not_match, filename)
