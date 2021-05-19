#!/usr/bin/env python3
import os
import sys
import unittest
from unittest import mock

from moosetools.moosetest import main
from moosetools.moosetest.main import TestHarness

class TestTestHarness(unittest.TestCase):
    def testDefault(self):
        th = TestHarness()
        self.assertTrue(hasattr(th, 'applyCommandLineArguments'))

if __name__ == '__main__':
    unittest.main(module=__name__, verbosity=2, buffer=True)
