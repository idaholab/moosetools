#!/usr/bin/env python3
#* This file is part of MOOSETOOLS repository
#* https://www.github.com/idaholab/moosetools
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moosetools/blob/main/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html

import os
import unittest
from unittest import mock
from moosetools.moosetest.differs import TextFileDiffer


class TestTextFileDiffer(unittest.TestCase):
    def testErrors(self):
        obj = TextFileDiffer(name='diff')
        with self.assertLogs(level='CRITICAL') as log:
            obj._compare('wrong', None)
        self.assertEqual(len(log.output), 1)
        self.assertIn("The file 'wrong' does not exist.", log.output[0])

        with self.assertLogs(level='CRITICAL') as log:
            obj._compare(__file__, 'wrong')
        self.assertEqual(len(log.output), 1)
        self.assertIn("The 'gold' file 'wrong' does not exist.", log.output[0])

    def testEqual(self):
        a = os.path.join(os.path.dirname(__file__), 'a.csv')
        obj = TextFileDiffer(name='diff', file_names_created=(a, ), file_goldnames=(a, ))
        obj.preExecute()

        with mock.patch('builtins.print') as mock_print:
            obj.execute(0, '', '')
        mock_print.assert_called_once_with("Files are the same: {} == {}".format(a, a))
        self.assertEqual(obj.status(), 0)

    def testDifferent(self):
        a = os.path.join(os.path.dirname(__file__), 'a.csv')
        b = os.path.join(os.path.dirname(__file__), 'b.csv')

        obj = TextFileDiffer(name='diff', file_names_created=(b, ), file_goldnames=(a, ))
        obj.preExecute()

        with mock.patch('builtins.print') as mock_print, self.assertLogs(level='ERROR') as log:
            obj.execute(0, '', '')
        mock_print.assert_called_once()
        self.assertEqual(obj.status(), 1)

        self.assertEqual(len(log.output), 1)
        self.assertIn("does not match", log.output[0])


if __name__ == '__main__':
    unittest.main(module=__name__, verbosity=2)
