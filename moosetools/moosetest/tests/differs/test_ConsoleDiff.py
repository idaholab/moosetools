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
from moosetools.moosetest.differs import ConsoleDiff


class TestConsoleDiff(unittest.TestCase):
    def testDefault(self):
        obj = ConsoleDiff(name='diff')
        obj.execute(0, '', '')
        self.assertEqual(obj.status(), 0)

    def testTextIn(self):
        obj = ConsoleDiff(name='diff', text_in='andrew')
        obj.execute(0, 'andrew', '')
        self.assertEqual(obj.status(), 0)

        obj.execute(0, '', 'andrew')
        self.assertEqual(obj.status(), 0)

        with self.assertLogs(level='ERROR') as log:
            obj.execute(0, '', '')
        self.assertEqual(len(log.output), 1)
        self.assertIn("The content of 'text_in' parameter, 'andrew', was not located in the output",
                      log.output[0])
        self.assertEqual(obj.status(), 1)

    def testTextNotIn(self):
        obj = ConsoleDiff(name='diff', text_not_in='andrew')
        obj.execute(0, 'bob', 'julie')
        self.assertEqual(obj.status(), 0)

        with self.assertLogs(level='ERROR') as log:
            obj.execute(0, 'andrew', '')
        self.assertEqual(len(log.output), 1)
        self.assertIn("The content of 'text_not_in' parameter, 'andrew', was located in the output",
                      log.output[0])
        self.assertEqual(obj.status(), 1)

        obj.reset()
        with self.assertLogs(level='ERROR') as log:
            obj.execute(0, '', 'andrew')
        self.assertEqual(len(log.output), 1)
        self.assertIn("The content of 'text_not_in' parameter, 'andrew', was located in the output",
                      log.output[0])
        self.assertEqual(obj.status(), 1)

    def testTextInStdout(self):
        obj = ConsoleDiff(name='diff', text_in_stdout='andrew')
        obj.execute(0, 'andrew', 'andrew')
        self.assertEqual(obj.status(), 0)

        with self.assertLogs(level='ERROR') as log:
            obj.execute(0, '', 'andrew')
        self.assertEqual(len(log.output), 1)
        self.assertIn(
            "The content of 'text_in_stdout' parameter, 'andrew', was not located in the output",
            log.output[0])
        self.assertEqual(obj.status(), 1)

    def testTextNotInStdout(self):
        obj = ConsoleDiff(name='diff', text_not_in_stdout='andrew')
        obj.execute(0, 'bob', 'andrew')
        self.assertEqual(obj.status(), 0)

        with self.assertLogs(level='ERROR') as log:
            obj.execute(0, 'andrew', 'andrew')
        self.assertEqual(len(log.output), 1)
        self.assertIn(
            "The content of 'text_not_in_stdout' parameter, 'andrew', was located in the output",
            log.output[0])
        self.assertEqual(obj.status(), 1)

    def testTextInStderr(self):
        obj = ConsoleDiff(name='diff', text_in_stderr='andrew')
        obj.execute(0, 'andrew', 'andrew')
        self.assertEqual(obj.status(), 0)

        with self.assertLogs(level='ERROR') as log:
            obj.execute(0, 'andrew', '')
        self.assertEqual(len(log.output), 1)
        self.assertIn(
            "The content of 'text_in_stderr' parameter, 'andrew', was not located in the output",
            log.output[0])
        self.assertEqual(obj.status(), 1)

    def testTextNotInStderr(self):
        obj = ConsoleDiff(name='diff', text_not_in_stderr='andrew')
        obj.execute(0, 'andrew', 'bob')
        self.assertEqual(obj.status(), 0)

        with self.assertLogs(level='ERROR') as log:
            obj.execute(0, 'andrew', 'andrew')
        self.assertEqual(len(log.output), 1)
        self.assertIn(
            "The content of 'text_not_in_stderr' parameter, 'andrew', was located in the output",
            log.output[0])
        self.assertEqual(obj.status(), 1)

    def testReMatch(self):
        obj = ConsoleDiff(name='diff', re_match='\d{4}-\d{2}-\d{2}')
        obj.execute(0, '1980-06-24', '198-06-24')
        self.assertEqual(obj.status(), 0)

        obj.execute(0, '198-06-24', '1980-06-24')
        self.assertEqual(obj.status(), 0)

        with self.assertLogs(level='ERROR') as log:
            obj.execute(0, '198-06-24', '')
        self.assertEqual(len(log.output), 1)
        self.assertIn(
            "The regular expression of 're_match' parameter, '\d{4}-\d{2}-\d{2}', did not produce a match in the output",
            log.output[0])
        self.assertEqual(obj.status(), 1)

        obj.reset()
        with self.assertLogs(level='ERROR') as log:
            obj.execute(0, '', '198-06-24')
        self.assertEqual(len(log.output), 1)
        self.assertIn(
            "The regular expression of 're_match' parameter, '\d{4}-\d{2}-\d{2}', did not produce a match in the output",
            log.output[0])
        self.assertEqual(obj.status(), 1)

    def testReMatchStdout(self):
        obj = ConsoleDiff(name='diff', re_match_stdout='\d{4}-\d{2}-\d{2}')
        obj.execute(0, '1980-06-24', '1980-06-24')
        self.assertEqual(obj.status(), 0)

        with self.assertLogs(level='ERROR') as log:
            obj.execute(0, '198-06-24', '1980-06-24')
        self.assertEqual(len(log.output), 1)
        self.assertIn(
            "The regular expression of 're_match' parameter, '\d{4}-\d{2}-\d{2}', did not produce a match in the output",
            log.output[0])
        self.assertEqual(obj.status(), 1)

    def testReMatchStderr(self):
        obj = ConsoleDiff(name='diff', re_match_stderr='\d{4}-\d{2}-\d{2}')
        obj.execute(0, '1980-06-24', '1980-06-24')
        self.assertEqual(obj.status(), 0)

        with self.assertLogs(level='ERROR') as log:
            obj.execute(0, '1980-06-24', '198-06-24')
        self.assertEqual(len(log.output), 1)
        self.assertIn(
            "The regular expression of 're_match' parameter, '\d{4}-\d{2}-\d{2}', did not produce a match in the output",
            log.output[0])
        self.assertEqual(obj.status(), 1)


if __name__ == '__main__':
    unittest.main(module=__name__, verbosity=2)
