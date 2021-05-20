#* This file is part of MOOSETOOLS repository
#* https://www.github.com/idaholab/moosetools
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moosetools/blob/main/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html

from moosetools.moosetest.base import Controller


class TestController(Controller):
    @staticmethod
    def validParams():
        params = Controller.validParams()
        params.setValue('prefix', 'test')
        return params

    def execute(self, *args, **kwargs):
        pass
