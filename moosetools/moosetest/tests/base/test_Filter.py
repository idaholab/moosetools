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
from moosetools import core
from moosetools import parameters
from moosetools import moosetest


class TestFilter(unittest.TestCase):
    def testDefault(self):
        f = moosetest.base.Filter()
        self.assertEqual(f.name(), 'Filter')
        self.assertFalse(f.isRemoved())

        with self.assertRaises(NotImplementedError) as ex:
            f.execute(None)
        self.assertIn("The 'execute' method must be overridden.", str(ex.exception))

    def test_reset_remove(self):
        f = moosetest.base.Filter()
        self.assertFalse(f.isRemoved())
        f.remove()
        self.assertTrue(f.isRemoved())
        f.reset()
        self.assertFalse(f.isRemoved())

    def test_apply(self):
        class RunnerProxy(object):
            def __init__(self, status=0):
                self.__status = status

            def name(self):
                return 'name'

            def status(self):
                return self.__status

        class SomeFilter(moosetest.base.Filter):
            def execute(self, runner):
                self.remove()

        f = SomeFilter()
        self.assertFalse(f.isRemoved())
        self.assertTrue(f.apply(RunnerProxy()))
        self.assertTrue(f.isRemoved())
        f.reset()
        self.assertFalse(f.isRemoved())

        with mock.patch('moosetools.moosetest.base.Filter.status',
                        return_value=1), self.assertRaises(RuntimeError) as ex:
            f.apply(RunnerProxy())
        self.assertIn("An error occurred, on the filter", str(ex.exception))

        with self.assertRaises(RuntimeError) as ex:
            f.apply(RunnerProxy(1))
        self.assertIn("An error occurred, on the runner", str(ex.exception))


if __name__ == '__main__':
    unittest.main(module=__name__, verbosity=2)
