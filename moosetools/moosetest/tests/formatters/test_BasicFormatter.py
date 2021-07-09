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
import argparse
from unittest import mock
from moosetools.moosetest.base import TestCase
from moosetools.moosetest.formatters import shorten_line, shorten_text, ShortenMode
from moosetools.moosetest.formatters import BasicFormatter


class TestShorten(unittest.TestCase):
    def test_short_line(self):
        with self.assertRaises(RuntimeError) as e:
            shorten_line("\n", 42)
        self.assertIn("The supplied text must be a single line", str(e.exception))

        self.assertEqual(shorten_line("andrew", 42), "andrew")

        text = "The ultimate test of your greatness is the way you treat every human being."
        short = shorten_line(text, 15)
        self.assertEqual(short, "The ult...being.")
        self.assertEqual(len(short), 16)

        short = shorten_line(text, 14, replace='#####')
        self.assertEqual(short, "The ult#####being.")
        self.assertEqual(len(short), 18)

        short = shorten_line(text, 14, mode=ShortenMode.BEGIN)
        self.assertEqual(short, "...y human being.")
        self.assertEqual(len(short), 17)

        short = shorten_line(text, 22, mode=ShortenMode.END)
        self.assertEqual(short, "The ultimate test of y...")
        self.assertEqual(len(short), 25)

    def test_short_text(self):
        self.assertEqual(shorten_text("andrew", 42), "andrew")

        text = "This\nthat\nand\nthe\nother"
        short = shorten_text(text, 2)
        self.assertEqual(short, "This\n...\nother")

        short = shorten_text(text, 2, replace='####')
        self.assertEqual(short, "This\n####\nother")

        short = shorten_text(text, 3, mode=ShortenMode.BEGIN)
        self.assertEqual(short, "...\nand\nthe\nother")

        short = shorten_text(text, 3, mode=ShortenMode.END)
        self.assertEqual(short, "This\nthat\nand\n...")


class TestBasicFormatter(unittest.TestCase):
    def testDefault(self):
        obj = BasicFormatter()
        self.assertIsInstance(obj._max_state_width, int)
        self.assertTrue(obj._max_state_width > 0)

        self.assertIsInstance(obj._extra_width, int)
        self.assertTrue(obj._extra_width > 0)

    def testWidth(self):
        obj = BasicFormatter(width=42)
        self.assertEqual(obj.width(), 42)

        with mock.patch('shutil.get_terminal_size', return_value=(1980, None)):
            obj = BasicFormatter()
            self.assertEqual(obj.width(), 1980)

    def testFill(self):
        obj = BasicFormatter(width=40)
        dots = obj.fill("andrew", "edward")
        self.assertEqual(dots, '.' * 12)

    def testShortenLines(self):
        obj = BasicFormatter(max_lines=2)
        self.assertEqual(obj.shortenLines("one\ntwo\nthree"),
                         "one\n...OUTPUT REMOVED (MAX LINES: 2)...\nthree")

    def testShortenLine(self):
        obj = BasicFormatter()
        self.assertEqual(obj.shortenLine("andrew", 2), "a...w")

    def test_formatProgress(self):
        obj = BasicFormatter(width=60)

        kwargs = dict()
        kwargs['percent'] = 42
        kwargs['duration'] = 123.4
        kwargs['state'] = TestCase.Progress.RUNNING
        kwargs['name'] = "The:name/of/test"
        kwargs['reasons'] = None

        with mock.patch('moosetools.mooseutils.color_text', side_effect=lambda *args: args[0]):
            text = obj._formatProgress(**kwargs)
        self.assertEqual(text, "The:name/of/test...................RUNNING    42% [123.4s]  ")

        kwargs['reasons'] = ['reason']
        with mock.patch('moosetools.mooseutils.color_text', side_effect=lambda *args: args[0]):
            text = obj._formatProgress(**kwargs)
        self.assertEqual(text, "The:name/of/test..........[reason] RUNNING    42% [123.4s]  ")

        # Long reasons
        kwargs['reasons'] = ['the', 'reasons', 'are', 'many']
        with mock.patch('moosetools.mooseutils.color_text', side_effect=lambda *args: args[0]):
            text = obj._formatProgress(**kwargs)
        self.assertEqual(text, "The:name/of/test..[...; are; many] RUNNING    42% [123.4s]  ")

        # Long name
        kwargs['name'] = "This/is/a/long/name/that/will/get/shortened/in/the/middle"
        kwargs['reasons'] = None
        with mock.patch('moosetools.mooseutils.color_text', side_effect=lambda *args: args[0]):
            text = obj._formatProgress(**kwargs)
        self.assertEqual(text, "This/is/a/l.../the/middle..........RUNNING    42% [123.4s]  ")

        # Long name and long reasons
        kwargs['name'] = "This/is/a/long/name/that/will/get/shortened/in/the/middle"
        kwargs['reasons'] = ['the', 'reasons', 'are', 'many']
        with mock.patch('moosetools.mooseutils.color_text', side_effect=lambda *args: args[0]):
            text = obj._formatProgress(**kwargs)
        self.assertEqual(text, "This/is/a/l.../the/middle..[...ny] RUNNING    42% [123.4s]  ")

        # Max
        obj.parameters().setValue('min_print_progress', TestCase.Result.ERROR)
        with mock.patch('moosetools.mooseutils.color_text', side_effect=lambda *args: args[0]):
            text = obj._formatProgress(**kwargs)
        self.assertIsNone(text)

    def test_formatResult(self):
        obj = BasicFormatter(width=60)

        kwargs = dict()
        kwargs['percent'] = 42
        kwargs['duration'] = 123.4
        kwargs['state'] = TestCase.Result.PASS
        kwargs['name'] = "The:name/of/test"
        kwargs['reasons'] = None
        kwargs['stdout'] = 'regular output\n'
        kwargs['stderr'] = 'error output\n'

        with mock.patch('moosetools.mooseutils.color_text', side_effect=lambda *args: args[0]):
            text = obj._formatResult(**kwargs)
        self.assertEqual(text, None)

        obj = BasicFormatter(width=60, min_print_result=TestCase.Result.PASS)
        with mock.patch('moosetools.mooseutils.color_text', side_effect=lambda *args: args[0]):
            text = obj._formatResult(**kwargs)
        self.assertIn('regular output', text)
        self.assertIn('error output', text)

        kwargs['stdout'] = None
        kwargs['stderr'] = None
        with mock.patch('moosetools.mooseutils.color_text', side_effect=lambda *args: args[0]):
            text = obj._formatResult(**kwargs)
        self.assertIn('', text)

        # Max
        kwargs['stdout'] = 'regular output\n'
        obj.parameters().setValue('min_print_result', TestCase.Result.ERROR)
        with mock.patch('moosetools.mooseutils.color_text', side_effect=lambda *args: args[0]):
            text = obj._formatResult(**kwargs)
        self.assertIsNone(text)

    def test_formatRunnerProgress(self):
        obj = BasicFormatter()
        with mock.patch('moosetools.moosetest.formatters.BasicFormatter._formatProgress') as fm:
            obj.formatRunnerProgress(name='Andrew')
        fm.assert_called_once_with(name='Andrew')

    def test_formatDifferProgress(self):
        obj = BasicFormatter()
        with mock.patch('moosetools.moosetest.formatters.BasicFormatter._formatProgress') as fm:
            obj.formatDifferProgress(name='Andrew', percent=42, duration=42)
        fm.assert_called_once_with(indent=' ' * 4, name='Andrew')

    def test_formatRunnerResult(self):
        obj = BasicFormatter()
        with mock.patch('moosetools.moosetest.formatters.BasicFormatter._formatResult') as fm:
            obj.formatRunnerResult(name='Andrew')
        fm.assert_called_once_with(name='Andrew')

    def test_formatDifferProgress(self):
        obj = BasicFormatter()
        with mock.patch('moosetools.moosetest.formatters.BasicFormatter._formatResult') as fm:
            obj.formatDifferResult(name='Andrew')
        fm.assert_called_once_with(indent=' ' * 4, name='Andrew')

    def test_formatComplete(self):
        obj = BasicFormatter()

        class TestCaseProxy(object):
            def __init__(self, name, state, t):
                self._name = name
                self.state = state
                self.time = t

            def name(self):
                return self._name

        complete = [
            TestCaseProxy('A', TestCase.Result.PASS, 10),
            TestCaseProxy('B', TestCase.Result.FATAL, 20)
        ]
        with mock.patch('moosetools.mooseutils.color_text', side_effect=lambda *args: args[0]):
            text = obj.formatComplete(complete)
        self.assertIn("Executed 2 tests", text)
        self.assertNotIn("in 40.0 seconds", text)
        self.assertIn("REMOVE:0 SKIP:0 OK:1 TIMEOUT:0 DIFF:0 ERROR:0 EXCEPTION:0 FATAL:1", text)

        kwargs = {'duration': 40}
        with mock.patch('moosetools.mooseutils.color_text', side_effect=lambda *args: args[0]):
            text = obj.formatComplete(complete, **kwargs)

        self.assertIn("Executed 2 tests in 40.0 seconds", text)
        self.assertIn("REMOVE:0 SKIP:0 OK:1 TIMEOUT:0 DIFF:0 ERROR:0 EXCEPTION:0 FATAL:1", text)

        self.assertIn('Longest running test(s)', text)
        self.assertIn('\n  20.00s B\n  10.00s A', text)

    def test_setup(self):
        obj = BasicFormatter()
        args = argparse.Namespace(min_print_result='PASS', min_print_progress='PASS', verbose=False)

        self.assertEqual(obj.getParam('min_print_result'), TestCase.Result.DIFF)
        self.assertEqual(obj.getParam('min_print_progress'), TestCase.Result.SKIP)
        obj._setup(args)
        self.assertEqual(obj.getParam('min_print_result'), TestCase.Result.PASS)
        self.assertEqual(obj.getParam('min_print_progress'), TestCase.Result.PASS)

        args.verbose = True
        obj._setup(args)
        self.assertEqual(obj.getParam('min_print_result'), TestCase.Result.REMOVE)
        self.assertEqual(obj.getParam('min_print_progress'), TestCase.Result.REMOVE)


if __name__ == '__main__':
    unittest.main(module=__name__, verbosity=2, buffer=True)
