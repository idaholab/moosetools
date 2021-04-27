import enum
import math
from moosetools.moosetest.base import Differ

class ShortenMode(enum.Enum):
    BEGIN = 0
    MIDDLE = 1
    END = 2


def shorten_text(text, max_lines=10, mode=ShortenMode.MIDDLE, replace='...'):
    lines = text.splitlines()
    if len(lines) < max_lines:
        return text

    if mode == ShortenMode.BEGIN:
        return '{replace}\n{}'.format('\n'.join(lines[:max_lines], replace=replace))
    elif mode == ShortenMode.END:
        return '{}\n{replace}'.format('\n'.join(lines[max_lines:], replace=replace))
    elif mode == ShortenMode.MIDDLE:
        n = math.floor(max_lines/2)
        return '{}\n{replace}\n{}'.format('\n'.join(lines[:n]), '\n'.join(lines[-n:]), replace=replace)

class TextDiff(Differ):
    @staticmethod
    def validParams():
        params = Differ.validParams()
        params.add('text_in_stdout', vtype=str, doc="Checks that the supplied text exists in sys.stdout.")
        params.add('text_not_in_stdout', vtype=str, doc="Checks that the supplied text does not exist in sys.stdout.")
        params.add('text_in_stderr', vtype=str, doc="Checks that the supplied text exists in sys.stderr.")
        params.add('text_not_in_stderr', vtype=str, doc="Checks that the supplied text does not exist in sys.stderr.")

        params.add('max_lines', default=5, vtype=int, doc="Maximum number of output lines to show in error messages.")
        return params

    def __init__(self, *args, **kwargs):
        Differ.__init__(self, *args, **kwargs)

    def execute(self, rcode, stdout, stderr):
        quote_stdout = shorten_text(stdout, self.getParam('max_lines'))
        quote_stderr = shorten_text(stderr, self.getParam('max_lines'))

        text_in = self.getParam('text_in_stdout')
        if (text_in is not None) and (text_in not in stdout):
            msg = "The content of 'text_in_stdout' parameter, '{}', was not located in the output:\n{}"
            self.error(msg, text_in, quote_stdout)

        text_not_in = self.getParam('text_not_in_stdout')
        if (text_not_in is not None) and (text_not_in in stdout):
            msg = "The content of 'text_not_in_stdout' parameter, '{}', was located in the output:\n{}"
            self.error(msg, text_in, quote_stdout)

        text_in = self.getParam('text_in_stderr')
        if (text_in is not None) and (text_in not in stderr):
            msg = "The content of 'text_in_stderr' parameter, '{}', was not located in the output:\n{}"
            self.error(msg, text_in, quote_stderr)

        text_not_in = self.getParam('text_not_in_stderr')
        if (text_not_in is not None) and (text_not_in in stderr):
            msg = "The content of 'text_not_in_stderr' parameter, '{}', was located in the output:\n{}"
            self.error(msg, text_in, quote_stderr)
