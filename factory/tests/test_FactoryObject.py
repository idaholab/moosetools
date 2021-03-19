#!/usr/bin/env python3
#* This file is part of MOOSETOOLS repository
#* https://www.github.com/idaholab/moosetools
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moosetools/blob/main/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html
import unittest
import parameters
import factory

class TestParameter(unittest.TestCase):
    def testBase(self):
        obj = factory.FactoryObject()
        self.assertIsNone(obj.getParam('name'))
        self.assertFalse(obj.isParamValid('name'))
        self.assertIsInstance(obj.parameters(), parameters.InputParameters)

        obj = factory.FactoryObject(name='object')
        self.assertEqual(obj.getParam('name'), 'object')
        self.assertTrue(obj.isParamValid('name'))

        self.assertIsNone(obj.getParam('wrong'))
        self.assertFalse(obj.isParamValid('wrong'))


    def testCustom(self):
        class CustomObject(factory.FactoryObject):
            @staticmethod
            def validParams():
                params = factory.FactoryObject.validParams()
                params.add('year', doc="The best year")
                return params

        obj = CustomObject()
        self.assertIsNone(obj.getParam('year'))
        self.assertFalse(obj.isParamValid('year'))

        obj = CustomObject(year=1980)
        self.assertEqual(obj.getParam('year'), 1980)
        self.assertTrue(obj.isParamValid('year'))





if __name__ == '__main__':
    unittest.main(module=__name__, verbosity=2)
