#!/usr/bin/env python3
#* This file is part of MOOSETOOLS repository
#* https://www.github.com/idaholab/moosetools
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moosetools/blob/main/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html

import sys
import io
import unittest
import threading
import time
import logging
import concurrent.futures
import collections
import multiprocessing
from moosetools import mooseutils
from moosetools import moosetest


def print_stdout(text, wait):
    time.sleep(wait)
    with mooseutils.RedirectOutput() as out:
        print(text)
    return out.stdout


def print_stderr(text, wait):
    time.sleep(wait)
    with mooseutils.RedirectOutput() as out:
        print(text, file=sys.stderr)
    return out.stderr


def log_stderr(text, wait):
    time.sleep(wait)
    with mooseutils.RedirectOutput() as out:
        logging.error(text)
    return out.stderr


class Test(unittest.TestCase):
    def test_PrintSerial(self):
        with mooseutils.RedirectOutput() as out:
            print("stdout")
        self.assertEqual(out.stdout, "stdout\n")

        with mooseutils.RedirectOutput() as out:
            print("stderr", file=sys.stderr)
        self.assertEqual(out.stderr, "stderr\n")

    def test_PrintThreads(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(print_stdout, text, tm)
                for text, tm in [('two', 2), ('zero', 0), ('one', 1)]
            ]
        results = set(f.result() for f in concurrent.futures.as_completed(futures))
        self.assertEqual(results, set(['two\n', 'one\n', 'zero\n']))

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(print_stderr, text, tm)
                for text, tm in [('two', 2), ('zero', 0), ('one', 1)]
            ]
        results = set(f.result() for f in concurrent.futures.as_completed(futures))
        self.assertEqual(results, set(['two\n', 'one\n', 'zero\n']))

    def test_LogSerial(self):

        with mooseutils.RedirectOutput() as out:
            print("test print")
            logging.error("test log")
        self.assertIn("test print\n", out.stdout)
        self.assertIn("test log\n", out.stderr)

        logging.basicConfig()
        l = logging.getLogger()
        with mooseutils.RedirectOutput() as out:
            print("test print")
            l.error("test log")
        self.assertIn("test print\n", out.stdout)
        self.assertIn("test log\n", out.stderr)

    def test_LogThreads(self):

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(log_stderr, text, tm)
                for text, tm in [('two', 2), ('zero', 0), ('one', 1)]
            ]
        results = set(f.result() for f in concurrent.futures.as_completed(futures))
        self.assertEqual(results, set(['ERROR:root:two\n', 'ERROR:root:one\n',
                                       'ERROR:root:zero\n']))

    def test_raises(self):
        with self.assertRaises(RuntimeError) as cm:
            with mooseutils.RedirectOutput() as out:
                raise RuntimeError("raise in context")
        self.assertIn("raise in context", str(cm.exception))

    def test_MergeToStdout(self):
        with mooseutils.RedirectOutput(merge=True) as out:
            print("test print")
            logging.error("test log")
        self.assertIn("test print\n", out.stdout)
        self.assertIn("test log\n", out.stdout)


if __name__ == '__main__':
    unittest.main(module=__name__, verbosity=2)
