import logging
import time
import platform
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
        params.add('sleep', vtype=(int, float), default=0)
        params.add('object_name')
        return params

    @staticmethod
    def validObjectParams():
        params = Controller.validObjectParams()
        params.add('platform', array=True, allow=('Linux', 'Darwin', 'Windows'),
                   doc="Limit the execution to the supplied platform(s).")
        return params

    def setValue(self, name, value):
        self.parameters().setValue(name, value)

    def execute(self, obj, params):
        time.sleep(self.getParam('sleep'))

        obj_name = self.getParam('object_name')
        if (obj_name is None) or (obj.name().startswith(obj_name)):
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

        sys_platform = platform.system()
        self.debug('platform.system() = {}', repr(sys_platform))
        pf = params.getValue('platform')
        if (pf is not None) and (sys_platform not in pf):
            self.skip('{} not in {}', repr(sys_platform), repr(pf))
            self.debug("The system platform {} is not in the allowable platforms list of {}",
                       repr(sys_platform), repr(pf))

class TestRunner(Runner):
    @staticmethod
    def validParams():
        params = Runner.validParams()
        params.add('stdout', default=False)
        params.add('stderr', default=False)
        params.add('error', default=False)
        params.add('raise', default=False)
        params.add('fatal', default=False)
        params.add('sleep', vtype=(int, float), default=0)
        return params

    def status(self):
        if self.getParam('fatal'):
            raise Exception("runner fatal")
        return Runner.status(self)

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
        params.add('fatal', default=False)
        params.add('sleep', vtype=(int, float), default=0)
        return params

    def status(self):
        if self.getParam('fatal'):
            raise Exception("differ fatal")
        return Differ.status(self)

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
