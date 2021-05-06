import uuid
import enum
from moosetools.base import MooseObject
from .Differ import Differ

def make_runner(cls, controllers=None, **kwargs):
    """
    Create a `Runner` object given the *cls* with the `validObjectParams` of the *controllers*.

    The *controllers* argument, if supplied, should be an iterable of `moosetest.base.Controller`
    objects. The parameters supplied in the static `validObjectParams` method of each controller are
    added as a sub-parameter to the `validParams` of the object being instatiated, using the
    parameter name given in the "prefix" parameter of the `Controller` object.

    For example, consider the `moosetest.controllers.EnvironmentController` object, which has a
    default prefix of "env" defined and a "platform" parameter defined in the `validObjectParams`
    static function. If an instance of this type is passed into this function a sub-parameter with
    the name "env" will added, which contains the "platform" parameter.  Hence, the `Runner` object
    will contain parameters relevant to the environment that can be set.

    The *\*\*kwargs* arguments are applied to the default parameters as done for the base
    `base.MooseObject` class. Implementing the following will demonstrate that the "platform"
    parameter can be set for the `Runner` object, using the "env" prefix.

    ```python
    from moosetools import moosetest
    c = moosetest.controllers.EnvironmentController()
    r = moosetest.base.make_runner(moosetest.base.Runner, [c,], env_platform='Darwin')
    print(r)
    ```

    See `parameters.InputParameters` for details regarding getting/setting values of a
    sub-parameter.
    """
    params = cls.validParams()

    for ctrl in controllers or []:
        for ctrl in controllers or []:
            params.add(ctrl.getParam('prefix'), default=ctrl.validObjectParams())
    return cls(params, **kwargs)

class Runner(MooseObject):
    """
    Base class for defining a task to be "run", via the `moosetest.run` function.

    The `Runner` object is designed to be as simple as possible. Child objects must override a
    single method: `execute`.
    """
    @staticmethod
    def validParams():
        params = MooseObject.validParams()
        params.setRequired('name', True)
        params.add('differs', vtype=Differ, array=True,
                   doc="The 'Differ' object(s) to execute after execution of this object.")
        return params

    def execute(self):
        """
        Override this method to define the task to be "run".

        This method is called by the `TestCase` object that expects a return code. The
        return code is not analyzed and may be non-zero. The code, along with the sys.stdout and
        sys.stderr, are passed to any `Differ` object(s) supplied to in the "differs" input
        parameter.

        Refer to `moosetools.base.TestCase` for how this function is called and
        `moosetools.moosetest.runners.RunCommand` for an example implementation.
        """
        raise NotImplementedError("The 'execute' method must be overridden.")
