import os
import threading
import multiprocessing
import subprocess
from .Runner import Runner

class ProcessRunner(Runner):
    @staticmethod
    def validParams():
        params = Runner.validParams()
        params.add('command', vtype=str, array=True, required=True, doc="Command to execute.")
        params.add('timeout', vtype=int, default=100, doc="Limit the execution to the specified time; implemented via 'timeout' flag in `subprocess.run` command.")
        params.add('allow_exception', vtype=bool, default=False, doc="Do not raise exception if the process fails; implemented via 'check' flag in `subprocess.run` command.")
        return params

    def execute(self):
        kwargs = dict()
        kwargs['capture_output'] = False # store stdout/stderr
        kwargs['text'] = True # encode output to UTF-8
        kwargs['check'] = self.getParam('allow_exception')
        kwargs['timeout'] = self.getParam('timeout')
        print("Don't show this!")
        out = subprocess.run(self.getParam('command'), **kwargs)
        return out.returncode, out.stdout, out.stderr
