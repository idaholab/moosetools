from moosetools.moosetest.base import Controller

class TestController(Controller):
    @staticmethod
    def validParams():
        params = Controller.validParams()
        params.set('prefix', 'test')
        return params

    def execute(self, *args, **kwargs):
        pass
