#!/usr/bin/env python3

import os
import sys
import unittest
import platform
import argparse
from unittest import mock

from moosetools import mooseutils
from moosetools import moosetest

class NewTestHarness(moosetest.base.TestHarness):

    @staticmethod
    def validParams():
        params = moosetest.base.TestHarness.validParams()
        params.add('number', default=1949)
        return params

    @staticmethod
    def createCommandLineParser(params):
        parser = moosetest.base.TestHarness.createCommandLineParser(moosetest.base.TestHarness.validParams())
        parser.add_argument('--number')
        return parser

    def _setup(self, args):
        moosetest.base.TestHarness._setup(self, args)
        self.parameters().setValue('number', int(args.number))


class TestTestHarness(unittest.TestCase):
    def testDefault(self):
        th = moosetest.base.TestHarness()
        self.assertEqual(th.getParam('timeout'), 300)
        self.assertIsNone(th._TestHarness__fuzzer)

    def testCreateCommandLineParser(self):
        parser = moosetest.base.TestHarness.createCommandLineParser(moosetest.base.TestHarness.validParams())
        self.assertIsInstance(parser, argparse.ArgumentParser)

    @mock.patch('argparse.ArgumentParser.parse_args')
    def test_parse(self, mock_args):

        mock_args.return_value = argparse.Namespace(number=1980, timeout=10., max_failures=42, spec_file_blocks=['Assessments', 'Tests'], spec_file_names=['a', 'b'], fuzzer=None)

        th = NewTestHarness()
        th.parse()
        self.assertEqual(th.getParam('number'), 1980)
        self.assertEqual(th.getParam('timeout'), 10)
        self.assertEqual(th.getParam('max_failures'), 42)
        self.assertEqual(th.getParam('spec_file_blocks'), ('Assessments', 'Tests'))
        self.assertEqual(th.getParam('spec_file_names'), ('a', 'b'))

    def test_run(self):
        path = os.path.join(os.path.dirname(__file__), '..', 'demo')
        with mooseutils.CurrentWorkingDirectory(path):
            th = NewTestHarness()
            rcode = th.run()

        self.assertEqual(rcode, 0)

    def test_fuzzer(self):
        th = NewTestHarness()
        rcode = th.run()


if __name__ == '__main__':
    unittest.main(module=__name__, verbosity=2, buffer=True)
