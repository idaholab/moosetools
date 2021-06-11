#* This file is part of MOOSETOOLS repository
#* https://www.github.com/idaholab/moosetools
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moosetools/blob/main/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html

import io
import copy
import platform
import logging
from moosetools.base import MooseObject


def make_differ(cls, controllers=None, **kwargs):
    """
    Create a `Differ` object given the *cls* with the `validObjectParams` of the *controllers*.

    This function operates in the same fashion as `moosetools.base.make_runner`.
    """
    params = cls.validParams()
    for ctrl in controllers or []:
        params.add(ctrl.getParam('prefix'), default=ctrl.validObjectParams())
    return cls(params, **kwargs)


class Differ(MooseObject):
    """
    Base class for analyzing the results from a `moosetest.base.Runner` after a "run".

    The `Differ` object is designed to be as simple as possible. Child objects must override a
    single method: `execute`.
    """
    @staticmethod
    def validParams():
        params = MooseObject.validParams()
        params.setRequired('name', True)

        params.add(
            'base_dir',
            vtype=str,
            doc=
            "The base directory for the relative paths of the supplied names in the 'filenames' parameter."
        )
        params.add('filenames',
                   vtype=str,
                   array=True,
                   doc="Filename(s) to be inspected by this object.")
        return params

    def preExecute(self):
        """
        Called prior to execution of this object.
        """
        pass

    def postExecute(self):
        """
        Called after execution of this object.

        This method is always called, even if `preExecute` and/or `execute` raises an exception or
        results in an error.
        """
        pass

    def execute(self, rcode, stdout, stderr):
        """
        Override this method to define the comparison to be performed.

        This method is called by the `TestCase` object that expects a return code. The
        return code is not analyzed and may be non-zero. The *rcode*, *stdout*, and *stderr*
        arguments are the output for the `moosetest.base.Runner` object that was executed
        prior to running this object.

        Refer to `moosetools.base.TestCase` for how this function is called and
        `moosetools.moosetest.differs.ConsoleDiff` for an example implementation.
        """
        raise NotImplementedError("The 'execute' method must be overridden.")
