#* This file is part of MOOSETOOLS repository
#* https://www.github.com/idaholab/moosetools
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moosetools/blob/main/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html

from moosetools.base import MooseObject


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
