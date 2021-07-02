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
from moosetools import core
from moosetools import parameters
from moosetools import moosetest


class TestController(unittest.TestCase):
    def testDefault(self):

        ctrl = moosetest.base.Controller(prefix="foo")
        self.assertEqual(ctrl.name(), 'Controller')
        self.assertIsNone(ctrl.state())

        with self.assertRaises(NotImplementedError) as ex:
            ctrl.execute(None, None)
        self.assertIn("The 'execute' method must be overridden.", str(ex.exception))

    def test_state(self):
        ctrl = moosetest.base.Controller(prefix="foo")
        self.assertIsNone(ctrl.state())
        ctrl.skip("Don't do it!")
        self.assertEqual(ctrl.state(), moosetest.base.TestCase.Result.SKIP)
        self.assertIn("Don't do it!", ctrl.getReasons())

        ctrl.reset()
        self.assertIsNone(ctrl.state())
        self.assertNotIn("Don't do it!", ctrl.getReasons())

        ctrl.remove("Don't do it!")
        self.assertEqual(ctrl.state(), moosetest.base.TestCase.Result.REMOVE)
        self.assertIn("Don't do it!", ctrl.getReasons())

    def test_validObjectParams(self):
        params = moosetest.base.Controller.validObjectParams()
        self.assertIsInstance(params, parameters.InputParameters)

    def test_validCommandLineArguments(self):
        params = moosetest.base.Controller.validCommandLineArguments(None, None)
        self.assertIsNone(params)

    def test_setup(self):
        f = moosetest.base.Controller(prefix='foo')
        self.assertIsNone(f._setup(None))


if __name__ == '__main__':
    unittest.main(module=__name__, verbosity=2)
