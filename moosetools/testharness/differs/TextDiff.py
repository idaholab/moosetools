from ..base import Differ

class TextDiff(Differ):
    @staticmethod
    def validParams():
        params = Differ.validParams()
        params.add('text_in', vtype=str, doc="Checks that the supplied text exists in the output.")
        params.add('text_not_in', vtype=str, doc="Checks that the supplied text does not exist in the output.")
        return params

    def __init__(self, *args, **kwargs):
        Differ.__init__(self, *args, **kwargs)

    def execute(self, returncode, output):
        text_in = self.getParam('text_in')
        if (text_in is not None) and (text_in not in output):
            msg = "The content of 'text_in' parameter, '{}', was not located in the output."
            self.error(msg, text_in)

        text_not_in = self.getParam('text_not_in')
        if (text_not_in is not None) and (text_not_ion in output):
            msg = "The content of 'text_not_in' parameter, '{}', was located in the output."
            self.error(msg, text_in)
