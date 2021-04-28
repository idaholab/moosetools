import uuid
import enum
from moosetools.base import MooseObject
from .Differ import Differ

class Runner(MooseObject):
    """
    Base class for defining a task to be "run".

    The `Runner` object is designed to be as simple as possible. Child objects must override a
    single method: `execute`.
    """
    @staticmethod
    def validParams():
        params = MooseObject.validParams()
        params.setRequired('name', True)
        params.add('differs', vtype=Differ, array=True, doc="The 'Differ' object(s) to execute.")

        params.add('_unique_id', vtype=uuid.UUID, mutable=False, private=True)
        return params

    def __init__(self, params=None, controllers=None, **kwargs):
        if params is None: params = getattr(self.__class__, 'validParams')()
        for ctrl in controllers:
            params.add(ctrl.getParam('prefix'), default=ctrl.validObjectParams())
        kwargs['_unique_id'] = uuid.uuid4()
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
