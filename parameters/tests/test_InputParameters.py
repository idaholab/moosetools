#!/usr/bin/env python3
#* This file is part of MOOSETOOLS repository
#* https://www.github.com/idaholab/moosetools
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moosetools/blob/main/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html

import os
import sys
import re
import unittest

from base import MooseException
from parameters import InputParameters, Parameter


class TestInputParameters(unittest.TestCase):
    def testAdd(self):
        params = InputParameters()
        params.add('foo')
        self.assertEqual(list(params.keys()), ['error_mode', 'foo'])
        self.assertFalse(params.isValid('foo'))
        self.assertIn('foo', params)
        self.assertIsNone(params.get('foo'))
        self.assertTrue(params.hasParameter('foo'))

        params.set('error_mode', InputParameters.ErrorMode.ERROR) # use error to capture return
        with self.assertLogs(level='ERROR') as log:
            params.add('foo')
        self.assertEqual(len(log.output), 1)
        self.assertIn("Cannot add parameter, the parameter 'foo' already exists.", log.output[0])

        sub = InputParameters()
        params.add('bar', InputParameters())
        with self.assertLogs(level='ERROR') as log:
            params.add('bar_something')
        self.assertEqual(len(log.output), 1)
        self.assertIn(
            "Cannot add a parameter with the name 'bar_something', a sub parameter exists with the name 'bar'.",
            log.output[0])

    def testContains(self):
        params = InputParameters()
        params.add('foo')
        self.assertIn('foo', params)
        self.assertNotIn('bar', params)

    def testIAdd(self):
        params = InputParameters()
        params.add('foo')

        params2 = InputParameters()
        params2.add('bar')

        params += params2
        self.assertIn('foo', params)
        self.assertIn('bar', params)

    def testItems(self):
        params = InputParameters()
        params.add('foo', 1949)
        params.add('bar', 1980)

        gold = [('error_mode', InputParameters.ErrorMode.EXCEPTION), ('foo', 1949), ('bar', 1980)]
        for i, (k, v) in enumerate(params.items()):
            self.assertEqual(k, gold[i][0])
            self.assertEqual(v, gold[i][1])

    def testValues(self):
        params = InputParameters()
        params.add('foo', 1949)
        params.add('bar', 1980)

        gold = [InputParameters.ErrorMode.EXCEPTION, 1949, 1980]
        for i, v in enumerate(params.values()):
            self.assertEqual(v, gold[i])

    def testKeys(self):
        params = InputParameters()
        params.add('foo', 1949)
        params.add('bar', 1980)

        gold = ['error_mode', 'foo', 'bar']
        for i, v in enumerate(params.keys()):
            self.assertEqual(v, gold[i])

    def testRemove(self):
        params = InputParameters()
        params.add('foo')
        self.assertTrue(params.hasParameter('foo'))
        params.remove('foo')
        self.assertFalse(params.hasParameter('foo'))

        with self.assertRaises(MooseException) as e:
            params.remove('bar')
        self.assertIn("The parameter 'bar' does not exist", str(e.exception))

    def testIsValid(self):
        params = InputParameters()
        params.add('foo')
        self.assertFalse(params.isValid('foo'))
        params.set('foo', 1980)
        self.assertTrue(params.isValid('foo'))

        with self.assertRaises(MooseException) as e:
            params.isValid('bar')
        self.assertIn("The parameter 'bar' does not exist", str(e.exception))

    def testSetDefault(self):
        params = InputParameters()
        params.add('foo', vtype=int)
        self.assertIsNone(params.get('foo'))
        params.setDefault('foo', 1980)
        self.assertEqual(params.get('foo'), 1980)

        params.add('bar', default=1980)
        params.setDefault('bar', 1949)
        self.assertEqual(params.get('bar'), 1980)
        self.assertEqual(params.getDefault('bar'), 1949)

        with self.assertRaises(MooseException) as e:
            params.setDefault('other', 1980)
        self.assertIn("The parameter 'other' does not exist", str(e.exception))

        params.set('error_mode', InputParameters.ErrorMode.ERROR) # use error to capture return
        with self.assertLogs(level='ERROR') as log:
            params.setDefault('foo', 'wrong')
        self.assertEqual(len(log.output), 1)
        self.assertIn("'foo' must be of type", log.output[0])

    def testGetDefault(self):
        params = InputParameters()
        params.add('foo', default=42)
        params.set('foo', 54)
        self.assertEqual(params.getDefault('foo'), 42)

        with self.assertRaises(MooseException) as e:
            params.getDefault('bar')
        self.assertIn("The parameter 'bar' does not exist", str(e.exception))

    def testIsDefault(self):
        params = InputParameters()
        params.add('foo', default=1949)
        self.assertTrue(params.isDefault('foo'))
        params.set('foo', 1980)
        self.assertFalse(params.isDefault('foo'))

        with self.assertRaises(MooseException) as e:
            params.isDefault('bar')
        self.assertIn("The parameter 'bar' does not exist", str(e.exception))

    def testIsSetByUser(self):
        params = InputParameters()
        params.add('foo', default=1949)
        self.assertFalse(params.isSetByUser('foo'))
        params.set('foo', 1980)
        self.assertFalse(params.isDefault('foo'))

    def testSet(self):
        params = InputParameters()
        params.add('foo', vtype=int)
        params.set('foo', 42)
        self.assertTrue(params.isValid('foo'))
        self.assertIn('foo', params)
        self.assertIsNotNone(params.get('foo'))
        self.assertEqual(params.get('foo'), 42)
        self.assertTrue(params.hasParameter('foo'))

        with self.assertRaises(MooseException) as e:
            params.set('bar', 1980)
        self.assertIn("The parameter 'bar' does not exist", str(e.exception))

        # Sub-options
        params2 = InputParameters()
        params2.add('bar')
        params.add('sub', params2)
        params.set('sub', {'bar': 2013})
        self.assertEqual(params2.get('bar'), 2013)
        self.assertEqual(params.get('sub').get('bar'), 2013)

        params2.set('bar', 1954)
        self.assertEqual(params2.get('bar'), 1954)
        self.assertEqual(params.get('sub').get('bar'), 1954)

        params3 = InputParameters()
        params3.add('bar', default=2011)
        params.set('sub', params3)
        self.assertEqual(params2.get('bar'), 1954)
        self.assertEqual(params3.get('bar'), 2011)
        self.assertEqual(params.get('sub').get('bar'), 2011)

        params.set('sub', 'bar', 1944)
        self.assertEqual(params2.get('bar'), 1954)
        self.assertEqual(params3.get('bar'), 1944)
        self.assertEqual(params.get('sub').get('bar'), 1944)

        with self.assertRaises(MooseException) as e:
            params.set('foo', 1980, 2011)
        self.assertIn("Extra argument(s) found: 1980", str(e.exception))

        params.set('error_mode', InputParameters.ErrorMode.ERROR) # log to capture return
        with self.assertLogs(level='ERROR') as log:
            params.set('foo')
        self.assertEqual(len(log.output), 1)
        self.assertIn("One or more names must be supplied.", log.output[0])

        params.set('error_mode', InputParameters.ErrorMode.ERROR)
        with self.assertLogs(level='ERROR') as log:
            params.set('foo', 'wrong')
        self.assertEqual(len(log.output), 1)
        self.assertIn("'foo' must be of type", log.output[0])

    def testGet(self):
        params = InputParameters()
        params.add('foo', default=1980)
        self.assertEqual(params.get('foo'), 1980)

        with self.assertRaises(MooseException) as e:
            params.get('bar')
        self.assertIn("The parameter 'bar' does not exist", str(e.exception))

    def testHasParameter(self):
        params = InputParameters()
        params.add('foo')
        self.assertTrue(params.hasParameter('foo'))
        self.assertFalse(params.hasParameter('bar'))

    def testUpdate(self):
        params = InputParameters()
        params.add('foo')
        params.update(foo=1980)
        self.assertEqual(params.get('foo'), 1980)

        params2 = InputParameters()
        params2.add('foo', 2013)

        params.update(params2)
        self.assertEqual(params.get('foo'), 2013)

        with self.assertRaises(MooseException) as e:
            params.update(foo=2011, bar=2013)
        self.assertIn("The parameter 'bar' does not exist.", str(e.exception))

        with self.assertRaises(MooseException) as e:
            params.update('wrong')
        self.assertIn("The supplied arguments must be InputParameters object", str(e.exception))

    def testErrorMode(self):
        params = InputParameters()
        params.set('error_mode', InputParameters.ErrorMode.WARNING)
        with self.assertLogs(level='WARNING') as log:
            self.assertIsNone(params.isValid('bar'))
        self.assertEqual(len(log.output), 1)
        self.assertIn("The parameter 'bar' does not exist", log.output[0])

        params = InputParameters()
        params.set('error_mode', InputParameters.ErrorMode.ERROR)
        with self.assertLogs(level='ERROR') as log:
            self.assertIsNone(params.isValid('bar'))
        self.assertEqual(len(log.output), 1)
        self.assertIn("The parameter 'bar' does not exist", log.output[0])

        params = InputParameters()
        params.set('error_mode', InputParameters.ErrorMode.CRITICAL)
        with self.assertLogs(level='CRITICAL') as log:
            self.assertIsNone(params.isValid('bar'))
        self.assertEqual(len(log.output), 1)
        self.assertIn("The parameter 'bar' does not exist", log.output[0])

        params = InputParameters()
        params.set('error_mode', InputParameters.ErrorMode.EXCEPTION)
        with self.assertRaises(MooseException) as e:
            self.assertIsNone(params.isValid('bar'))
        self.assertIn("The parameter 'bar' does not exist", str(e.exception))

    def testSetWithSubOption(self):
        andrew = InputParameters()
        andrew.add('year')

        people = InputParameters()
        people.add('andrew', default=andrew)

        people.set('andrew', 'year', 1949)
        self.assertEqual(andrew.get('year'), 1949)

        people.set('andrew', {'year': 1954})
        self.assertEqual(andrew.get('year'), 1954)

        people.set('andrew_year', 1977)
        self.assertEqual(andrew.get('year'), 1977)

        yo_dawg = InputParameters()
        yo_dawg.add('nunchuck')
        andrew.add('skills', yo_dawg)
        self.assertEqual(yo_dawg.get('nunchuck'), None)

        people.set('andrew_skills', 'nunchuck', True)
        self.assertEqual(yo_dawg.get('nunchuck'), True)

        with self.assertRaises(MooseException) as e:
            people.set('andrew_day', 'python', False)
        self.assertIn("The parameter 'day' does not exist", str(e.exception))

        with self.assertRaises(MooseException) as e:
            people.set('andrew_skills', 'python', False)
        self.assertIn("The parameter 'python' does not exist.", str(e.exception))

    def testGetWithSubOption(self):
        unit = InputParameters()
        unit.add('name', 'pts')

        font = InputParameters()
        font.add('size', default=24)
        font.add('unit', unit)

        text = InputParameters()
        text.add('font', font)

        self.assertEqual(text.get('font', 'size'), 24)
        self.assertEqual(text.get('font', 'unit', 'name'), 'pts')

        self.assertEqual(text.get('font_size'), 24)
        self.assertEqual(text.get('font_unit_name'), 'pts')

    def testToString(self):
        font = InputParameters()
        font.add('size', default=24)
        font.add('name')

        text = InputParameters()
        text.add('font', font)

        self.assertEqual(str(text), text.toString())
        self.assertIn('font\n', text.toString())
        self.assertIn('font_size\n', text.toString())

        self.assertIn('size\n', font.toString())
        self.assertIn('name\n', font.toString())


        self.assertIn('size\n', font.toString('size'))
        self.assertNotIn('name\n', font.toString('size'))

    def testValidate(self):
        font = InputParameters()
        font.add('size', default=24)
        font.add('name', required=True)

        with self.assertRaises(MooseException) as e:
            font.validate()
        self.assertIn("The Parameter 'name' is marked as required, but no value is assigned", str(e.exception))

    def testParameter(self):
        font = InputParameters()
        font.add('size', default=24)
        p = font.parameter('size')
        self.assertIsInstance(p, Parameter)

if __name__ == '__main__':
    unittest.main(module=__name__, verbosity=2, buffer=True, exit=False)
