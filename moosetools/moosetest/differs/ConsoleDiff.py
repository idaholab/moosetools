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


class ConsoleDiff(Differ):
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

    def execute(self, rcode, stdout, stderr):

        # STDOUT/STDERR
        text_in = self.getParam('text_in')
        if (text_in is not None) and (text_in not in stdout) and (text_in not in stderr):
            msg = "The content of 'text_in' parameter, '{}', was not located in the output of sys.stdout or sys.stderr:\n{}\n{}"
            self.error(msg, text_in, stdout, stderr)

        text_not_in = self.getParam('text_not_in')
        if (text_not_in is not None) and ((text_not_in in stdout) or (text_not_in in stderr)):
            msg = "The content of 'text_not_in' parameter, '{}', was located in the output sys.stdout or sys.stderr:\n{}\n{}"
            self.error(msg, text_not_in, stdout, stderr)

        # STDOUT
        text_in = self.getParam('text_in_stdout')
        if (text_in is not None) and (text_in not in stdout):
            msg = "The content of 'text_in_stdout' parameter, '{}', was not located in the output of sys.stdout:\n{}"
            self.error(msg, text_in, stdout)

        text_not_in = self.getParam('text_not_in_stdout')
        if (text_not_in is not None) and (text_not_in in stdout):
            msg = "The content of 'text_not_in_stdout' parameter, '{}', was located in the output of sys.stdout:\n{}"
            self.error(msg, text_not_in, stdout)

        # STDERR
        text_in = self.getParam('text_in_stderr')
        if (text_in is not None) and (text_in not in stderr):
            msg = "The content of 'text_in_stderr' parameter, '{}', was not located in the output of sys.stderr:\n{}"
            self.error(msg, text_in, stderr)

        text_not_in = self.getParam('text_not_in_stderr')
        if (text_not_in is not None) and (text_not_in in stderr):
            msg = "The content of 'text_not_in_stderr' parameter, '{}', was located in the output of sys.stderr:\n{}"
            self.error(msg, text_not_in, stderr)

        # RE
        flags = 0
        for flag in self.getParam('re_flags'):
            flags |= eval(f're.{flag}')

        re_match = self.getParam('re_match')
        if re_match is not None:
            match = re.search(re_match, stdout, flags=flags) or re.match(
                re_match, stderr, flags=flags)
            if not match:
                msg = "The regular expression of 're_match' parameter, '{}', did not produce a match in the output of sys.stdout or sys.stderr:\n{}\n{}"
                self.error(msg, re_match, stdout, stderr)

        re_match = self.getParam('re_not_match')
        if re_match is not None:
            match = re.search(re_match, stdout, flags=flags) or re.match(
                re_match, stderr, flags=flags)
            if match:
                msg = "The regular expression of 're_not_match' parameter, '{}', did produce a match in the output of sys.stdout or sys.stderr:\n{}\n{}"
                self.error(msg, re_match, stdout, stderr)

        # RE STDOUT
        re_match = self.getParam('re_match_stdout')
        if re_match is not None:
            match = re.search(re_match, stdout, flags=flags)
            if not match:
                msg = "The regular expression of 're_match_stdout' parameter, '{}', did not produce a match in the output of sys.stdout:\n{}"
                self.error(msg, re_match, stdout)

        re_match = self.getParam('re_not_match_stdout')
        if re_match is not None:
            match = re.search(re_match, stdout, flags=flags)
            if match:
                msg = "The regular expression of 're_not_match_stdout' parameter, '{}', did produce a match in the output of sys.stdout:\n{}"
                self.error(msg, re_match, stdout)

        # RE STDERR
        re_match = self.getParam('re_match_stderr')
        if re_match is not None:
            match = re.search(re_match, stderr, flags=flags)
            if not match:
                msg = "The regular expression of 're_match_stderr' parameter, '{}', did not produce a match in the output of sys.stderr:\n{}"
                self.error(msg, re_match, stderr)

        re_match = self.getParam('re_not_match_stderr')
        if re_match is not None:
            match = re.search(re_match, stderr, flags=flags)
            if match:
                msg = "The regular expression of 're_not_match_stderr' parameter, '{}', did produce a match in the output of sys.stderr:\n{}"
                self.error(msg, re_match, stdout)

        # EXIT CODE
        nonzero_exit_expected = self.getParam('nonzero_exit_expected')
        if nonzero_exit_expected and rcode == 0:
            log.error("A non-zero exit code was expected, but not produced.")
        elif not nonzero_exit_expected and rcode > 0:
            log.error(
                "A non-zero exit code was not expected, but and exit code of '{}' was produced.",
                rcode)
