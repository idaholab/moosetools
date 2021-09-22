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
import sys
import threading
import multiprocessing
import subprocess
from moosetools.moosetest.base import Runner
from tempfile import SpooledTemporaryFile


class ExecuteCommand(Runner):
    @staticmethod
    def validParams():
        params = Runner.validParams()

        # TODO: Cannot be applied to Runner b/c you can't interrupt a python function within a Thread
        params.add('timeout', default=300, vtype=(float, int), doc="Allowable execution time, in seconds.")


        params.add('command', vtype=str, array=True, required=True, doc="Command to execute.")
        params.add(
            'allow_exception',
            vtype=bool,
            default=False,
            doc=
            "Do not raise exception if the process fails; implemented via 'check' flag in `subprocess.run` command."
        )

        #params.add('shell', vtype=bool, default=True, doc="Set the 'shell' input for `subprocess.run` command.")
        return params

    def execute(self):

        #f = SpooledTemporaryFile(max_size=1000000)
        #f = io.StringIO()

        kwargs = dict()
        #kwargs['capture_output'] = True  # MOOSE executable output is not captured without this
        kwargs['encoding'] = 'utf-8'
        kwargs['check'] = self.getParam('allow_exception')

        kwargs['stdout'] = subprocess.PIPE
        kwargs['stderr'] = subprocess.STDOUT
        kwargs['cwd'] = self.getParam('working_dir') or os.getcwd()
        kwargs['timeout'] = self.getParam('timeout')
        #kwargs['close_fds'] = False
        #kwargs['shell'] = True#self.getParam('shell')
        #kwargs['preexec_fn'] = os.setsid

        cmd = self.getParam('command')
        str_cmd = ' '.join(cmd)
        self.info('RUNNING COMMAND:\n{0}\n{1}\n{0}'.format('-' * len(str_cmd), str_cmd))

        out = subprocess.run(cmd, **kwargs)
        #f.flush()
        #f.seek(0)
        #content = f.read().decode('utf-8')
        #f.close()
        #content = out.stdout
        #self.info(content)
        self.info(out.stdout)

        return out.returncode
