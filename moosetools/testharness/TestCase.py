import enum
from moosetools.base import MooseObject






class TestCase(MooseObject):
    class State(enum.Enum):
        WAITING = 1
        RUNNER = 2
        DONE = 3
        CLOSED = 4

    def __init__(self, runner, *args, **kwargs):
        MooseObject.__init__(self, *args, **kwargs)



    def execute(self):
        self.__state = State.RUNNING
        self.__runner.init()
        if self.__runner.status(logging.WARNING):
            self.__state = State.DONE
            return self.__runner.getStream()


        returncode, stdout, stderr = self.__runner.execute()
        #for differ in self.__differs:
        #    out.append(differ.execute(*out[0]))
        #return out

    def done(self, future):
        self.__state = State.DONE
        self.__results = future.result()

    def update(self):
        return None#'update'

    def results(self):
        # TODO: raise if not DONE
        self.__state = State.CLOSED
        return self.__results
