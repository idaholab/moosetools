#* This file is part of MOOSETOOLS repository
#* https://www.github.com/idaholab/moosetools
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moosetools/blob/main/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html

from moosetools.moosetest.base import Filter


class NameFilter(Filter):
    """
    Filter for removing tests that do not match `Runner` name criteria.
    """
    AUTO_BUILD = True

    @staticmethod
    def validParams():
        params = Filter.validParams()
        params.add('in_name',
                   vtype=str,
                   doc="Ensure the that supplied text is in the `Runner` name.")
        return params

    def execute(self, runner):
        """
        Indicate that the *runner* object should be removed, if the name criteria are not satisfied.
        """
        name = runner.name()
        in_name = self.getParam('in_name')
        if (in_name is not None) and (in_name not in name):
            self.remove()
