import collections
import time
import textwrap
from moosetools.mooseutils import color_text
from moosetools.moosetest.base import Formatter, TestCase
class BasicFormatter(Formatter):

    """
    TODO: Create a list of keyword arguments and functions that can be passed into an F-string then
          get rid of FStringFormatter.
          Rename this to BasicFormatter to be inline with basicConfig...

          Update State to include state.text for raw string and state.display to be color version

    """


    @staticmethod
    def validParams():
        params = Formatter.validParams()
        params.add('width', default=100, vtype=int,
                   doc="The width of the state output (the results output is not altered).")
        params.add('print_state', vtype=TestCase.Result, default=TestCase.Result.TIMEOUT,
                   doc="The minimum state of results to display.")
        params.add('differ_indent', default=' '*15, vtype=str,
                   doc="The text to use for indenting the differ state output.")
        #params.add('fill_character', default='.', vtype=str,
                  # verify=(lambda v: len(v) == 1, "Must be a single character."), # TODO: This break multiprocessing...
        #           doc="The character to use for filling between name and state.")
        return params

    def __init__(self, *args, **kwargs):
        Formatter.__init__(self, *args, **kwargs)

        max_state = max([len(e.text) for e in list(TestCase.Progress)])
        max_result = max([len(e.text) for e in list(TestCase.Result)])
        self._max_state_width = max(max_state, max_result)

    def fill(self, *args):
        char = self.getParam('fill_character')
        width = self.getParam('width')
        return char * (width - sum([len(a) for a in args]) - 1)

    def formatRunnerState(self, **kwargs):
        return self._formatState('', **kwargs)

    def formatDifferState(self, **kwargs):
        kwargs.pop('percent')
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
        out.append("-"*self.getParam('width'))
        t = kwargs.get('duration', None)
        if t is not None:
            out.append(f"Executed {len(complete)} tests in {t:.1f} seconds.")
        out.append(' '.join(f"{color_text(s.display, *s.color)}:{counts[s]}" for s in TestCase.Result))
        return '\n'.join(out)

    def _formatState(self, indent, **kwargs):
        state = kwargs.get('state')
        reasons = kwargs.get('reasons')
        percent = kwargs.get('percent', None)
        if percent is not None:
            percent = f'{percent:>3.0f}% '
        if reasons is not None:
            reasons = '; '.join(reasons)
        stext = f"{state.text:.<{self._max_state_width + 1}}{kwargs['name']}"
        msg = f"{percent or ''}{indent}{state.format(stext)} [{kwargs['duration']:.2f}s] {reasons or ''}"
        return msg

    def _formatResult(self, indent='', **kwargs):
        state = kwargs.get('state')
        name = kwargs.get('name')
        max_state = self.getParam('print_state')
        if state.level >= max_state.level:
            offset = indent + ' '*(self._max_state_width + 1)
            stdout = kwargs.get('stdout')
            if stdout:
                prefix = offset + state.format(name) + ' '
                stdout = textwrap.indent('sys.stdout:\n' + kwargs.get('stdout'), prefix, lambda *args: True)

            stderr = kwargs.get('stderr')
            if stderr:
                prefix = offset + state.format(name) + ' '
                stderr = textwrap.indent('sys.stderr:\n' + kwargs.get('stderr'), prefix, lambda *args: True)

            return (stdout + stderr).strip('\n')
