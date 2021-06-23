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

        with self.assertRaises(core.MooseException) as ex:
            moosetest.base.Controller()
        self.assertIn("The parameter 'prefix' is marked as required", str(ex.exception))

        ctrl = moosetest.base.Controller(prefix="foo")
        self.assertEqual(ctrl.name(), 'Controller')
        self.assertTrue(ctrl.isRunnable())

        with self.assertRaises(NotImplementedError) as ex:
            ctrl.execute(None, None)
        self.assertIn("The 'execute' method must be overridden.", str(ex.exception))

    def testControllers(self):
        ctrl = moosetest.base.Controller(prefix="foo")
        self.assertTrue(ctrl.isRunnable())
        ctrl.skip("Don't do it!")
        self.assertFalse(ctrl.isRunnable())
        self.assertIn("Don't do it!", ctrl.getReasons())

        ctrl.reset()
        self.assertTrue(ctrl.isRunnable())
        self.assertNotIn("Don't do it!", ctrl.getReasons())

    def testValidObjectParams(self):
        params = moosetest.base.Controller.validObjectParams()
        self.assertIsInstance(params, parameters.InputParameters)


if __name__ == '__main__':
    unittest.main(module=__name__, verbosity=2)
