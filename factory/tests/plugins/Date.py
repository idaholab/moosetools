from base import MooseObject

class Date(MooseObject):
      @staticmethod
      def validParams():
            params = MooseObject.validParams()
            params.add('year', vtype=int)
            params.add('month', vtype=str)
            return params
