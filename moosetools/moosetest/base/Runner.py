#* This file is part of MOOSETOOLS repository
#* https://www.github.com/idaholab/moosetools
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moosetools/blob/main/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html

import os
import fnmatch
from moosetools import mooseutils
from moosetools.parameters import InputParameters
from .MooseTestObject import MooseTestObject
from .Differ import Differ


def make_runner(cls, controllers=None, **kwargs):
    """
    Create a `Runner` object given the *cls* with the `validObjectParams` of the *controllers*.

    The *controllers* argument, if supplied, should be an iterable of `moosetest.base.Controller`
    objects. The parameters supplied in the static `validObjectParams` method of each controller are
    added as a sub-parameter to the `validParams` of the object being instatiated, using the
    parameter name given in the "prefix" parameter of the `Controller` object.

    For example, consider the `moosetest.controllers.EnvironmentController` object, which has a
    default prefix of "env" defined and a "platform" parameter defined in the `validObjectParams`
    static function. If an instance of this type is passed into this function a sub-parameter with
    the name "env" will added, which contains the "platform" parameter.  Hence, the `Runner` object
    will contain parameters relevant to the environment that can be set.

    The *\*\*kwargs* arguments are applied to the default parameters as done for the base
    `core.MooseObject` class. Implementing the following will demonstrate that the "platform"
    parameter can be set for the `Runner` object, using the "env" prefix.

    ```python
    from moosetools import moosetest
    c = moosetest.controllers.EnvironmentController()
    r = moosetest.base.make_runner(moosetest.base.Runner, [c,], env_platform='Darwin')
    print(r)
    ```

    See `parameters.InputParameters` for details regarding getting/setting values of a
    sub-parameter.
    """
    params = cls.validParams()
    for ctrl in controllers or []:
        params.add(ctrl.getParam('prefix'), default=ctrl.validObjectParams())
    return cls(params, **kwargs)


class Runner(MooseTestObject):
    """
    Base class for defining a task to be "run", via the `moosetest.run` function.

    The `Runner` object is designed to be as simple as possible. Child objects must override a
    single method: `execute`.

    !alert info title=Working Directory
    A `Runner` object is expected to be executed from within a `TestCase` object. In particular, when
    executed the working directory is set to "working_dir" parameter. As such, the use of
    `os.getcwd()` is expected to be correct within this object.
    """
    @staticmethod
    def isDirectory(path):
        """
        Helper for verify function.

        Using 'os.path.isdir' directly yields problems when testing with mock.
        """
        return os.path.isdir(path)

    @staticmethod
    def validParams():
        params = MooseTestObject.validParams()
        params.setRequired('name', True)
        params.add('differs',
                   vtype=Differ,
                   array=True,
                   doc="The 'Differ' object(s) to execute after execution of this object.")

        params.add(
            'working_dir',
            vtype=str,
            default=os.getcwd(),
            verify=(Runner.isDirectory, "The supplied working directory must exist."),
            doc=
            "The working directory for the execution of this `Runner` object. This parameter is automatically utilized when running the object via a `moosetest.run` function."
        )

        # Parameters associated with file names
        params.add(
            'file',
            default=InputParameters(),
            doc="Parameters for managing file(s) associated with execution of the `Runner` object.")
        f_params = params.getValue('file')
        f_params.add(
            'names',
            vtype=str,
            array=True,
            doc=
            "File name(s) that are expected to be created during execution of this object. The file(s) listed here are joined with the 'filenames' parameter from each `Differ` object. The combined set is what is used for associated error checking."
        )

        f_params.add(
            'check_created',
            vtype=bool,
            default=True,
            doc=
            "Check that all files created are accounted for in the 'names' parameter of this `Runner` object and/or associated `Differ` objects."
        )

        f_params.add(
            'clean',
            vtype=bool,
            default=True,
            doc=
            "Delete pre-existing file names defined in the 'names' parameter of this `Runner` object and/or associated `Differ` objects before calling the `execute` method."
        )

        f_params.add(
            'ignore_patterns',
            vtype=str,
            array=True,
            doc=
            "File/path patterns to ignore when inspecting created files (see 'check_created'). The python `fnmatch` module (https://docs.python.org/3/library/fnmatch.html) is used for comparing files."
        )

        return params

    def __init__(self, *args, **kwargs):
        MooseTestObject.__init__(self, *args, **kwargs)
        self.__expected_files = None
        self.__pre_execute_files = None

    def preExecute(self):
        """
        Called prior to execution of this object.

        Performs checks regarding the files expected to be created during execution.
        """
        self._preExecuteExpectedFiles()

    def postExecute(self):
        """
        Called after execution of this object.

        This method is always called, even if `preExecute` and/or `execute` raises an exception or
        results in an error.

        Performs checks that the expected files were created.
        """
        self._postExecuteExpectedFiles()

    def execute(self):
        """
        Override this method to define the task to be "run".

        This method is called by the `TestCase` object that expects a return code. The
        return code is not analyzed and may be non-zero. The code, along with the sys.stdout and
        sys.stderr, are passed to any `Differ` object(s) supplied to in the "differs" input
        parameter.

        Refer to `moosetools.core.TestCase` for how this function is called and
        `moosetools.moosetest.runners.RunCommand` for an example implementation.
        """
        raise NotImplementedError("The 'execute' method must be overridden.")

    def _preExecuteExpectedFiles(self):
        """
        Prepare for inspection of expected file prior to execution.
        """

        # Create set of expected files from this object and Differ objects
        self.__expected_files = self._getExpectedFiles()

        # Check that the file is not under version control
        root_dir = mooseutils.git_root_dir()
        if root_dir:
            git_files = set(mooseutils.git_ls_files() or root_dir)
            intersect = git_files.intersection(self.__expected_files)
            if intersect:
                msg = "The following file(s) are being tracked with 'git', thus cannot be expected to be created by the execution of this object:\n  {}."
                self.error(msg, '\n  '.join(intersect))
                return

        # Remove expected output
        if self.getParam('file', 'clean'):
            for fname in self.__expected_files:
                if os.path.isfile(fname):
                    self.info("Removing file: {}", fname)
                    os.remove(fname)

        # Check that expected files do not exist
        exist = [fname for fname in self.__expected_files if os.path.isfile(fname)]
        if exist:
            msg = "The following files(s) are expected to be created, but they already exist:\n  {}"
            self.error(msg, '\n  '.join(exist))
            return

        # Store directory content
        if self.getParam('file', 'check_created'):
            self.__pre_execute_files = set(os.listdir())

    def _postExecuteExpectedFiles(self):
        """
        Inspect expected file after execution.
        """

        # check that expected files exist
        do_not_exist = [fname for fname in self.__expected_files if not os.path.isfile(fname)]
        if do_not_exist:
            msg = "The following file(s) were not created as expected:\n  {}"
            self.error(msg, '\n  '.join(do_not_exist))

        # check for other files
        if self.__pre_execute_files is not None:
            post_execute_files = set(os.listdir())

            # remove ignored pattern(s)
            ignore_patterns = self.getParam('file', 'ignore_patterns') or tuple()
            for pattern in ignore_patterns:
                post_execute_files -= set(fnmatch.filter(post_execute_files, pattern))

            diff = post_execute_files.difference(self.__pre_execute_files)
            if diff and set(self.__expected_files) != diff:
                msg = "The following file(s) were created but not expected:\n  {}"
                self.error(msg, '\n  '.join(diff.difference(set(self.__expected_files))))

    def _getExpectedFiles(self):
        """
        Build the list of expected files.
        """
        expected = set(self.getParam('file', 'names') or tuple())
        for differ in self.getParam('differs') or set():
            expected |= set(differ.getParam('file', 'names') or tuple())
        return expected
