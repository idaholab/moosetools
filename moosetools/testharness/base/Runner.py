from moosetools.base import MooseObject
class Runner(MooseObject):
    """

    """

    @staticmethod
    def validParams():
        params = MooseObject.validParams()
        params.setRequired('name', True)
        return params

    def __init__(self, *args, **kwargs):
        MooseObject.__init__(self, *args, **kwargs)

    def execute(self):
        raise NotImplementedError()
