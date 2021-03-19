#!/usr/bin/env python3
import unittest
import parameters
from base import MooseObject, MooseException

class CustomObject(MooseObject):
    @staticmethod
    def validParams():
        params = MooseObject.validParams()
        params.add("year")
        return params

class TestMooseObject(unittest.TestCase):
    def testInitAndName(self):
        obj = MooseObject()
        self.assertFalse(obj.isParamValid("name"))
        self.assertEqual(obj.name(), None)

        obj = MooseObject(name='Andrew')
        self.assertEqual(obj.name(), 'Andrew')

    def testLogs(self):
        msg = "This is a test: {}"
        obj = MooseObject()

        with self.assertLogs(level='INFO') as log:
            obj.info(msg, 'INFO')
        self.assertEqual(len(log.output), 1)
        self.assertIn(msg.format('INFO'), log.output[0])

        with self.assertLogs(level='DEBUG') as log:
            obj.debug(msg, 'DEBUG')
        self.assertEqual(len(log.output), 1)
        self.assertIn(msg.format('DEBUG'), log.output[0])

        with self.assertLogs(level='WARNING') as log:
            obj.warning(msg, 'WARNING')
        self.assertEqual(len(log.output), 1)
        self.assertIn(msg.format('WARNING'), log.output[0])

        with self.assertLogs(level='ERROR') as log:
            obj.error(msg, 'ERROR')
        self.assertEqual(len(log.output), 1)
        self.assertIn(msg.format('ERROR'), log.output[0])

        with self.assertLogs(level='CRITICAL') as log:
            obj.critical(msg, 'CRITICAL')
        self.assertEqual(len(log.output), 1)
        self.assertIn(msg.format('CRITICAL'), log.output[0])

        with self.assertLogs(level='CRITICAL') as log:
            obj.critical(msg, 'CRITICAL', stack_info=True)
        self.assertEqual(len(log.output), 1)
        self.assertIn('Stack (most recent call last):', log.output[0])

        with self.assertLogs(level='CRITICAL') as log:
            try:
                raise MooseException("You messed up!")
            except MooseException:
                obj.exception(msg, 'CRITICAL')

        self.assertEqual(len(log.output), 1)
        self.assertIn(msg.format('CRITICAL'), log.output[0])

        with self.assertRaises(AssertionError) as e:
            obj.exception('You called exception wrong')
        self.assertEqual("No Exception raised, see `MooseObject.exception` for help.", str(e.exception))

        with self.assertRaises(AssertionError) as e:
            obj.info(42)
        self.assertEqual("The supplied 'message' must be a python `str` type, see `MooseObject.log`.", str(e.exception))

    def testParameters(self):
        obj = MooseObject()
        self.assertIs(obj._parameters, obj.parameters())

    def testIsParamValid(self):
        obj = MooseObject()
        self.assertFalse(obj.isParamValid('name'))

        obj = MooseObject(name='Andrew')
        self.assertTrue(obj.isParamValid('name'))

    def testGetParam(self):
        obj = MooseObject()
        self.assertEqual(obj.getParam('name'), None)

        obj = MooseObject(name='Andrew')
        self.assertEqual(obj.getParam('name'), 'Andrew')

        with self.assertRaises(MooseException) as me:
            obj.getParam('wrong')
        self.assertEqual("The parameter 'wrong' does not exist.", me.exception.message)

        with self.assertLogs(level='WARNING') as log:
            obj = MooseObject(error_mode=parameters.InputParameters.ErrorMode.WARNING)
            obj.getParam('wrong')
        self.assertEqual(len(log.output), 1)
        self.assertIn("The parameter 'wrong' does not exist.", log.output[0])

        with self.assertLogs(level='ERROR') as log:
            obj = MooseObject(error_mode=parameters.InputParameters.ErrorMode.ERROR)
            obj.getParam('wrong')
        self.assertEqual(len(log.output), 1)
        self.assertIn("The parameter 'wrong' does not exist.", log.output[0])

        with self.assertLogs(level='CRITICAL') as log:
            obj = MooseObject(error_mode=parameters.InputParameters.ErrorMode.CRITICAL)
            obj.getParam('wrong')
        self.assertEqual(len(log.output), 1)
        self.assertIn("The parameter 'wrong' does not exist.", log.output[0])

    def testCustom(self):
        obj = CustomObject(year=1980)
        self.assertEqual(obj.getParam('year'), 1980)

    def testType(self):
        obj = MooseObject()
        self.assertEqual(obj.getParam('type'), 'MooseObject')

        obj = CustomObject()
        self.assertEqual(obj.getParam('type'), 'CustomObject')

        with self.assertLogs(level='WARNING') as log:
            obj.parameters().set('type', "SomeOtherName")
        self.assertEqual(len(log.output), 1)
        self.assertIn("An attempt was made to change 'type', but it is marked as immutable.", log.output[0])





if __name__ == '__main__':
    unittest.main(module=__name__, verbosity=2)
