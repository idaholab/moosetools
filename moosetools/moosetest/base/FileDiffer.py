#* This file is part of MOOSETOOLS repository
#* https://www.github.com/idaholab/moosetools
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moosetools/blob/main/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html

import os
from .Runner import Runner
from .Differ import Differ


class FileDiffer(Differ):
    """
    Base Differ object for performing file comparisons.

    The main purpose is provide pairs of file names for comparison, (created, gold), that
    can be iterated over using the `pairs` method.
    """
    def validParams():
        params = Differ.validParams()
        f_params = params.getValue('file')
        f_params.add('goldnames', vtype=str, array=True, doc="")
        f_params.add('golddir', vtype=str, default='gold', doc="")
        return params

    def __init__(self, *args, **kwargs):
        Differ.__init__(self, *args, **kwargs)
        self.__filename_pairs = list()

    def preExecute(self):
        """
        Build file pairs for comparison prior to calling the `execute` method.
        """
        Differ.preExecute(self)

        filenames = self.getParam('file', 'names') or tuple()
        if self.isParamValid('file', 'goldnames'):
            gold_filenames = self.getParam('file', 'goldnames') or tuple()

        else:
            gold_dir = self.getParam('file', 'golddir')
            gold_filenames = list()
            for filename in filenames:
                d, f = os.path.split(filename)
                gold_filenames.append(os.path.join(d, gold_dir, f))

        if len(filenames) != len(gold_filenames):
            msg = "The number of supplied file(s) for comparison are not the same length:\nFile(s):\n{}\nGold File(s):\n{}"
            self.error(msg, '\n'.join(filenames), '\n'.join(gold_filenames))

        self.__filename_pairs = [(f, g) for f, g in zip(filenames, gold_filenames)]

    def pairs(self):
        """
        Yield pairs of files, created and gold, for comparison.
        """
        for f, g in self.__filename_pairs:
            yield f, g
