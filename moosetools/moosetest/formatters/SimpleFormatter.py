import textwrap
from moosetools.mooseutils import color_text
from moosetools.moosetest.base import Formatter
class SimpleFormatter(Formatter):

    @staticmethod
    def validParams():
        params = Formatter.validParams()
        params.add('width', default=100, vtype=int,
                   doc="The width of the state output (the results output is not altered).")
        params.add('differ_indent', default=' '*4, vtype=str,
                   doc="The text to use for indenting the differ state output.")
        params.add('fill_character', default='.', vtype=str,
                   #verify=(lambda v: len(v) == 1, "Must be a single character."), # TODO: This break multiprocessing...
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
        prefix = '    ' + color_text(obj.name(), *state.color) + ':sys.stdout '
        return textwrap.indent(out, prefix, lambda *args: True)

    def formatDifferResult(self, obj, state, rcode, out, err, **kwargs):
        prefix = '    ' + color_text(obj.name(), *state.color) + ':sys.stderr '
        return textwrap.indent(err, prefix, lambda *args: True)
