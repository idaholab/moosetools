#* This file is part of the MOOSE framework
#* https://www.mooseframework.org
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moose/blob/master/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html

import parameters

class FactoryObject(object):
    INPUTPARAMETERS_ERROR_MODE = parameters.InputParameters.ErrorMode.EXCEPTION

    @staticmethod
    def validParams():
        params = parameters.InputParameters(mode=parameters)
        params.add('name', vtype=str, doc="The name of the object.")
        return params

    def __init__(self, **kwargs):
        self._parameters = getattr(self.__class__, 'validParams')()
        self._parameters.update(**kwargs)

    def name(self):
        return self.getParam('name')

    def parameters(self):
        return self._parameters

    def getParam(self, name):
        return self._parameters.get(name)

    def isParamValid(self, name):
        return self._parameters.isValid(name)
