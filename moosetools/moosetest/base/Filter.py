#* This file is part of MOOSETOOLS repository
#* https://www.github.com/idaholab/moosetools
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moosetools/blob/main/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html

from moosetools import core


class Filter(core.MooseObject):
    """
    An object to dictate if a `Runner` should be filtered out (i.e., removed) execution.

    See `moosetest.run` for use.
    """
    AUTO_BUILD = False

    @staticmethod
    def validParams():
        params = core.MooseObject.validParams()
        return params

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('name', self.__class__.__name__)
        core.MooseObject.__init__(self, *args, **kwargs)
        self.__remove = False  # by default the runner will not be filtered out (i.e., removed)

    def reset(self):
        """
        Reset the remove and error status for the object.
        """
        self.__remove = False
        core.MooseObject.reset(self)

    def remove(self):
        """
        Indicate that a runner object should be removed.

        This method should be called within the `execute` method, if the runner supplied should
        be removed.
        """
        self.__remove = True

    def isRemoved(self):
        """
        Return True if the `remove` method was called.
        """
        return self.__remove

    def apply(self, runner):
        """
        Return False if the filter should remove the supplied *runner* should be removed.

        See `moosetest.run._apply_filters` for use.
        """

        self.reset()
        self.execute(runner)

        if self.status():
            msg = "An error occurred, on the filter, within the `execute` method of the {} filter with '{}' runner.".format(
                self.name(), runner.name())
            raise RuntimeError(msg)
        if runner.status():
            msg = "An error occurred, on the runner, within the `execute` method of the {} filter with '{}' runner.".format(
                self.name(), runner.name())
            raise RuntimeError(msg)

        return self.isRemoved()

    def execute(self, runner):
        """
        Determine if the supplied *runner*, which should be a `moosetest.base.Runner` object,
        should be removed from the execution of tests.
        """
        raise NotImplementedError("The 'execute' method must be overridden.")
