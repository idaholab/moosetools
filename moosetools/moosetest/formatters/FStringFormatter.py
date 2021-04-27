import textwrap
from moosetools.mooseutils import color_text
from moosetools.moosetest.base import Formatter
class FStringFormatter(Formatter):

    @staticmethod
    def validParams():
        params = Formatter.validParams()
        params.add('state_string', vtype=str,
                   default="{color_text(obj.name(), *state.color)}{'.'*(100-len(obj.name()))}{color_text(state.display, *state.color):<} [{kwargs['duration']:.2f}s] ",
                   doc="Python f-string to use for formatting output of state data.")
        params.add('stdout_string', vtype=str,
                   default="{textwrap.indent(out, prefix=color_text(obj.name(), *state.color) + ':sys.stdout: ')}",
                   doc="Python f-string to use for formatting output from results to sys.stdout.")
        params.add('stderr_string', vtype=str,
                   default="{textwrap.indent(err, prefix=color_text(obj.name(), *state.color) + ':sys.stderr: ')}",
                   doc="Python f-string to use for formatting output from results to sys.stderr.")

        return params

    def __init__(self, *args, **kwargs):
        Formatter.__init__(self, *args, **kwargs)

    def formatState(self, obj, state, **kwargs):
        msg = eval('f"' +self.getParam('state_string') + '"')
        return(msg)

    def formatResult(self, obj, state, rcode, out, err, **kwargs):
        msg_out = eval('f"' +self.getParam('stdout_string') + '"')
        msg_err = eval('f"' +self.getParam('stderr_string') + '"')
        return msg_out + msg_err
