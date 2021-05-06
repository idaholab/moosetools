from moosetools.base import MooseObject

class Formatter(MooseObject):
    """
    Base class for defining how the progress and results are presented during the execution of test.

    TODO: Document difference between Runner/Differ state and results as well as kwargs passed from TestCase


    Refer to `moosetest.formatters.BasicFormatter` for an example implementation.

    See `moosetest.run` and `moosetest.base.TestCase` for details regarding the use of this object.
    """
    @staticmethod
    def validParams():
        params = MooseObject.validParams()
        return params

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('name', self.__class__.__name__)
        MooseObject.__init__(self, *args, **kwargs)

    def formatRunnerState(self, **kwargs):
        raise NotImplementedError("The 'formatRunnerState' method must be overridden.")

    def formatRunnerResult(self, **kwargs):
        raise NotImplementedError("The 'formatRunnerResult' method must be overridden.")

    def formatDifferState(self, **kwargs):
       raise NotImplementedError("The 'formatDifferState' method must be overridden.")

    def formatDifferResult(self, **kwargs):
       raise NotImplementedError("The 'formatDifferResult' method must be overridden.")

    def formatComplete(self, complete, **kwargs):
        """

        """
        raise NotImplementedError("The 'formatComplete' method must be overridden.")
