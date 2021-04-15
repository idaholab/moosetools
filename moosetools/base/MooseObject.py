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

class MooseObjectFormatter(logging.Formatter):
    """
    A formatter that is aware of the class hierarchy of the MooseDocs library.
    Call the init_logging function to initialize the use of this custom formatter.
    TODO: ChiggerFormatter or something similar (MooseDocsFormatter) should be used by all
          moosetools as should be the logging methods in ChiggerObject.
          Perhaps a "mixins" package: 'moosetools.mixins.MooseLoggerMixin' would add the log methods,
          other objects such at the AutoProperty would also go within that module
    """
    COLOR = dict(DEBUG='cyan_1',
                 INFO='white',
                 WARNING='yellow_1',
                 ERROR='red_1',
                 CRITICAL='magenta_1')

    COUNTS = dict(CRITICAL=0, ERROR=0, WARNING=0, INFO=0, DEBUG=0)

    def format(self, record):
        """Format the supplied logging record and count the occurrences."""
        self.COUNTS[record.levelname] += 1
        return record.mooseobject.logFormat(self, record)

# Setup the logging
level = dict(critical=logging.CRITICAL, error=logging.ERROR, warning=logging.warning,
             info=logging.INFO, debug=logging.DEBUG, notset=logging.NOTSET)


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
        params.add(
            'name',
            vtype=str,
            doc=
            "The name of the object. If using the factory.Parser to build objects from an input file, this will be automatically set to the block name in the input file."
        )

        params.add('log_level', default=logging.INFO, mutable=False,
                   allow=(logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL),
                   doc="Set the logging level, see python 'logging' package for details.")

        params.add('_logger', vtype=logging.Logger, mutable=False, private=True)
        params.add('_formatter', default=MooseObjectFormatter(), vtype=logging.Formatter, mutable=False, private=True)
        params.add('_handler', default=logging.StreamHandler(), vtype=logging.Handler, mutable=False, private=True)
        return params

    def __init__(self, params=None, **kwargs):
        self.__logger = logging.getLogger(self.__class__.__module__)
        self.__log_counts = {key: 0 for key in logging._levelToName.keys()}
        self._parameters = params or getattr(self.__class__, 'validParams')()
        self._parameters.update(**kwargs)
        self._parameters.set('_moose_object', self)
        self._parameters.set('_logger', self.__logger)
        self._parameters.validate()  # once this is called, the mutable flag becomes active
        formatter = self.getParam('_formatter')
        handler = self.getParam('_handler')
        handler.setFormatter(formatter)
        self.__logger.addHandler(handler)
        self.__logger.setLevel(self.getParam('log_level'))

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

    def status(self, *levels):
        """
        Return 1 if logging messages exist.

        By default only the logging.ERROR and logging.CRITICAL levels are
        considered. If *levels* is provided the levels given are used.
        """
        if not levels: levels = [logging.ERROR, logging.CRITICAL]
        count = 0
        for lvl in levels:
            if lvl not in self.__log_counts:
                msg = "Attempting to get logging count for '{}' level, but the level does not exist."
                self.error(msg, lvl)
                continue
            count += self.__log_counts[lvl]
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
        log_extra = {'mooseobject':self}
        if extra is not None: log_extra.update(extra)
        self.__logger.log(level, message, exc_info=exc_info, stack_info=stack_info, extra=log_extra)
        self.__log_counts[level] += 1

    def logFormat(self, formatter, record):
        """
        Called by formatter to produce log output.
        """
        name = self.name() or record.levelname
        msg = '{} {}'.format(mooseutils.color_text(name + ':', formatter.COLOR[record.levelname]),
                             logging.Formatter.format(formatter, record))
        return msg

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
