#* This file is part of MOOSETOOLS repository
#* https://www.github.com/idaholab/moosetools
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moosetools/blob/main/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html

import os
import contextlib


class CurrentWorkingDirectory(contextlib.AbstractContextManager):
    """
    A context for temporarily changing the working directory to *working_dir*.
    """
    def __init__(self, working_dir):

        if not os.path.isdir(working_dir):
            raise OSError("The supplied working directory does not exist: {}".format(working_dir))

        self.__external_working_dir = os.getcwd()
        self.__internal_working_dir = working_dir

    @property
    def external(self):
        """
        Return the directory for the working directory external of the context.
        """
        return self.__external_working_dir

    @property
    def internal(self):
        """
        Return the directory for the working directory internal of the context.
        """
        return self.__internal_working_dir

    def __enter__(self):
        """
        Set the working directory to the supplied value from the constructor upon entering context.
        """
        os.chdir(self.__internal_working_dir)
        return super().__enter__()

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Restore the working directory to the value outside the context and re-raise any exception.
        """
        os.chdir(self.__external_working_dir)
        if exc_type is not None:
            raise  # re-raise current exception (https://docs.python.org/3/library/exceptions.html)
