from moosetools.base import MooseObject

class Tester(MooseObject):
    def __init__(self, *args, **kwargs):
        MooseObject.__init__(self, *args, **kwargs)

    def execute(self, exitcode, stdout, stderr):
        pass
