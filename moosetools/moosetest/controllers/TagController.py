#* This file is part of MOOSETOOLS repository
#* https://www.github.com/idaholab/moosetools
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moosetools/blob/main/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html

import re
from moosetools.moosetest.base import Controller, Runner


class TagController(Controller):
    """
    A controller to dictate if an object should run based on allowable tags.
    """
    AUTO_BUILD = True

    @staticmethod
    def validParams():
        params = Controller.validParams()
        params.setValue('prefix', 'tag')
        params.add('allowable_names',
                   array=True,
                   vtype=str,
                   doc="The allowable tag names for limiting test execution.")
        return params

    @staticmethod
    def validObjectParams():
        """
        The "prefix" parameter for this object is not set, so this method is not used.

        See the `make_runner` and `make_differ` in the Runner.py and Differ.py modules.
        """
        params = Controller.validObjectParams()
        params.add('names', array=True, vtype=str, doc="The tag names that object is restricted.")
        return params

    def execute(self, obj, params):

        available = set(
            self.getParam('allowable_names')) if self.isParamValid('allowable_names') else set()
        restricted = set(params.getValue('names')) if params.isValid('names') else None
        if (restricted is not None) and (not restricted.issubset(available)):
            diff = restricted.difference(available)
            msg = ("The execution of the test is limited to the {} tags, but the test has the "
                   "tags {} that are not in this set.")
            self.debug(msg, available, diff)
            self.skip("{} not in {}", tuple(diff), tuple(available))
