#!/usr/bin/env python3
#* This file is part of MOOSETOOLS repository
#* https://www.github.com/idaholab/moosetools
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moosetools/blob/main/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html

import io
import logging
import unittest
from unittest import mock
from moosetools.moosetest.base import FileDiffer


class TestFileDiff(unittest.TestCase):
    def testGoldFilenames(self):
        obj = FileDiffer(name='diff', file_names_created=('a', 'b'), file_goldnames=('c', 'd'))
        obj.preExecute()
        pairs = list(obj.pairs())
        self.assertEqual(pairs, [('a', 'c'), ('b', 'd')])

    def testGoldFilenamesError(self):
        obj = FileDiffer(name='diff', file_names_created=('a', 'b'), file_goldnames=('c', 'd', 'e'))
        with self.assertLogs(level='ERROR') as log:
            obj.preExecute()
        self.assertEqual(len(log.output), 1)
        self.assertIn("The number of supplied file(s) for comparison", log.output[0])

    def testGoldDir(self):
        obj = FileDiffer(name='diff', file_names_created=('a', 'b'))
        obj.preExecute()
        pairs = list(obj.pairs())
        self.assertEqual(pairs, [('a', 'gold/a'), ('b', 'gold/b')])


if __name__ == '__main__':
    unittest.main(module=__name__, verbosity=2)
