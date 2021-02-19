#!/usr/bin/env python
#* This file is part of MOOSETOOLS repository
#* https://www.github.com/idaholab/moosetools
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moose/blob/master/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html

import sys
import os
import unittest
import mock
import tempfile
import subprocess

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'bin'))
import fixup_headers


class TestFixupHeaders(unittest.TestCase):
    def assertInFile(self, filename, content):
        with open(filename, 'r') as fid:
            fcontent = fid.read()
        self.assertIn(content, fcontent)

    def assertNotInFile(self, filename, content):
        with open(filename, 'r') as fid:
            fcontent = fid.read()
        self.assertNotIn(content, fcontent)

    def setUp(self):
        _, self._src = tempfile.mkstemp(dir=os.path.dirname(__file__), suffix='.C')
        _, self._hdr = tempfile.mkstemp(dir=os.path.dirname(__file__), suffix='.h')
        _, self._py = tempfile.mkstemp(dir=os.path.dirname(__file__), suffix='.py')
        self._cwd = os.path.abspath(os.path.join(os.path.dirname(__file__)))
        self._files = [self._src, self._hdr, self._py]

    def tearDown(self):
        os.remove(self._src)
        os.remove(self._hdr)
        os.remove(self._py)

    def testDefault(self):
        r = subprocess.run(['../../bin/fixup_headers.py'], cwd=self._cwd)
        self.assertEqual(r.returncode, 0)

    @mock.patch('fixup_headers._git_ls_files')
    def testNotUpToDate(self, mock_files):
        mock_files.return_value = self._files
        r = fixup_headers.main()
        self.assertEqual(r, 1)

        self.assertNotInFile(self._src, 'MOOSETOOLS')
        self.assertNotInFile(self._hdr, 'MOOSETOOLS')
        self.assertNotInFile(self._py, 'MOOSETOOLS')

    @mock.patch('fixup_headers._git_ls_files')
    def testUpdate(self, mock_files):
        mock_files.return_value = self._files
        sys.argv += ['--update']
        r = fixup_headers.main()

        self.assertInFile(self._src, 'MOOSETOOLS')
        self.assertInFile(self._hdr, 'MOOSETOOLS')
        self.assertInFile(self._py, 'MOOSETOOLS')

        r = fixup_headers.main()
        self.assertEqual(r, 0)


if __name__ == '__main__':
    unittest.main(module=__name__, verbosity=2, buffer=True, exit=False)
