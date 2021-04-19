import io
import platform
import logging
from moosetools.base import MooseObject

class Runner(MooseObject):
    """

    Runner state tracked by TestCase, run via subprocess by run all output handled via log stream.
    """

    @staticmethod
    def validParams():
        params = MooseObject.validParams()
        params.add('platform', array=True, allow=('Linux', 'Darwin', 'Windows'),
                   doc="Limit the execution to the supplied platform(s).")
        params.add('output_progress_interval', vtype=int, default=5, mutable=False,
                   doc="The during between printing the 'RUNNING' progress message.")

        #params.add('_stream', private=True, mutable=False, default=io.StringIO())
        return params

    def __init__(self, *args, **kwargs):
        MooseObject.__init__(self, *args, **kwargs)
        #handler = self.getParam('_handler')
        #handler.setStream(self.getParam('_stream'))

        self.__runnable = True # toggle for isRunnable method; a call to skip flips it

    def getStream(self):
        return 'foo'
    #    return self.getParam('_stream').getvalue()

    def isRunnable(self):
        return self.__runnable

    def skip(self, *args, **kwargs):
        self.__runnable = Falsesel
        self.info(*args, **kwargs)

    def initialize(self):
        self.debug('Checking that TestCase is able to execute.')
        sys_platform = platform.system()
        self.debug('platform.system() = {}', repr(sys_platform))
        pf = self.getParam('platform')
        if (pf is not None) and (sys_platform not in pf):
            self.skip('{} not in {}', repr(sys_platform), repr(platform))

    def execute(self):
        # returns code, stdout, stderr
        raise NotImplementedError()
