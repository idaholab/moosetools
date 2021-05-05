import io
import platform
import logging
from moosetools.parameters import InputParameters
from moosetools.moosetest.base import Controller

class EnvironmentController(Controller):
    """
    Controls if a `moosetest.base.Runner` or `moosetest.base.Differ` should execute.

    Refer to `moosetest.base.Runner` documentation for how these are utilized.
    """
    @staticmethod
    def validParams():
        params = Controller.validParams()
        params.set('prefix', 'env')
        return params

    @staticmethod
    def validObjectParams():
        """
        Return an `parameters.InputParameters` object to be added to a sub-parameter of an object
        with the name given in the "prefix" parameter
        """
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

    def execute(self, obj, params):
        self.debug("Checking that '{}'is able to execute.", obj.name())

        sys_platform = platform.system()
        self.debug('platform.system() = {}', repr(sys_platform))
        pf = params.get('platform')
        if (pf is not None) and (sys_platform not in pf):
            self.skip(obj, '{} not in {}', repr(sys_platform), repr(pf))
            self.debug("The system platform {} is not in the allowable platforms list of {}",
                       repr(sys_platform), repr(pf))
