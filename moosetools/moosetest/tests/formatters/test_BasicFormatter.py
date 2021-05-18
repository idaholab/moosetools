#!/usr/bin/env python3
import io
import logging
import unittest
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
        self.assertEqual(dots, '.'*12)

    def testShortenLines(self):
        obj = BasicFormatter(max_lines=2)
        self.assertEqual(obj.shortenLines("one\ntwo\nthree"),
                         "one\n...OUTPUT REMOVED (MAX LINES: 2)...\nthree")

    def testShortenLine(self):
        obj = BasicFormatter()
        self.assertEqual(obj.shortenLine("andrew", 2), "a...w")

    def test_formatState(self):
        obj = BasicFormatter(width=60)

        kwargs = dict()
        kwargs['percent'] = 42
        kwargs['duration'] = 123.4
        kwargs['state'] = TestCase.Progress.RUNNING
        kwargs['name'] = "The:name/of/test"
        kwargs['reasons'] = None

        with mock.patch('moosetools.mooseutils.color_text', side_effect=lambda *args: args[0]):
            text = obj._formatState(**kwargs)
        self.assertEqual(text, "The:name/of/test...................RUNNING    42% [123.4s]  ")

        kwargs['reasons'] = ['reason']
        with mock.patch('moosetools.mooseutils.color_text', side_effect=lambda *args: args[0]):
            text = obj._formatState(**kwargs)
        self.assertEqual(text, "The:name/of/test..........[reason] RUNNING    42% [123.4s]  ")

        # Long reasons
        kwargs['reasons'] = ['the', 'reasons', 'are', 'many']
        with mock.patch('moosetools.mooseutils.color_text', side_effect=lambda *args: args[0]):
            text = obj._formatState(**kwargs)
        self.assertEqual(text, "The:name/of/test..[...; are; many] RUNNING    42% [123.4s]  ")

        # Long name
        kwargs['name'] = "This/is/a/long/name/that/will/get/shortened/in/the/middle"
        kwargs['reasons'] = None
        with mock.patch('moosetools.mooseutils.color_text', side_effect=lambda *args: args[0]):
            text = obj._formatState(**kwargs)
        self.assertEqual(text, "This/is/a/l.../the/middle..........RUNNING    42% [123.4s]  ")

        # Long name and long reasons
        kwargs['name'] = "This/is/a/long/name/that/will/get/shortened/in/the/middle"
        kwargs['reasons'] = ['the', 'reasons', 'are', 'many']
        with mock.patch('moosetools.mooseutils.color_text', side_effect=lambda *args: args[0]):
            text = obj._formatState(**kwargs)
        self.assertEqual(text, "This/is/a/l.../the/middle..[...ny] RUNNING    42% [123.4s]  ")

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

        obj = BasicFormatter(width=60, print_state=TestCase.Result.PASS)
        with mock.patch('moosetools.mooseutils.color_text', side_effect=lambda *args: args[0]):
            text = obj._formatResult(**kwargs)
        self.assertIn('sys.stdout:', text)
        self.assertIn('regular output', text)
        self.assertIn('sys.stderr:', text)
        self.assertIn('error output', text)

    def test_formatRunnerState(self):
        obj = BasicFormatter()
        with mock.patch('moosetools.moosetest.formatters.BasicFormatter._formatState') as fm:
            obj.formatRunnerState(name='Andrew')
        fm.assert_called_once_with(name='Andrew')

    def test_formatDifferState(self):
        obj = BasicFormatter()
        with mock.patch('moosetools.moosetest.formatters.BasicFormatter._formatState') as fm:
            obj.formatDifferState(name='Andrew', percent=42, duration=42)
        fm.assert_called_once_with(indent=' '*4, name='Andrew')

    def test_formatRunnerResult(self):
        obj = BasicFormatter()
        with mock.patch('moosetools.moosetest.formatters.BasicFormatter._formatResult') as fm:
            obj.formatRunnerResult(name='Andrew')
        fm.assert_called_once_with(name='Andrew')

    def test_formatDifferState(self):
        obj = BasicFormatter()
        with mock.patch('moosetools.moosetest.formatters.BasicFormatter._formatResult') as fm:
            obj.formatDifferResult(name='Andrew')
        fm.assert_called_once_with(indent=' '*4, name='Andrew')

    def test_formatComplete(self):
        obj = BasicFormatter()

        class TestCaseProxy(object):
            def __init__(self, name, state, t):
                self._name = name
                self.state = state
                self.time = t
            def name(self):
                return self._name

        complete = [TestCaseProxy('A', TestCase.Result.PASS, 10), TestCaseProxy('B', TestCase.Result.FATAL,20)]
        with mock.patch('moosetools.mooseutils.color_text', side_effect=lambda *args: args[0]):
            text = obj.formatComplete(complete)
        self.assertIn("Executed 2 tests", text)
        self.assertNotIn("in 40.0 seconds", text)
        self.assertIn("OK:1 SKIP:0 TIMEOUT:0 DIFF:0 ERROR:0 EXCEPTION:0 FATAL:1", text)

        kwargs = {'duration':40}
        with mock.patch('moosetools.mooseutils.color_text', side_effect=lambda *args: args[0]):
            text = obj.formatComplete(complete, **kwargs)

        self.assertIn("Executed 2 tests in 40.0 seconds", text)
        self.assertIn("OK:1 SKIP:0 TIMEOUT:0 DIFF:0 ERROR:0 EXCEPTION:0 FATAL:1", text)

        self.assertIn('Longest running tests(s)', text)
        self.assertIn('\n  B: 20s\n  A: 10s', text)


if __name__ == '__main__':
    unittest.main(module=__name__, verbosity=2, buffer=True)
