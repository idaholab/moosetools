from moosetools.moosetest.base import Controller

class TestController(Controller):
    @staticmethod
    def validParams():
        params = Controller.validParams()
        params.setValue('prefix', 'test')
        return params

    def execute(self, *args, **kwargs):
        pass
