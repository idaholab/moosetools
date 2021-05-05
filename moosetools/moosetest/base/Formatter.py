from moosetools.base import MooseObject

class Formatter(MooseObject):
    """
    Base class for defining how the progress and results are presented during the execution of test.

    Refer to `moosetest.formatters.BasicFormatter` for an example implementation.

    See `moosetest.run` and `moosetest.base.TestCase` for details regarding the use of this object.
    """


    @staticmethod
    def validParams():
        params = MooseObject.validParams()
        return params

    def __init__(self, *args, **kwargs):
        MooseObject.__init__(self, *args, **kwargs)

    def formatComplete(self, complete, **kwargs):
        """

        """
        raise NotImplementedError("The 'formatComplete' method must be overridden.")

    def formatRunnerState(self, **kwargs):
        raise NotImplementedError("The 'formatRunnerState' method must be overridden.")

    def formatRunnerResult(self, **kwargs):
        raise NotImplementedError("The 'formatRunnerResult' method must be overridden.")

    def formatDifferState(self, **kwargs):
       raise NotImplementedError("The 'formatDifferState' method must be overridden.")

    def formatDifferResult(self, **kwargs):
       raise NotImplementedError("The 'formatDifferResult' method must be overridden.")
