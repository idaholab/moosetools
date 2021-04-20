import io
import platform
import logging
from moosetools.base import MooseObject
from .MooseTestController import MooseTestController

class MooseTestObject(MooseObject):
    """

    Runner state tracked by TestCase, run via subprocess by run all output handled via log stream.
    """

    @staticmethod
    def validParams():
        params = MooseObject.validParams()
        params.setRequired('name', True)
        params.add('output_progress_interval', vtype=int, default=5, mutable=False,
                   doc="The during between printing the 'RUNNING' progress message.")
        return params

    def __init__(self, params=None, controller=None, **kwargs):
        if params is None: params = getattr(self.__class__, 'validParams')()
        params.add('env', controller or MooseTestController.validParams())
        MooseObject.__init__(self, params, **kwargs)
