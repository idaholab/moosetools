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

from moosetools import mooseutils
from moosetools.moosetest.base import FileDiffer


class CSVDiffer(FileDiffer):
    """
    A tool for testing for the existence of text within `sys.stdour` and/or `sys.stderr`.
    """
    @staticmethod
    def validParams():
        params = FileDiffer.validParams()
        params.add('override_columns',
                   array=True,
                   vtype=str,
                   doc="A list of variable names to customize the CSV diff tolerances.")
        params.add('override_rel_err',
                   vtype=str,
                   array=True,
                   doc="A list of customized relative error tolerances.")
        params.add('override_abs_zero',
                   vtype=float,
                   array=True,
                   doc="A list of customized absolute zero tolerances.")
        params.add('comparison_file',
                   vtype=str,
                   doc="Name of custom comparison configuration file.")
        params.add('abs_zero',
                   vtype=float,
                   default=1e-10,
                   doc="Absolute zero cutoff in comparison()s.")
        params.add('rel_err',
                   vtype=float,
                   default=5.5e-6,
                   doc="Relative error value in comparison(s).")
        return params

    def execute(self, *args):
        args = types.SimpleNamespace(csv_file=None,
                                     comparison_file=self.getParam('comparison_file'),
                                     abs_zero=self.getParam('abs_zero'),
                                     relative_tolerance=self.getParam('rel_err'),
                                     custom_columns=self.getParam('override_columns'),
                                     custom_rel_err=self.getParam('override_rel_err'),
                                     custom_abs_zero=self.getParam('override_abs_zero'))

        for filename, gold_filename in self.pairs():
            # TODO: The mooseutils.CSVDiffer relies on argparse to open the files and the context
            #       operation of the CSVDiffer closes them. I feel it would be better if the object
            #       just opened them when they are used in the diff function.
            args.csv_file = (open(filename), open(gold_filename))
            with mooseutils.CSVDiffer(args) as csv_differ:
                messages = csv_differ.diff()
                for msg in messages:
                    self.error(msg)

                if not csv_differ.getNumErrors():
                    self.info("Files are the same: {} == {}",  filename, gold_filename)
