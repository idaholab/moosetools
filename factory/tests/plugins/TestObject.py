from base import MooseObject

class TestObject(MooseObject):
      @staticmethod
      def validParams():
            params = MooseObject.validParams()
            params.add('par')
            params.add('par_int', vtype=int)
            params.add('par_float', vtype=float)
            params.add('par_str', vtype=str)
            params.add('par_bool', vtype=bool)
            params.add('vec_int', vtype=int, array=True)
            params.add('vec_float', vtype=float, array=True)
            params.add('vec_str', vtype=str, array=True)
            params.add('vec_bool', vtype=bool, array=True)
            return params

class TestObjectBadInit(MooseObject):
      def __init__(self, *args, **kwargs):
            MooseObject.__init__(self, *args, **kwargs)
            raise Exception('__init__ failed')

class TestObjectBadParams(MooseObject):
      @staticmethod
      def validParams():
            params = MooseObject.validParams()
            raise Exception('validParams failed')
            return params
