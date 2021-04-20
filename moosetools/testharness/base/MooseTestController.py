import io
import platform
import logging
from moosetools.base import MooseObject

class MooseTestController(MooseObject):
    """


    """

    @staticmethod
    def validParams():
        params = MooseObject.validParams()
        params.add('platform', array=True, allow=('Linux', 'Darwin', 'Windows'),
                   doc="Limit the execution to the supplied platform(s).")
        return params

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('name', self.__class__.__name__)
        MooseObject.__init__(self, *args, **kwargs)
        self.__runnable = True

    def isRunnable(self):
        return self.__runnable

    def skip(self, *args, **kwargs):
        self.__runnable = False
        self.warning(*args, **kwargs)

    def execute(self, obj):
        skip = False
        self.debug("Checking that '{}'is able to execute.", obj.name())
        sys_platform = platform.system()
        self.debug('platform.system() = {}', repr(sys_platform))
        pf = obj.getParam('env_platform')
        if (pf is not None) and (sys_platform not in pf):
            self.skip('{} not in {}', repr(sys_platform), repr(platform))
