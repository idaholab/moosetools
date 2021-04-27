#!/usr/bin/env python3
import io
import logging
import unittest
from moosetools.base import MooseException
from moosetools import moosetest

class TestRunner(unittest.TestCase):
    def testDefault(self):

        # name is required
        with self.assertRaises(MooseException) as ex:
            runner = moosetest.base.Runner()
        self.assertIn("The parameter 'name' is marked as required", str(ex.exception))

        runner = moosetest.base.Runner(name='name')
        self.assertIsNotNone(runner.getParam('_unique_id'))
        self.assertIsNone(runner.getParam('differs'))

        with self.assertRaises(NotImplementedError) as ex:
            runner.execute()
        self.assertIn("The 'execute' method must be overridden.", str(ex.exception))



if __name__ == '__main__':
    unittest.main(module=__name__, verbosity=2)
