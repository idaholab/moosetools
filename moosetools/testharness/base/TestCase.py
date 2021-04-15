import enum
import logging
from moosetools.base import MooseObject

class State(enum.Enum):
    def __new__(cls, value, exitcode, display, color):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.exitcode = exitcode
        obj.display = display
        obj.color = color
        return obj

class TestCase(MooseObject):
    class Progress(State):
        WAITING  = (1, 0, 'WAITING', 'white')
        RUNNING  = (2, 0, 'RUNNING', 'cyan')
        DONE     = (3, 0, 'DONE', 'white')
        CLOSED   = (4, 0, 'CLOSED', 'white')

    class Result(State):
        SKIP     = (5, 0, 'SKIP', 'cyan')
        FAIL     = (6, 1, 'FAILED', 'red')
        PASS     = (7, 0, 'OK', 'green')

    def __init__(self, runner, *args, **kwargs):
        kwargs.setdefault('name', runner.getParam('name'))
        MooseObject.__init__(self, *args, **kwargs)
        self._runner = runner
        self.__state = None
        self.__results = None
        self.setState(TestCase.Progress.WAITING)

    def setState(self, state):
        self.__state = state

    def getState(self):
        return self.__state

    def execute(self):
        self.setState(TestCase.Progress.RUNNING)
        self._runner.init()
        if self._runner.status(logging.WARNING):
            return TestCase.Result.SKIP, self._runner.getStream()

        self._runner.execute()
        if self._runner.status(logging.ERROR, logging.CRITICAL):
            return TestCase.Result.FAIL, self._runner.getStream()

        return TestCase.Result.PASS, self._runner.getStream()

    def done(self, future):
        self.setState(TestCase.Progress.DONE)
        self.__results = future.result()

    def report(self):
        state = self.getState()
        if state not in (TestCase.Progress.CLOSED, TestCase.Progress.DONE):
            #print('{}.......{}'.format(self.name(), state.display))
            self.info(state.display)

        elif state == TestCase.Progress.DONE:
            retcode, stream = self.__results
            self.info(retcode.display)

            #print('{}.......{}'.format(self.name(), retcode.display))
            self.setState(TestCase.Progress.CLOSED)




    #def update(self):
    #    if getState()

    #    return None#'update'

    #def results(self):
    #    self.setState(State.CLOSED)
    #    return self.__results
