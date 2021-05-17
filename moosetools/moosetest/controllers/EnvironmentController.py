import io
import platform
import logging
#import mooseutils
import packaging.version
from moosetools import mooseutils
from moosetools.parameters import InputParameters
from moosetools.moosetest.base import Controller

class EnvironmentController(Controller):
    """
    A controller to dictate if an object should run based on the environment.
    """
    @staticmethod
    def validParams():
        params = Controller.validParams()
        params.setValue('prefix', 'env')
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
        params.add('python_required_packages', vtype=str, array=True,
                   doc="List of python packages, if any, that must exist.")
        return params

    def execute(self, obj, params):
        self.debug("Checking that '{}'is able to execute.", obj.name())

        # System information
        sys_platform = platform.system()
        self.debug('platform.system() = {}', repr(sys_platform))

        sys_py_version = platform.python_version()
        self.debug('platform.python_version() = {}', sys_py_version)

        # Platform
        pf = params.getValue('platform')
        if (pf is not None) and (sys_platform not in pf):
            self.skip('{} not in {}', repr(sys_platform), repr(pf))
            self.debug("The system platform {} is not in the allowable platforms list of {}",
                       repr(sys_platform), repr(pf))

        # Python min. version
        min_py_version = params.getValue('python_minimum_version')
        if (min_py_version is not None) and (packaging.version.parse(min_py_version) > packaging.version.parse(sys_py_version)):
            self.skip('{} > {}', min_py_version, sys_py_version)
            self.debug("The system python version {} is less then the allowed minimum version of {}",
                       sys_py_version, min_py_version)

        # Python max. version
        max_py_version = params.getValue('python_maximum_version')
        if (max_py_version is not None) and (packaging.version.parse(max_py_version) <= packaging.version.parse(sys_py_version)):
            self.skip('{} < {}', max_py_version, sys_py_version)
            self.debug("The system python version {} is greater then the allowed maximum version of {}",
                       sys_py_version, max_py_version)

        # Check python packages
        py_packages = params.getValue('python_required_packages')
        if py_packages is not None:
            missing = mooseutils.check_configuration(py_packages, message=False)
            if missing:
                self.skip('missing python package(s)')
                self.debug("Missing required python package(s): {}", ', '.join(missing))
