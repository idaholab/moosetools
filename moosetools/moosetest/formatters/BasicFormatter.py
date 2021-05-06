import enum
import math
import collections
import time
import shutil
import textwrap
from moosetools.mooseutils import color_text
from moosetools.moosetest.base import Formatter, TestCase


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

class BasicFormatter(Formatter):

    """
    TODO: Create a list of keyword arguments and functions that can be passed into an F-string then
          get rid of FStringFormatter.
          Rename this to BasicFormatter to be inline with basicConfig...

    """


    @staticmethod
    def validParams():
        params = Formatter.validParams()
        params.add('width', vtype=int,
                   doc="The width of the state output (the results output is not altered), if not " \
                       "provided terminal width is inferred with a default width of 80.")
        params.add('print_state', vtype=TestCase.Result, default=TestCase.Result.TIMEOUT,
                   doc="The minimum state of results to display.")
        params.add('differ_indent', default=' '*4, vtype=str,
                   doc="The text to use for indenting the differ state/result output.")

        params.add('max_lines', default=500, vtype=int,
                   doc="Maximum number of lines to show in sys.stdout/sys.stderr in result output.")
        return params

    def __init__(self, *args, **kwargs):
        Formatter.__init__(self, *args, **kwargs)

        max_state = max([len(e.text) for e in list(TestCase.Progress)])
        max_result = max([len(e.text) for e in list(TestCase.Result)])
        self._max_state_width = max(max_state, max_result)
        self._extra_width = 15 # Extract width for percent complete and duration

    def width(self):
        width = self.getParam('width')
        if width is None:
            width, _ = shutil.get_terminal_size()
        return width

    def fill(self, *args):
        width = self.width() - self._extra_width
        return '.' * (width - sum([len(a) for a in args]))

    def shortenLines(self, content):
        n = self.getParam('max_lines')
        return shorten_text(content, n, replace=f'...OUTPUT REMOVED (MAX LINES: {n})...')

    def formatRunnerState(self, **kwargs):
        return self._formatState('', **kwargs)

    def formatDifferState(self, **kwargs):
        kwargs.pop('percent')
        kwargs.pop('duration')
        return self._formatState(self.getParam('differ_indent'), **kwargs)

    def formatRunnerResult(self, **kwargs):
        return self._formatResult(**kwargs)

    def formatDifferResult(self, **kwargs):
        return self._formatResult(self.getParam('differ_indent'), **kwargs)

    def formatComplete(self, complete, **kwargs):
        counts = collections.defaultdict(int)
        for tc in complete:
            counts[tc.state] += 1

        out = list()
        out.append("-"*self.width())
        t = kwargs.get('duration', None)
        if t is not None:
            out.append(f"Executed {len(complete)} tests in {t:.1f} seconds.")
        out.append(' '.join(f"{color_text(s.display, *s.color)}:{counts[s]}" for s in TestCase.Result))
        return '\n'.join(out)

    def _formatState(self, indent, **kwargs):

        # Build suffix string that contains precent/duration information
        percent = kwargs.get('percent', None)
        percent = f"{percent:>3.0f}%" if (percent is not None) else ''

        duration = kwargs.get('duration', None)
        duration = f"[{duration:3.1f}s]" if (duration is not None) and (duration > 0) else ''

        suffix = "{:<{width}}".format(percent + ' ' + duration, width=self._extra_width)

        # Build the main status line
        # TODO: Handle long name and long reasons
        state = kwargs.get('state')
        status = f"{state.text:<{self._max_state_width}}"

        name = kwargs.get('name')

        # Create reasons and handle long reasons
        width_avail = self.width() - sum(len(x) for x in [indent, status, name])
        reasons = kwargs.get('reasons', None)
        reasons = '; '.join(reasons) if (reasons is not None) else ''
        if len(reasons) > (width_avail - 3):
            reasons = textwrap.shorten(reasons, width_avail - 6, placeholder='...')
        reasons = "[{}] ".format(reasons) if reasons else ''

        fill = self.fill(indent, name, reasons, status)
        msg = f"{indent}{state.format(name)}{fill}{state.format(reasons)}{state.format(status)}{suffix}"
        return msg

    def _formatResult(self, indent='', **kwargs):
        # TODO: Add shorten_text function here and remove from TextDiff


        state = kwargs.get('state')
        name = kwargs.get('name')
        max_state = self.getParam('print_state')
        if state.level >= max_state.level:
            stdout = kwargs.get('stdout')
            if stdout:
                prefix = indent + state.format(name) + ' '
                stdout = textwrap.indent('sys.stdout:\n' + self.shortenLines(kwargs.get('stdout')), prefix, lambda *args: True)

            stderr = kwargs.get('stderr')
            if stderr:
                prefix = indent + state.format(name) + ' '
                stderr = textwrap.indent('sys.stderr:\n' + self.shortenLines(kwargs.get('stderr')), prefix, lambda *args: True)

            return (stdout + stderr).strip('\n')
