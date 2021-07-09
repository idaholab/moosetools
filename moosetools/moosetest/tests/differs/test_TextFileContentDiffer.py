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
from moosetools.moosetest.differs import TextFileContentDiffer


class TestTextFileContentDiffer(unittest.TestCase):
    def testDoNothing(self):
        obj = TextFileContentDiffer(name='diff')
        obj._checkFile(__file__)
        self.assertEqual(obj.status(), 0)

    def testIsFileError(self):
        obj = TextFileContentDiffer(name='diff', file_names_created=('wrong', ))
        with self.assertLogs(level='ERROR') as log:
            obj.execute(0, '', '')
        self.assertEqual(obj.status(), 1)
        self.assertEqual(len(log.output), 1)
        self.assertIn("does not exist", log.output[0])

    def testTextIn(self):
        a = os.path.join(os.path.dirname(__file__), 'a.csv')
        obj = TextFileContentDiffer(name='diff', file_names_created=(a, ), text_in='andrew')
        with mock.patch('builtins.open', mock.mock_open(read_data='andrew')) as m:
            obj.execute(0, '', '')
        self.assertEqual(obj.status(), 0)
        m.assert_called_once_with(a, 'r')

        with mock.patch(
                'builtins.open',
                mock.mock_open(read_data='edward')) as m, self.assertLogs(level='ERROR') as log:
            obj.execute(0, '', '')
        self.assertEqual(len(log.output), 1)
        self.assertIn(
            "The content of 'text_in' parameter, 'andrew', was not located in the content",
            log.output[0])
        self.assertEqual(obj.status(), 1)

    def testTextNotIn(self):
        a = os.path.join(os.path.dirname(__file__), 'a.csv')
        obj = TextFileContentDiffer(name='diff', file_names_created=(a, ), text_not_in='edward')
        with mock.patch('builtins.open', mock.mock_open(read_data='andrew')) as m:
            obj.execute(0, '', '')
        self.assertEqual(obj.status(), 0)
        m.assert_called_once_with(a, 'r')

        with mock.patch(
                'builtins.open',
                mock.mock_open(read_data='edward')) as m, self.assertLogs(level='ERROR') as log:
            obj.execute(0, '', '')
        self.assertEqual(len(log.output), 1)
        self.assertIn(
            "The content of 'text_not_in' parameter, 'edward', was located in the content",
            log.output[0])
        self.assertEqual(obj.status(), 1)

    def testReMatch(self):
        a = os.path.join(os.path.dirname(__file__), 'a.csv')
        obj = TextFileContentDiffer(name='diff', file_names_created=(a, ), re_match='a[a-z]+w')
        with mock.patch('builtins.open', mock.mock_open(read_data='andrew')) as m:
            obj.execute(0, '', '')
        self.assertEqual(obj.status(), 0)
        m.assert_called_once_with(a, 'r')

        with mock.patch(
                'builtins.open',
                mock.mock_open(read_data='edward')) as m, self.assertLogs(level='ERROR') as log:
            obj.execute(0, '', '')
        self.assertEqual(len(log.output), 1)
        self.assertIn("The regular expression of 're_match' parameter, 'a[a-z]+w', did not produce",
                      log.output[0])
        self.assertEqual(obj.status(), 1)

    def testReNotMatch(self):
        a = os.path.join(os.path.dirname(__file__), 'a.csv')
        obj = TextFileContentDiffer(name='diff', file_names_created=(a, ), re_not_match='e[a-z]+d')
        with mock.patch('builtins.open', mock.mock_open(read_data='andrew')) as m:
            obj.execute(0, '', '')
        self.assertEqual(obj.status(), 0)
        m.assert_called_once_with(a, 'r')

        with mock.patch(
                'builtins.open',
                mock.mock_open(read_data='edward')) as m, self.assertLogs(level='ERROR') as log:
            obj.execute(0, '', '')
        self.assertEqual(len(log.output), 1)
        self.assertIn("The regular expression of 're_not_match' parameter, 'e[a-z]+d', did produce",
                      log.output[0])
        self.assertEqual(obj.status(), 1)


if __name__ == '__main__':
    unittest.main(module=__name__, verbosity=2)
