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
import sys
import unittest
import platform
import argparse
from unittest import mock

from moosetools import mooseutils
from moosetools import moosetest


class TestTestHarness(unittest.TestCase):
    def testDefault(self):
        th = moosetest.base.TestHarness()
        self.assertEqual(th.getParam('timeout'), 300)

    def test_validCommandLineArguments(self):
        parser = argparse.ArgumentParser()
        moosetest.base.TestHarness.validCommandLineArguments(
            parser, moosetest.base.TestHarness.validParams())

        args = parser.parse_args(args=[])
        self.assertIn('n_threads', args)

    def test_setup(self):
        th = moosetest.base.TestHarness()
        args = argparse.Namespace(n_threads=None, timeout=1980., max_failures=None)
        th._setup(args)
        self.assertEqual(th.getParam('timeout'), 1980.)

    @mock.patch('argparse.ArgumentParser.parse_args')
    def test_parse(self, mock_args):

        mock_args.return_value = argparse.Namespace(timeout=10.,
                                                    max_failures=42,
                                                    spec_file_names=['a', 'b'])

        th = moosetest.base.TestHarness()
        th.parse()
        self.assertEqual(th.getParam('timeout'), 10)
        self.assertEqual(th.getParam('max_failures'), 42)
        self.assertEqual(th.getParam('spec_file_names'), ('a', 'b'))

    def test_run(self):
        path = os.path.join(os.path.dirname(__file__), '..', 'demo')
        with mooseutils.CurrentWorkingDirectory(path):
            th = moosetest.base.TestHarness(controllers=(moosetest.controllers.TagController(), ))
            rcode = th.run(th.discover())

        self.assertEqual(rcode, 0)


if __name__ == '__main__':
    unittest.main(module=__name__, verbosity=2, buffer=True)
