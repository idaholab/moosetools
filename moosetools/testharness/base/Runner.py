from .MooseTestObject import MooseTestObject

class Runner(MooseTestObject):
    """

    """

    @staticmethod
    def validParams():
        params = MooseTestObject.validParams()
        return params

    def __init__(self, *args, **kwargs):
        MooseTestObject.__init__(self, *args, **kwargs)

    def execute(self):
        raise NotImplementedError()
