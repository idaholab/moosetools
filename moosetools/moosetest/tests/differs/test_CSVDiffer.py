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
from moosetools.moosetest.differs import CSVDiffer


class TestCSVDiffer(unittest.TestCase):
    def testEqual(self):
        a = os.path.join(os.path.dirname(__file__), 'a.csv')
        obj = CSVDiffer(name='diff', file_names=(a, ), file_goldnames=(a, ))
        obj.preExecute()

        with mock.patch('builtins.print') as mock_print:
            obj.execute(0, '', '')
        mock_print.assert_called_once_with("Files are the same: {} == {}".format(a, a))
        self.assertEqual(obj.status(), 0)

    def testDifferent(self):
        a = os.path.join(os.path.dirname(__file__), 'a.csv')
        b = os.path.join(os.path.dirname(__file__), 'b.csv')

        obj = CSVDiffer(name='diff', file_names=(b, ), file_goldnames=(a, ))
        obj.preExecute()

        with mock.patch('builtins.print') as mock_print, self.assertLogs(level='ERROR') as log:
            obj.execute(0, '', '')
        mock_print.assert_not_called()
        self.assertEqual(obj.status(), 1)

        self.assertEqual(len(log.output), 2)
        self.assertIn('The values in column "month" don\'t match', log.output[0])
        self.assertIn('The values in column "day" don\'t match', log.output[1])


if __name__ == '__main__':
    unittest.main(module=__name__, verbosity=2)
