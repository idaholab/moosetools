import io
import platform
import logging
from ..base import Controller

class EnvironmentController(Controller):
    PREFIX = 'env'

    @staticmethod
    def validParams():
        params = Controller.validParams()
        params.add('platform', array=True, allow=('Linux', 'Darwin', 'Windows'),
                   doc="Limit the execution to the supplied platform(s).")
        return params

    def __init__(self, *args, **kwargs):
        Controller.__init__(self, *args, **kwargs)

    def execute(self, obj):
        self.debug("Checking that '{}'is able to execute.", obj.name())
        sys_platform = platform.system()
        self.debug('platform.system() = {}', repr(sys_platform))
        pf = obj.getParam('env_platform')
        if (pf is not None) and (sys_platform not in pf):
            self.skip('{} not in {}', repr(sys_platform), repr(platform))
