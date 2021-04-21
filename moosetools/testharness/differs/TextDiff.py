import enum
import math
from ..base import Differ

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
        params.add('text_in', vtype=str, doc="Checks that the supplied text exists in the output.")
        params.add('text_not_in', vtype=str, doc="Checks that the supplied text does not exist in the output.")
        params.add('max_lines', default=5, vtype=int, doc="Maximum number of output lines to show in error messages.")
        return params

    def __init__(self, *args, **kwargs):
        Differ.__init__(self, *args, **kwargs)

    def execute(self, returncode, output):
        quote = shorten_text(output, self.getParam('max_lines'))

        text_in = self.getParam('text_in')
        if (text_in is not None) and (text_in not in output):
            msg = "The content of 'text_in' parameter, '{}', was not located in the output:\n{}"
            self.error(msg, text_in, quote)

        text_not_in = self.getParam('text_not_in')
        if (text_not_in is not None) and (text_not_ion in output):
            msg = "The content of 'text_not_in' parameter, '{}', was located in the output:"
            self.error(msg, text_in)
