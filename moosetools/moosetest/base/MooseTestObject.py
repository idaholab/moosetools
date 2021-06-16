#* This file is part of MOOSETOOLS repository
#* https://www.github.com/idaholab/moosetools
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moosetools/blob/main/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html

from moosetools import base


class MooseTestObject(base.MooseObject):
    """
    Base object for `moosetest` objects.

    The supplies common functionality across the `Controller`, `Runner`, and `Differ` objects.

    This includes the ability to store "reasons", which are short messages that get attached to
    the formatted output of `TestCase` objects. They are added by calling the `reasons` method, which
    is designed to operate similar to the `MooseObject` logging methods (e.g., `MooseObject.error`).
    """
    @staticmethod
    def validParams():
        params = base.MooseObject.validParams()
        return params

    def __init__(self, *args, **kwargs):
        base.MooseObject.__init__(self, *args, **kwargs)
        self.__reasons = list()

    def reset(self):
        """
        Reset the the stored "reasons".
        """
        self.__reasons = list()
        base.MooseObject.reset(self)

    def getReasons(self):
        """
        Return the "reasons: messages for this object.

        The skip reasons are cleared with the `reset` method.

        See `moosetest.base.TestCase` for details of how this method is used.
        """
        return self.__reasons

    def reason(self, msg, *args, **kwargs):
        """
        Add a *msg* formatted with *\*args* and *\*\*kwargs to the list of reasons.

        This method is meant to operate in the same capacity as the logging methods (e.g., `error`).
        """
        self.__reasons.append(msg.format(*args, **kwargs))
