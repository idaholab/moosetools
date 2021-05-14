import logging
import time
from moosetools.moosetest.base import Controller, Runner, Differ

class TestController(Controller):
    @staticmethod
    def validParams():
        params = Controller.validParams()
        params.setValue('prefix', 'ctrl')
        params.add('skip', default=False)
        params.add('stdout', default=False)
        params.add('stderr', default=False)
        params.add('error', default=False)
        params.add('raise', default=False)
        params.add('sleep', vtype=int, default=0)
        params.add('type')
        return params

    @staticmethod
    def validObjectParams():
        params = Controller.validObjectParams()
        params.add('platform')
        return params

    def setValue(self, name, value):
        self.parameters().setValue(name, value)

    def execute(self, obj, *args):
        time.sleep(self.getParam('sleep'))

        obj_type = self.getParam('type')
        if (obj_type is None) or isinstance(obj, obj_type):
            if self.getParam('skip'):
                self.skip("a reason")
            if self.getParam('stdout'):
                print("controller stdout")
            if self.getParam('stderr'):
                logging.error("controller stderr")
            if self.getParam('error'):
                self.error("controller error")
            if self.getParam('raise'):
                raise Exception("controller raise")

class TestRunner(Runner):
    @staticmethod
    def validParams():
        params = Runner.validParams()
        params.add('stdout', default=False)
        params.add('stderr', default=False)
        params.add('error', default=False)
        params.add('raise', default=False)
        params.add('sleep', vtype=int, default=0)
        return params

    def setValue(self, name, value):
        self.parameters().setValue(name, value)

    def execute(self, *args):
        time.sleep(self.getParam('sleep'))

        if self.getParam('stdout'):
            print("runner stdout")
        if self.getParam('stderr'):
            logging.error("runner stderr")
        if self.getParam('error'):
            self.error("runner error")
        if self.getParam('raise'):
            raise Exception("runner raise")
        return 2011

class TestDiffer(Differ):
    @staticmethod
    def validParams():
        params = Runner.validParams()
        params.add('stdout', default=False)
        params.add('stderr', default=False)
        params.add('error', default=False)
        params.add('raise', default=False)
        params.add('sleep', vtype=int, default=0)
        return params

    def setValue(self, name, value):
        self.parameters().setValue(name, value)

    def execute(self, *args):
        time.sleep(self.getParam('sleep'))

        if self.getParam('stdout'):
            print("differ stdout")
        if self.getParam('stderr'):
            logging.error("differ stderr")
        if self.getParam('error'):
            self.error("differ error")
        if self.getParam('raise'):
            raise Exception("differ raise")
        return 2013
