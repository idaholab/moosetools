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
import unittest
import mooseutils

try:
    from PyQt5 import QtWidgets, QtCore
    MOOSE_USE_QT5 = True
except:
    MOOSE_USE_QT5 = False


class TestMooseMessageDialog(unittest.TestCase):
    """
    Tests the usage of the various messages functions in message package.
    """

    app = QtWidgets.QApplication(sys.argv) if MOOSE_USE_QT5 else None

    @unittest.skipIf(not MOOSE_USE_QT5, 'PyQt5 not installed')
    def testMooseMessageDefault(self):
        """
        Test the default dialog message.
        """
        box = mooseutils.mooseMessage("A message", dialog=True, test=True)
        self.assertTrue(box.text() == "A message")
        self.assertTrue(box.icon() == QtWidgets.QMessageBox.NoIcon)

    @unittest.skipIf(not MOOSE_USE_QT5, 'PyQt5 not installed')
    def testMooseMessageWarning(self):
        """
        Test the warning dialog message.
        """
        box = mooseutils.mooseWarning("A message", dialog=True, test=True)
        self.assertIn("A message", box.text())
        self.assertIn("WARNING", box.text())
        self.assertTrue(box.icon() == QtWidgets.QMessageBox.Warning)

    @unittest.skipIf(not MOOSE_USE_QT5, 'PyQt5 not installed')
    def testMooseMessageError(self):
        """
        Test the error dialog message.
        """
        box = mooseutils.mooseError("A message", dialog=True, test=True)
        self.assertIn("A message", box.text())
        self.assertIn("ERROR", box.text())
        self.assertTrue(box.icon() == QtWidgets.QMessageBox.Critical)


if __name__ == '__main__':
    unittest.main(module=__name__, verbosity=2, buffer=True, exit=False)
