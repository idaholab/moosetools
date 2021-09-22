#* This file is part of MOOSETOOLS repository
#* https://www.github.com/idaholab/moosetools
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moosetools/blob/main/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html

import re
from moosetools.moosetest.base import Differ


class ConsoleDiffer(Differ):
    """
    A tool for testing for the existence of text within `sys.stdour` and/or `sys.stderr`.
    """
    @staticmethod
    def validParams():
        params = Differ.validParams()
        params.add('text_in',
                   vtype=str,
                   doc="Checks that the supplied text exists in sys.stdout or sys.stderr.")
        params.add('text_not_in',
                   vtype=str,
                   doc="Checks that the supplied text does not exist in sys.stdout and sys.stderr.")
        params.add('text_in_stdout',
                   vtype=str,
                   doc="Checks that the supplied text exists in sys.stdout.")
        params.add('text_not_in_stdout',
                   vtype=str,
                   doc="Checks that the supplied text does not exist in sys.stdout.")
        params.add('text_in_stderr',
                   vtype=str,
                   doc="Checks that the supplied text exists in sys.stderr.")
        params.add('text_not_in_stderr',
                   vtype=str,
                   doc="Checks that the supplied text does not exist in sys.stderr.")
        params.add(
            're_match',
            vtype=str,
            doc=
            "Checks that the supplied regular expression returns a match in sys.stdout or sys.stderr."
        )
        params.add(
            're_not_match',
            vtype=str,
            doc=
            "Checks that the supplied regular expression does not return a match in sys.stdout or sys.stderr."
        )
        params.add('re_match_stdout',
                   vtype=str,
                   doc="Checks that the supplied regular expression returns a match in sys.stdout.")
        params.add(
            're_not_match_stdout',
            vtype=str,
            doc="Checks that the supplied regular expression does not returns a match in sys.stdout."
        )
        params.add('re_match_stderr',
                   vtype=str,
                   doc="Checks that the supplied regular expression returns a match in sys.stderr.")
        params.add(
            're_not_match_stderr',
            vtype=str,
            doc="Checks that the supplied regular expression does not returns a match in sys.stderr."
        )

        params.add('re_flags',
                   vtype=str,
                   array=True,
                   default=('MULTILINE', 'DOTALL', 'UNICODE'),
                   allow=('MULTILINE', 'DOTALL', 'UNICODE', 'IGNORECASE', 'VERBOSE', 'LOCALE',
                          'DEBUG', 'ASCII'),
                   doc="The names of the flags to pass to regular expression `match` function.")

        params.add(
            'nonzero_exit_expected',
            vtype=bool,
            default=False,
            doc=
            "When True a non-zero exit code is expected, just does not result in a failure of this Differ."
        )

        return params

    def execute(self, rcode, text):

        # STDOUT/STDERR
        text_in = self.getParam('text_in')
        if (text_in is not None) and (text_in not in text):
            msg = "The content of 'text_in' parameter, '{}', was not located in the output text:\n{}"
            self.error(msg, text_in, text)

        text_not_in = self.getParam('text_not_in')
        if (text_not_in is not None) and ((text_not_in in stdout) or (text_not_in in stderr)):
            msg = "The content of 'text_not_in' parameter, '{}', was located in the output text:\n{}"
            self.error(msg, text_not_in, text)

        # RE
        flags = 0
        for flag in self.getParam('re_flags'):
            flags |= eval(f're.{flag}')

        re_match = self.getParam('re_match')
        if re_match is not None:
            match = re.search(re_match, text, flags=flags)
            if not match:
                msg = "The regular expression of 're_match' parameter, '{}', did not produce a match in the output text:\n{}"
                self.error(msg, re_match, text)

        re_match = self.getParam('re_not_match')
        if re_match is not None:
            match = re.search(re_match, text, flags=flags)
            if match:
                msg = "The regular expression of 're_not_match' parameter, '{}', did produce a match in the output text:\n{}"
                self.error(msg, re_match, text)

        # EXIT CODE
        nonzero_exit_expected = self.getParam('nonzero_exit_expected')
        if nonzero_exit_expected and rcode == 0:
            self.error("A non-zero exit code was expected, but not produced.")
        elif not nonzero_exit_expected and rcode > 0:
            self.error(
                "A non-zero exit code was not expected, but an exit code of '{}' was produced.",
                rcode)
