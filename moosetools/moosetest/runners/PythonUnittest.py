#* This file is part of MOOSETOOLS repository
#* https://www.github.com/idaholab/moosetools
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moosetools/blob/main/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html

import os
import io
import unittest
from unittest import mock
import subprocess
from .ExecuteCommand import ExecuteCommand


class PythonUnittest(ExecuteCommand):
    """
    A Runner that loads and executes python unittests within the moosetest system.
    """
    @staticmethod
    def validParams():
        params = ExecuteCommand.validParams()
        params.setRequired('command', False)

        params.add('input', required=False, vtype=str,
                   doc="List of python input files containing unittests to execute.")
        params.add('test_cases', vtype=str, array=True,
                   doc="List of specific test cases to execute, by default all test cases in the files are loaded.")
        #params.add('buffer', False, "Equivalent to passing -b or --buffer to the unittest.")
        #params.add('separate', False, "Run each test in the file in a separate subprocess")
        return params

    def execute(self):
        command = ['python', '-m', 'unittest', '--buffer', '--verbose']
        module, _ = os.path.splitext(self.getParam('input'))
        if self.getParam('test_cases'):
            for test_case in self.getParam('test_cases'):
                command.append(f"{module}.{test_case}")
        else:
            command.append(module)
        self.parameters().setValue('command', tuple(command))
        return ExecuteCommand.execute(self)
