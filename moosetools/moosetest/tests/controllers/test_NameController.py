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
from moosetools.parameters import InputParameters
from moosetools.core import MooseException, MooseObject
from moosetools.moosetest.controllers import NameController
from moosetools.moosetest.base import make_differ, TestCase


class TestObject(MooseObject):
    pass


class TestNameController(unittest.TestCase):
    def testDefault(self):
        ctrl = NameController()
        self.assertEqual(ctrl.state(), None)
        self.assertIsNone(ctrl.getParam('prefix'))
        self.assertIsNone(ctrl.validObjectParams())

    def test_remove_if_text_in_name(self):
        ctrl = NameController()
        obj = MooseObject(name='Andrew')
        ctrl.parameters().setValue('remove_if_text_in_name', 'dr')
        ctrl.execute(obj, None)
        self.assertEqual(ctrl.state(), TestCase.Result.REMOVE)

    def test_remove_if_text_not_in_name(self):
        ctrl = NameController()
        obj = MooseObject(name='Andrew')
        ctrl.parameters().setValue('remove_if_text_not_in_name', 'Ali')
        ctrl.execute(obj, None)
        self.assertEqual(ctrl.state(), TestCase.Result.REMOVE)

    def test_remove_if_re_match_name(self):
        ctrl = NameController()
        obj = MooseObject(name='Andrew')
        ctrl.parameters().setValue('remove_if_re_match_name', '\w+')
        ctrl.execute(obj, None)
        self.assertEqual(ctrl.state(), TestCase.Result.REMOVE)

    def test_remove_if_re_not_match_name(self):
        ctrl = NameController()
        obj = MooseObject(name='Andrew')
        ctrl.parameters().setValue('remove_if_re_not_match_name', '\d+')
        ctrl.execute(obj, None)
        self.assertEqual(ctrl.state(), TestCase.Result.REMOVE)


if __name__ == '__main__':
    unittest.main(module=__name__, verbosity=2)
