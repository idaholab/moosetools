#* This file is part of MOOSETOOLS repository
#* https://www.github.com/idaholab/moosetools
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moosetools/blob/main/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html

import io
import platform
import logging
from moosetools.parameters import InputParameters
from .MooseTestObject import MooseTestObject


class Controller(MooseTestObject):
    """
    An object to dictate if a `moosetest.base.Runner` or `moosetest.base.Differ` should execute.

    The parameters defined in the static `validObjectParams` are applied to the `validParams` of
    a `moosetest.base.Runner` or `moosetest.base.Differ`. Refer to `moosetest.base.Runner`
    documentation for how these are utilized.

    The idea behind this concept is to allow for these checks to be shared among custom objects
    while allowing basic functionality to be included in the moosetools repository.

    The `Controller` objects within this repository are added by default, custom objects can be
    added by the [Controllers] block with the '.moosetools' configure file.
    """
    AUTO_BUILD = False

    @staticmethod
    def validParams():
        params = MooseTestObject.validParams()
        params.add('prefix',
                   vtype=str,
                   required=True,
                   mutable=False,
                   doc="Set the sub-parameters prefix of the controller.")
        return params

    @staticmethod
    def validObjectParams():
        """
        Return an `parameters.InputParameters` object to be added to a sub-parameter of an object
        with the name given in the "prefix" parameter.
        """
        params = InputParameters()
        return params

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('name', self.__class__.__name__)
        MooseTestObject.__init__(self, *args, **kwargs)
        self.__runnable = True

    def reset(self):
        """
        Reset the "runnable" state, the skip reasons, and the log status.
        """
        self.__runnable = True
        MooseTestObject.reset(self)

    def isRunnable(self):
        """
        Return `True` if the `execute` method of the object provided to the `execute` method of this
        class should be called.

        See `moosetest.base.TestCase` for details of how this method is used.
        """
        return self.__runnable

    def skip(self, msg, *args, **kwargs):
        """
        Indicate that the object passed to the `execute` method of this class should not run.

        The supplied *msg* is formatted with the `format` built-in with the supplied *\*args* and
        *\*\*kwargs* arguments.

        !alert tip title=Keep the message short
        The supplied message to this function should be as short as possible, since the content
        of the message is printed on a single line with the test name. If more information is needed
        the standard logging methods ('info', 'debug', etc. should be used). It is recommended that
        detailed messages be logged with the 'debug' method. For an example please refer to the
        `moosetest.controllers.EnvironmentController` for an example.
        """
        self.__runnable = False
        self.reason(msg, *args, **kwargs)

    def execute(self, obj, params):
        """
        Determine if the supplied *obj*, which should be a `moosetest.base.Runner` or
        `moosetest.base.Differ` object, should run. The *params* are the sub-parameters from object
        add by this `Controller` object.

        This method must be overridden in a child class. The `skip` method should be called to
        indicate that the supplied object should not be run.

        See `moosetest.base.TestCase` for details of how this method is used.
        """
        raise NotImplementedError("The 'execute' method must be overridden.")
