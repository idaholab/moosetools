#!/usr/bin/env python3
import io
import logging
import unittest
from moosetools.parameters import InputParameters
from moosetools.base import MooseException
from moosetools import moosetest

class TestFormatter(unittest.TestCase):
    def testDefault(self):

        f = moosetest.base.Formatter()
        self.assertEqual(f.name(), 'Formatter')


        methods = ['formatRunnerState', 'formatRunnerResult', 'formatDifferState', 'formatDifferResult']
        for method in methods:
            with self.assertRaises(NotImplementedError) as ex:
                getattr(f, method)()
            self.assertIn(f"The '{method}' method must be overridden.", str(ex.exception))

        with self.assertRaises(NotImplementedError) as ex:
            f.formatComplete(None)
        self.assertIn(f"The 'formatComplete' method must be overridden.", str(ex.exception))



if __name__ == '__main__':
    unittest.main(module=__name__, verbosity=2)
