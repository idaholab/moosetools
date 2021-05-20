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
        params.add('re_match_stdout',
                   vtype=str,
                   doc="Checks that the supplied regular expression returns a match in sys.stdout.")
        params.add('re_match_stderr',
                   vtype=str,
                   doc="Checks that the supplied regular expression returns a match in sys.stderr.")
        params.add('re_flags',
                   vtype=str,
                   array=True,
                   default=('MULTILINE', 'DOTALL', 'UNICODE'),
                   allow=('MULTILINE', 'DOTALL', 'UNICODE', 'IGNORECASE', 'VERBOSE', 'LOCALE',
                          'DEBUG', 'ASCII'),
                   doc="The names of the flags to pass to regular expression `match` function.")
        return params

    def execute(self, rcode, stdout, stderr):

        # STDOUT/STDERR
        text_in = self.getParam('text_in')
        if (text_in is not None) and (text_in not in stdout) and (text_in not in stderr):
            msg = "The content of 'text_in' parameter, '{}', was not located in the output:\nsys.stdout:\n{}\nsys.stderr:\n{}"
            self.error(msg, text_in, stdout, stderr)

        text_not_in = self.getParam('text_not_in')
        if (text_not_in is not None) and ((text_not_in in stdout) or (text_not_in in stderr)):
            msg = "The content of 'text_not_in' parameter, '{}', was located in the output:\nsys.stdout:\n{}\nsys.stderr:\n{}"
            self.error(msg, text_not_in, stdout, stderr)

        # STDOUT
        text_in = self.getParam('text_in_stdout')
        if (text_in is not None) and (text_in not in stdout):
            msg = "The content of 'text_in_stdout' parameter, '{}', was not located in the output:\n{}"
            self.error(msg, text_in, stdout)

        text_not_in = self.getParam('text_not_in_stdout')
        if (text_not_in is not None) and (text_not_in in stdout):
            msg = "The content of 'text_not_in_stdout' parameter, '{}', was located in the output:\n{}"
            self.error(msg, text_not_in, stdout)

        # STDERR
        text_in = self.getParam('text_in_stderr')
        if (text_in is not None) and (text_in not in stderr):
            msg = "The content of 'text_in_stderr' parameter, '{}', was not located in the output:\n{}"
            self.error(msg, text_in, stderr)

        text_not_in = self.getParam('text_not_in_stderr')
        if (text_not_in is not None) and (text_not_in in stderr):
            msg = "The content of 'text_not_in_stderr' parameter, '{}', was located in the output:\n{}"
            self.error(msg, text_not_in, stderr)

        # RE
        flags = 0
        for flag in self.getParam('re_flags'):
            flags |= eval(f're.{flag}')

        re_match = self.getParam('re_match')
        if re_match is not None:
            match = re.match(re_match, stdout, flags=flags) or re.match(
                re_match, stderr, flags=flags)
            if not match:
                msg = "The regular expression of 're_match' parameter, '{}', did not produce a match in the output:\nsys.stdout:\n{}\nsys.stderr:\n{}"
                self.error(msg, re_match, stdout, stderr)

        # RE STDOUT
        re_match = self.getParam('re_match_stdout')
        if re_match is not None:
            match = re.match(re_match, stdout, flags=flags)
            if not match:
                msg = "The regular expression of 're_match' parameter, '{}', did not produce a match in the output:\n{}"
                self.error(msg, re_match, stdout)

        # RE STDERR
        re_match = self.getParam('re_match_stderr')
        if re_match is not None:
            match = re.match(re_match, stderr, flags=flags)
            if not match:
                msg = "The regular expression of 're_match' parameter, '{}', did not produce a match in the output:\n{}"
                self.error(msg, re_match, stderr)
