#!/usr/bin/env python3
import io
import logging
import unittest
from moosetools import moosetest

class TestRunner(unittest.TestCase):
    def testDefault(self):


        runner = moosetest.runners.Runner(name='foo/bar.baz', log_level=logging.DEBUG)
        self.assertEqual(runner.getParam('platform'), None)

        #print(stream.getvalue())
        runner.init()
        print(runner.getStream())
        self.assertFalse(True)



if __name__ == '__main__':

    unittest.main(module=__name__, verbosity=2)
    #logging.basicConfig()
    #runner = moosetest.runners.Runner(log_level=logging.DEBUG, name='foo/bar.baz')
    #runner.init()
    #print(runner.stream())
