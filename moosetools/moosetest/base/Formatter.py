from moosetools.base import MooseObject

class Formatter(MooseObject):

    @staticmethod
    def validParams():
        params = MooseObject.validParams()
        return params

    def __init__(self, *args, **kwargs):
        MooseObject.__init__(self, *args, **kwargs)

    def formatState(self, obj, state, tcinfo):
        raise NotImplementedError()

    def formatResult(self, obj, state, rcode, out, err, tcinfo):
        raise NotImplementedError()
