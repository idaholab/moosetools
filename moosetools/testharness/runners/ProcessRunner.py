import subprocess
from .Runner import Runner

class ProcessRunner(Runner):
    @staticmethod
    def validParams():
        params = Runner.validParams()
        params.add('command', vtype=str, array=True, required=True, doc="The command to execute.")
        return params

    def execute(self):
        out = subprocess.run(self.getParam('command'), capture_output=True, text=True, check=False)
        if out.returncode > 0:
            self.info(out.stdout)
            self.error(out.stderr)
        else:
            self.debug(out.stdout)
