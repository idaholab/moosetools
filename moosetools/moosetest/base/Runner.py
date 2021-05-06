import uuid
import enum
from moosetools.base import MooseObject
from .Differ import Differ

class Runner(MooseObject):
    """
    Base class for defining a task to be "run", via the `moosetest.run` function.

    The `Runner` object is designed to be as simple as possible. Child objects must override a
    single method: `execute`.

    The *params* argument, if supplied, should be an `parameters.InputParameters` object otherwise
    the static `validParams` function of this class is called. The *controllers* argument, if
    supplied, should be an iterable of `moosetest.base.Controller` objects. The parameters supplied
    in the static `validObjectParams` method of each controller are added as a sub-parameter to the
    `validParams` of this object, using the parameter name given in the "prefix" parameter of the
    `Controller` object.

    For example, consider the `moosetest.controllers.EnvironmentController` object, which has a
    default prefix of "env" defined and a "platform" parameter defined in the `validObjectParams`
    static function. If an instance of this type is passed into this object a sub-parameter with the
    name "env" will added, which contains the "platform" parameter.  Hence, the `Runner` object will
    not contain parameters relevant to the environment that can be set. The *\*\*kwargs* arguments
    are applied to the default parameters as done for the base `base.MooseObject` class. Implementing
    the following will demonstrate that the "platform" parameter can be set for the `Runner` object,
    using the "env" prefix.

    ```python
    from moosetools import moosetest
    c = moosetest.controllers.EnvironmentController()
    r = moosetest.base.Runner(None, [c,], env_platform='Darwin')
    print(r)
    ```

    See `parameters.InputParameters` for details regarding getting/setting values of a
    sub-parameter.
    """
    @staticmethod
    def validParams():
        params = MooseObject.validParams()
        params.setRequired('name', True)
        params.add('differs', vtype=Differ, array=True,
                   doc="The 'Differ' object(s) to execute after execution of this object.")

        params.add('_reasons', vtype=list, private=True) # see Controller
        params.add('_unique_id', vtype=uuid.UUID, mutable=False, private=True)
        return params

    def __init__(self, params=None, controllers=None, **kwargs):
        if params is None: params = getattr(self.__class__, 'validParams')()
        for ctrl in controllers or []:
            params.add(ctrl.getParam('prefix'), default=ctrl.validObjectParams())
        kwargs['_unique_id'] = uuid.uuid4()
        kwargs['_reasons'] = list()
        MooseObject.__init__(self, params, **kwargs)

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
