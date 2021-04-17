#* This file is part of MOOSETOOLS repository
#* https://www.github.com/idaholab/moosetools
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moosetools/blob/main/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html

import sys
import logging
from moosetools import mooseutils
from moosetools import parameters

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
    __MooseObject_counter__ = -1


    @staticmethod
    def validParams():
        params = parameters.InputParameters()
        params.add(
            'name',
            vtype=str,
            doc=
            "The name of the object. If using the factory.Parser to build objects from an input file, this will be automatically set to the block name in the input file."
        )

        levels = tuple(logging._nameToLevel.keys())
        params.add('log_level', default='INFO', vtype=str, allow=levels, mutable=False,
                   doc="Set the logging level, see python 'logging' package for details.")
        params.add('log_status_error_level', default='ERROR', vtype=str, allow=levels,
                   doc="Set the allowable logging level for the status method to return an error code.")

        params.add('_logger', vtype=logging.Logger, mutable=False, private=True)
        return params

    def __init__(self, params=None, **kwargs):
        type(self).__MooseObject_counter__ += 1
        self.__log_counts = {key: 0 for key in logging._levelToName.keys()}
        self._parameters = params or getattr(self.__class__, 'validParams')()
        self._parameters.update(**kwargs)
        self._parameters.set('_moose_object', self)
        self._parameters.validate()  # once this is called, the mutable flag becomes active

        # Create a unique logger for this object
        logger_name = '{}.{}'.format(self.__class__.__module__, type(self).__MooseObject_counter__)
        logger = self.getParam('_logger') or logging.getLogger(logger_name)
        logger.setLevel(self.getParam('log_level'))
        self.__logger = logger

    def __del__(self):
        type(self).__MooseObject_counter__ -= 1

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

    def reset(self, *levels):
        """
        Reset the log counts.

        If *levels* is provided only the level provided in *levels* will be reset, otherwise all
        counts are returned to zero.
        """
        if not levels: levels = self.__log_counts.keys()
        for lvl in levels:
            if lvl not in self.__log_counts:
                msg = "Attempting to reset logging count for '{}' level, but the level does not exist."
                self.error(msg, lvl)
                continue
            self.__log_counts[lvl] = 0

    def status(self):
        """
        Return 1 if logging messages exist.

        By default only the logging.ERROR and logging.CRITICAL levels are
        considered. If *levels* is provided the levels given are used.
        """
        level = logging._nameToLevel[self.getParam('log_status_error_level')]
        count = 0
        for lvl, cnt in self.__log_counts.items():
            if lvl >= level:
                count += cnt
        return int(count > 0)

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

        Similar to as noted in "logging" package documentation for the "logging" `exception`
        function, this should be only used within exception handling. That is, when an exception
        occurs and is caught this method should be used to report it.

        By default this enables the "exc_info" flag passed to `log` and uses `logging.CRITICAL`
        level.
        """
        assert sys.exc_info() != (
            None, None, None), "No Exception raised, see `MooseObject.exception` for help."
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
        assert isinstance(
            message,
            str), "The supplied 'message' must be a python `str` type, see `MooseObject.log`."
        name = self.getParam('name')
        message = message.format(*args, **kwargs)
        #if extra is None: extra = dict()
        #extra.setdefault('mooseobject_name', self.name()
        self.__logger.log(level, message, exc_info=exc_info, stack_info=stack_info, extra=extra)
        self.__log_counts[level] += 1

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
