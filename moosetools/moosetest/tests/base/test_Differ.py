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
from moosetools.parameters import InputParameters
from moosetools.core import MooseException
from moosetools import moosetest


class TestDiffer(unittest.TestCase):
    def testDefault(self):

        with self.assertRaises(MooseException) as ex:
            moosetest.base.Differ()
        self.assertIn("The parameter 'name' is marked as required", str(ex.exception))

        diff = moosetest.base.Differ(name="foo")
        self.assertEqual(diff.name(), 'foo')

        with self.assertRaises(NotImplementedError) as ex:
            diff.execute(None, None, None)
        self.assertIn("The 'execute' method must be overridden.", str(ex.exception))

    def testControllers(self):
        class ProxyController(object):
            @staticmethod
            def validObjectParams():
                params = InputParameters()
                params.add('platform')
                return params

            def getParam(self, value):
                return 'test'

        diff = moosetest.base.make_differ(moosetest.base.Differ, [
            ProxyController(),
        ],
                                          name='name',
                                          test_platform='TempleOS')
        self.assertIn('test', diff.parameters())
        self.assertIn('platform', diff.getParam('test'))
        self.assertEqual(diff.getParam('test_platform'), 'TempleOS')


if __name__ == '__main__':
    unittest.main(module=__name__, verbosity=2)
