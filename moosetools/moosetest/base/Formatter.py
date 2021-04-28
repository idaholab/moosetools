from moosetools.base import MooseObject

class Formatter(MooseObject):

    @staticmethod
    def validParams():
        params = MooseObject.validParams()
        return params

    def __init__(self, *args, **kwargs):
        MooseObject.__init__(self, *args, **kwargs)

    def formatComplete(self, complete, **kwargs):
        raise NotImplementedError()

    def formatRunnerState(self, obj, state, **kwargs):
        raise NotImplementedError()

    def formatRunnerResult(self, obj, state, rcode, out, err, **kwargs):
        raise NotImplementedError()

    def formatDifferState(self, obj, state, **kwargs):
        raise NotImplementedError()

    def formatDifferResult(self, obj, state, rcode, out, err, **kwargs):
        raise NotImplementedError()
