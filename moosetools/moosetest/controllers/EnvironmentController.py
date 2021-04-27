import io
import platform
import logging
from moosetools.parameters import InputParameters
from moosetools.moosetest.base import Controller

class EnvironmentController(Controller):
    """
    Controls if a `TestCase` should execute based on the operating environment.
    """

    @staticmethod
    def validParams():
        params = Controller.validParams()
        params.set('prefix', 'env')
        return params

    @staticmethod
    def validObjectParams():
        params = Controller.validObjectParams()
        params.add('platform', array=True, allow=('Linux', 'Darwin', 'Windows'),
                   doc="Limit the execution to the supplied platform(s).")
        params.add('python_minimum_version', vtype=str,
                   doc="The minimum python version supported.")
        params.add('python_maximum_version', vtype=str,
                   doc="The maximum python version supported.")
        return params

    def __init__(self, *args, **kwargs):
        Controller.__init__(self, *args, **kwargs)

    def execute(self, params):
        self.debug("Checking that '{}'is able to execute.", obj.name())

        sys_platform = platform.system()
        self.debug('platform.system() = {}', repr(sys_platform))
        pf = params.get('platform')
        if (pf is not None) and (sys_platform not in pf):
            self.skip('{} not in {}', repr(sys_platform), repr(platform))
