import io
import platform
import logging
from moosetools.parameters import InputParameters
from moosetools.base import MooseObject

class Controller(MooseObject):
    """
    TODO: Clean this up...

    The `Controller` objects are used to dictate if the tests are able to run based on things like the
    operating environment. Each Controller object parameters are added to a sub-InputParameters for
    all test objects (i.e., Runners and Differs) upon creation of these objects. This allows test
    run controls to be added to all objects, such that each Runner and/or differ can run on
    different system configurations.

    The idea behind this concept is to allow for these checks to be shared among custom objects
    while allowing basic functionality to be included in the moosetools repository.

    The Controller objects within this repository are added by default, custom objects can be
    added by the [Controllers] block with the '.moosetools' configure file.
    """
    PREFIX = None

    @staticmethod
    def validParams():
        params = MooseObject.validParams()
        params.add('prefix', vtype=str, required=True, mutable=False,
                   doc="Set the sub-parameters prefix of the controller.")
        return params

    @staticmethod
    def validObjectParams():
        params = InputParameters()
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
        raise NotImplementedError()
