import io
import copy
import platform
import logging
from moosetools.base import MooseObject


def make_differ(cls, controllers=None, **kwargs):
    """
    Create a `Differ` object given the *cls* with the `validObjectParams` of the *controllers*.

    This function operates in the same fashion as `moosetools.base.make_runner`.
    """
    params = cls.validParams()
    for ctrl in controllers or []:
        params.add(ctrl.getParam('prefix'), default=ctrl.validObjectParams())
    return cls(params, **kwargs)


class Differ(MooseObject):
    """
    Base class for analyzing the results from a `moosetest.base.Runner` after a "run".

    The `Differ` object is designed to be as simple as possible. Child objects must override a
    single method: `execute`.
    """
    @staticmethod
    def validParams():
        params = MooseObject.validParams()
        params.setRequired('name', True)
        return params

    def execute(self, rcode, stdout, stderr):
        """
        Override this method to define the comparison to be performed.

        This method is called by the `TestCase` object that expects a return code. The
        return code is not analyzed and may be non-zero. The *rcode*, *stdout*, and *stderr*
        arguments are the output for the `moosetest.base.Runner` object that was executed
        prior to running this object.

        Refer to `moosetools.base.TestCase` for how this function is called and
        `moosetools.moosetest.differs.TextDiff` for an example implementation.
        """
        raise NotImplementedError("The 'execute' method must be overridden.")
