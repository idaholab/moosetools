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
import argparse
from moosetools.moosetest.filters import NameFilter


class RunnerProxy(object):
    def name(self):
        return 'the_runner'

    def status(self):
        return 0


class TestNameFilter(unittest.TestCase):
    def testDefault(self):
        f = NameFilter()
        r = RunnerProxy()

        self.assertFalse(f.apply(r))

        f.parameters().setValue('text_in', 'the_')
        self.assertFalse(f.apply(r))

        f.parameters().setValue('text_in', 'not_this')
        self.assertTrue(f.apply(r))

    def test_validCommandLineArguments(self):
        parser = argparse.ArgumentParser()
        f = NameFilter()
        f.validCommandLineArguments(parser, f.parameters())
        args = parser.parse_args(args=[])
        self.assertIn('text_in', args)

    def test_setup(self):
        f = NameFilter()
        args = argparse.Namespace(text_in='Andrew')
        f._setup(args)
        self.assertEqual(f.getParam('text_in'), 'Andrew')


if __name__ == '__main__':
    unittest.main(module=__name__, verbosity=2)
