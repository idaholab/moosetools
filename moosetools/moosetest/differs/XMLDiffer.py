#* This file is part of MOOSETOOLS repository
#* https://www.github.com/idaholab/moosetools
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moosetools/blob/main/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html

import os
import types

from moosetools import diff
from moosetools import mooseutils
from moosetools.moosetest.base import FileDiffer


class XMLDiffer(FileDiffer):
    """
    A tool for comparing XML files.
    """
    @staticmethod
    def validParams():
        params = FileDiffer.validParams()
        params.add('rel_err',
                   vtype=(float, int),
                   doc="Relative error value in comparison(s).")
        params.add('abs_err',
                   vtype=(float, int),
                   doc="Relative error value in comparison(s).")

        return params

    def execute(self, *args):
        rel_err = self.getParam('rel_err')
        abs_err = self.getParam('abs_err')

        if (rel_err is None) and (abs_err is None):
            abs_err = 0

        for filename, gold_filename in self.pairs():
            xml_diff = diff.compare_xml(filename, gold_filename,
                                        relative_error=rel_err, absolute_error=abs_err)
            if xml_diff:
                self.error(xml_diff.pretty())
