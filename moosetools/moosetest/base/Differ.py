import io
import platform
import logging
from moosetools.base import MooseObject

class Differ(MooseObject):
    """

    """

    @staticmethod
    def validParams():
        params = MooseObject.validParams()
        params.setRequired('name', True)
        params.add('_runner_name', vtype=str, private=True)
        return params

    def __init__(self, *args, **kwargs):
        MooseObject.__init__(self, *args, **kwargs)

    def execute(self, rcode, stdout, stderr):
        raise NotImplementedError()
