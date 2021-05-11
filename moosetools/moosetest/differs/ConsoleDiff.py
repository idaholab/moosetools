import enum
import math
from moosetools.moosetest.base import Differ

class ConsoleDiff(Differ):

    @staticmethod
    def validParams():
        params = Differ.validParams()
        # TODO: text_in_out
        # TODO: text_notin_out

        params.add('text_in_stdout', vtype=str, doc="Checks that the supplied text exists in sys.stdout.")
        params.add('text_not_in_stdout', vtype=str, doc="Checks that the supplied text does not exist in sys.stdout.")
        params.add('text_in_stderr', vtype=str, doc="Checks that the supplied text exists in sys.stderr.")
        params.add('text_not_in_stderr', vtype=str, doc="Checks that the supplied text does not exist in sys.stderr.")

        return params

    #def __init__(self, *args, **kwargs):
    #    Differ.__init__(self, *args, **kwargs)

    def execute(self, rcode, stdout, stderr):
        text_in = self.getParam('text_in_stdout')
        if (text_in is not None) and (text_in not in stdout):
            msg = "The content of 'text_in_stdout' parameter, '{}', was not located in the output:\n{}"
            self.error(msg, text_in, stdout)

        text_not_in = self.getParam('text_not_in_stdout')
        if (text_not_in is not None) and (text_not_in in stdout):
            msg = "The content of 'text_not_in_stdout' parameter, '{}', was located in the output:\n{}"
            self.error(msg, text_in, stdout)

        text_in = self.getParam('text_in_stderr')
        if (text_in is not None) and (text_in not in stderr):
            msg = "The content of 'text_in_stderr' parameter, '{}', was not located in the output:\n{}"
            self.error(msg, text_in, stderr)

        text_not_in = self.getParam('text_not_in_stderr')
        if (text_not_in is not None) and (text_not_in in stderr):
            msg = "The content of 'text_not_in_stderr' parameter, '{}', was located in the output:\n{}"
            self.error(msg, text_in, stderr)
