import os
import threading
import multiprocessing
import subprocess
from moosetools.moosetest.base import Runner

class ProcessRunner(Runner):
    @staticmethod
    def validParams():
        params = Runner.validParams()
        params.add('command', vtype=str, array=True, required=True, doc="Command to execute.")
        params.add('timeout', vtype=int, doc="Limit the execution to the specified time; implemented via 'timeout' flag in `subprocess.run` command.")
        params.add('allow_exception', vtype=bool, default=False, doc="Do not raise exception if the process fails; implemented via 'check' flag in `subprocess.run` command.")
        return params

    def execute(self):
        kwargs = dict()
        kwargs['capture_output'] = False # use sys.stdout/sys.stderr, which is captured by TestCase
        kwargs['text'] = True # encode output to UTF-8
        kwargs['check'] = self.getParam('allow_exception')
        kwargs['timeout'] = self.getParam('timeout')

        cmd = self.getParam('command')
        str_cmd = ' '.join(cmd)
        self.info('RUNNING COMMAND:\n{0}\n{1}\n{0}'.format('-'*len(str_cmd) , str_cmd))
        out = subprocess.run(self.getParam('command'), **kwargs)
        return out.returncode
