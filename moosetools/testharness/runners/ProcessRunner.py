from .Runner import Runner

class ProcessRunner(Runner):
    @staticmethod
    def validParams():
        params = Runner.validParams()
        params.add('command', vtype=str, array=True, required=True, doc="The command to execute.")
        return params

    def check(self):
        pass


    def execute(self):
        out = subprocess.run(['sleep', str(self.__index)], capture_output=True, text=True, check=False)
        return out.returncode, out.stdout, out.stderr
