#* This file is part of MOOSETOOLS repository
#* https://www.github.com/idaholab/moosetools
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moosetools/blob/main/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html

import os
import sys
import threading
import multiprocessing
import subprocess
from moosetools.moosetest.base import Runner


class RunCommand(Runner):
    @staticmethod
    def validParams():
        params = Runner.validParams()
        params.add('command', vtype=str, array=True, required=True, doc="Command to execute.")
        params.add(
            'timeout',
            vtype=int,
            doc=
            "Limit the execution to the specified time; implemented via 'timeout' flag in `subprocess.run` command."
        )
        params.add(
            'allow_exception',
            vtype=bool,
            default=False,
            doc=
            "Do not raise exception if the process fails; implemented via 'check' flag in `subprocess.run` command."
        )
        return params

    def execute(self):
        kwargs = dict()
        kwargs['capture_output'] = True  # MOOSE executable output is not captured without this
        kwargs['encoding'] = 'utf-8'
        kwargs['check'] = self.getParam('allow_exception')
        kwargs['timeout'] = self.getParam('timeout')

        cmd = self.getParam('command')
        str_cmd = ' '.join(cmd)
        print('RUNNING COMMAND:\n{0}\n{1}\n{0}'.format('-' * len(str_cmd), str_cmd))
        out = subprocess.run(cmd, **kwargs)
        sys.stdout.write(out.stdout)
        sys.stderr.write(out.stderr)
        return out.returncode
