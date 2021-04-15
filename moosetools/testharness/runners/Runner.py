import io
import platform
import logging
from moosetools.base import MooseObject

class Runner(MooseObject):

    @staticmethod
    def validParams():
        params = MooseObject.validParams()
        params.add('platform', array=True, allow=('Linux', 'Darwin', 'Windows'),
                   doc="Limit the execution to the supplied platform(s).")
        params.add('_stream', private=True, mutable=False, default=io.StringIO())
        return params

    def __init__(self, *args, **kwargs):
        MooseObject.__init__(self, *args, **kwargs)

        handler = self.getParam('_handler')
        handler.setStream(self.getParam('_stream'))

    def getStream(self):
        return self.getParam('_stream').getvalue()

    def skip(self, *args, **kwargs):
        self.warning(*args, **kwargs)

    def init(self):
        self.debug('Initializing TestCase:')
        sys_platform = platform.system()
        self.debug('platform.system() = {}', repr(sys_platform))
        pf = self.getParam('platform')
        if (pf is not None) and (sys_platform not in pf):
            self.skip('{} not in {}', repr(sys_platform), repr(platform))

    def execute(self):
        raise NotImplementedError()

    #def run(self):
    #    self.reset()
    #    self.setup()
    #    return self.status()
