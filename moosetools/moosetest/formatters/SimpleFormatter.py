import collections
import time
import textwrap
from moosetools.mooseutils import color_text
from moosetools.moosetest.base import Formatter, TestCase
class SimpleFormatter(Formatter):

    @staticmethod
    def validParams():
        params = Formatter.validParams()
        params.add('width', default=100, vtype=int,
                   doc="The width of the state output (the results output is not altered).")
        params.add('print_state', vtype=TestCase.Result, default=TestCase.Result.SKIP,
                   doc="The minimum state of results to display.")
        params.add('differ_indent', default=' '*4, vtype=str,
                   doc="The text to use for indenting the differ state output.")
        params.add('fill_character', default='.', vtype=str,
                  # verify=(lambda v: len(v) == 1, "Must be a single character."), # TODO: This break multiprocessing...
                   doc="The character to use for filling between name and state.")
        return params

    def __init__(self, *args, **kwargs):
        Formatter.__init__(self, *args, **kwargs)

    def fill(self, *args):
        char = self.getParam('fill_character')
        width = self.getParam('width')
        return char * (width - sum([len(a) for a in args]) - 1)

    def formatRunnerState(self, obj, state, **kwargs):
        name = obj.name()
        stext = f"{state.display:9}"
        time = f"[{kwargs['duration']:.2f}s]"
        msg = f"{color_text(name, *state.color)}{self.fill(name, stext, time)}{time} {color_text(stext, *state.color)}"
        return msg

    def formatDifferState(self, obj, state, **kwargs):
        name = self.getParam('differ_indent') + obj.name()
        stext = f"{state.display:9}"
        msg = f"{color_text(name, *state.color)}{self.fill(name, stext)} {color_text(stext, *state.color)}"
        return msg

    def formatRunnerResult(self, obj, state, rcode, out, err, **kwargs):
        max_state = self.getParam('print_state')
        if state.level >= max_state.level:

            prefix = color_text(obj.name(), *state.color) + ':sys.stdout: '
            stdout = textwrap.indent(out, prefix, lambda *args: True)

            prefix = color_text(obj.name(), *state.color) + ':sys.stderr: '
            stderr = textwrap.indent(err, prefix, lambda *args: True)

            return (stdout + stderr).strip('\n')

    def formatDifferResult(self, obj, state, rcode, out, err, **kwargs):
        max_state = self.getParam('print_state')
        if state.level >= max_state.level:

            name = self.getParam('differ_indent') + obj.name()
            prefix = color_text(name, *state.color) + ':sys.stdout: '
            stdout = textwrap.indent(out, prefix, lambda *args: True)

            prefix = color_text(name, *state.color) + ':sys.stderr: '
            stderr = textwrap.indent(err, prefix, lambda *args: True)

            return (stdout + stderr).strip('\n')

    def formatComplete(self, complete, **kwargs):
        counts = collections.defaultdict(int)
        for tc in complete:
            counts[tc.getState()] += 1

        out = list()
        out.append("-"*self.getParam('width'))
        t = kwargs.get('duration', None)
        if t is not None:
            out.append(f"Executed {len(complete)} tests in {t:.1f} seconds.")
        out.append(' '.join(f"{color_text(s.display, *s.color)}:{counts[s]}" for s in TestCase.Result))
        return '\n'.join(out)
