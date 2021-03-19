#* This file is part of the MOOSE framework
#* https://www.mooseframework.org
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moose/blob/master/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html
import sys
import logging
import parameters
from .MooseException import MooseException

class MooseObject(object):
    """
    Base for all objects in moosetools package.

    The purpose of this class it to provide a universal design for the classes in the various
    objects in the moosetools package.

    The static `validParams` function provides a consistent means for assigning arbitrary parameters
    to an object with the ability to perform type checking, verification, and documentation. This is
    accomplished by encapsulating an InputParameters object within the MooseObject. See
    `InputParameters` documentation for further information.

    A `MooseObject` also contains its own logger (using standard python logging package), with
    methods for reporting information, warnings, and errors. See `MooseObject.info` for further
    information.

    When constructing a MooseObject the `validParams` function is automatically called, which
    populates the defaults for the object parameters. Then the *\*\*kwargs* are passed to the
    `InputParameters.update` method before `InputParameters.validate` is called. Again, refer to
    `InputParameters` documentation for further information.
    """

    @staticmethod
    def validParams():
        params = parameters.InputParameters()
        params.add('name', vtype=str, doc="The name of the object.")
        return params

    def __init__(self, **kwargs):
        self.__logger = logging.getLogger(self.__class__.__module__)
        self._parameters = getattr(self.__class__, 'validParams')()
        self._parameters.update(**kwargs)
        self._parameters.validate()

    def name(self):
        """
        Return the "name" parameter, which by default is unset and thus will return `None`.
        """
        return self.getParam('name')

    def parameters(self):
        """
        Return the `InputParameters` instance for this `MooseObject`.
        """
        return self._parameters

    def info(self, *args, **kwargs):
        """
        Log a message with `logging.INFO` level, see `log`.
        """
        self.log(logging.INFO, *args, **kwargs)

    def debug(self, *args, **kwargs):
        """
        Log a message with `logging.INFO` level, see `log`.
        """
        self.log(logging.DEBUG, *args, **kwargs)

    def warning(self, *args, **kwargs):
        """
        Log a message with `logging.WARNING` level, see `log`.
        """
        self.log(logging.WARNING, *args, **kwargs)

    def error(self, *args, **kwargs):
        """
        Log a message with `logging.ERROR` level, see `log`.
        """
        self.log(logging.ERROR, *args, **kwargs)

    def critical(self, *args, **kwargs):
        """
        Log a message with `logging.CRITICAL` level, see `log`.
        """
        self.log(logging.CRITICAL, *args, **kwargs)

    def exception(self, *args, **kwargs):
        """
        Log a message with `logging.EXCEPTION` level, see `log`.

        As noted in "logging" package documentation, this should be only used within exception
        handling. That is, when an exception occurs and is caught this method should be used to
        report it.

        By default this enables the "exc_info" flag passed to `log` and uses `logging.CRITICAL`
        level.
        """
        assert sys.exc_info() != (None, None, None), "No Exception occurred."
        kwargs.setdefault('exc_info', True)
        self.log(logging.CRITICAL, *args, **kwargs)

    def log(self, level, message, *args, exc_info=False, stack_info=False, extra=None, **kwargs):
        """
        General logging function.

        The *level* should be a valid log level as defined in the "logging" package (e.g.,
        `logging.DEBUG`).  The supplied *message* is a string that all *\*args* and `*\*\*kwargs* are
        applied using the built-in python `format` function.

        The *exc_info*, *stack_info*, and *extra* keyword arguments are passed to the "logging"
        package. Please refer to this package for further information. In general, the *exc_info*
        option is not needed, it is automatically set to the correct value by the `exception` method
        that is designed for exception handling.
        """
        assert isinstance(message, str), "The supplied 'message' must be a python `str` type."
        name = self.getParam('name')
        message = message.format(*args, **kwargs)
        if name is not None: message = '({}): {}'.format(name, message)
        self.__logger.log(level, message, exc_info=exc_info, stack_info=stack_info, extra=extra)
        return message # see `exception` method for the reason behind this

    def isParamValid(self, *args):
        """
        Test if the given parameter is valid (i.e., not None).

        Refer to `InputParameters.isValid` for further information.
        """
        return self._parameters.isValid(*args)

    def getParam(self, *args):
        """
        Return the value of parameter.

        Refer to `InputParameters.get` for further information.
        """
        return self._parameters.get(*args)
