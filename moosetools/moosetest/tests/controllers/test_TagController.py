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
from moosetools.moosetest.controllers import TagController
from moosetools.moosetest.base import make_differ, TestCase, Runner


class TestObject(MooseObject):
    @staticmethod
    def validParams():
        params = MooseObject.validParams()

        tag = InputParameters()
        tag.add('names', array=True, vtype=str)
        params.add('tag', default=tag)
        return params


class TestNameController(unittest.TestCase):
    def test(self):
        ctrl = TagController(allowable_names=('avail', ))
        obj = TestObject(name='Andrew')
        ctrl.execute(obj, obj.getParam('tag'))
        self.assertEqual(ctrl.state(), None)

        obj.parameters().setValue('tag', 'names', ('avail', ))
        ctrl.execute(obj, obj.getParam('tag'))
        self.assertEqual(ctrl.state(), None)

        obj.parameters().setValue('tag', 'names', ('not_avail', ))
        ctrl.execute(obj, obj.getParam('tag'))
        self.assertEqual(ctrl.state(), TestCase.Result.SKIP)


if __name__ == '__main__':
    unittest.main(module=__name__, verbosity=2)
