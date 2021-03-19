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
import os
import unittest
from bin import jsondiff


class TestJsonDiff(unittest.TestCase):
    def setUpValidRelativeError(self):
        """Test Case: Valid command-line arguments using the relative error flag where the user specifies the relative error"""
        file01 = os.path.join('bin', 'jsondiff.py')
        A = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..', 'diff', 'tests', 'samples', 'json',
                         'sample05', 'sample05A.json'))
        B = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..', 'diff', 'tests', 'samples', 'json',
                         'sample05', 'sample05B.json'))
        relative_error = '1e-9'
        sys.argv = [file01, A, B, '--rel_tol', relative_error]
        return A, B, relative_error

    def setUpValidRelativeErrorDefault(self):
        """Test Case: Valid command-line arguments using the relative error flag where the default value is used for the relative error"""
        file01 = os.path.join('bin', 'jsondiff.py')
        A = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..', 'diff', 'tests', 'samples', 'json',
                         'sample05', 'sample05A.json'))
        B = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..', 'diff', 'tests', 'samples', 'json',
                         'sample05', 'sample05B.json'))
        relative_error = '1e-8'
        sys.argv = [file01, A, B, '--rel_tol']
        return A, B, relative_error

    def setUpValidAbsoluteError(self):
        """Test Case: Valid command-line arguments using the absolute error flag where the user specifies the absolute error"""
        file01 = os.path.join('bin', 'jsondiff.py')
        A = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..', 'diff', 'tests', 'samples', 'json',
                         'sample05', 'sample05A.json'))
        B = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..', 'diff', 'tests', 'samples', 'json',
                         'sample05', 'sample05B.json'))
        absolute_error = '1e-9'
        sys.argv = [file01, A, B, '--abs_tol', absolute_error]
        return A, B, absolute_error

    def setUpValidAbsoluteErrorDefault(self):
        """Test Case: Valid command-line arguments using the absolute error flag where the default value is used for the absolute error"""
        file01 = os.path.join('bin', 'jsondiff.py')
        A = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..', 'diff', 'tests', 'samples', 'json',
                         'sample05', 'sample05A.json'))
        B = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..', 'diff', 'tests', 'samples', 'json',
                         'sample05', 'sample05B.json'))
        absolute_error = '1e-10'
        sys.argv = [file01, A, B, '--abs_tol']
        return A, B, absolute_error

    def setUpValidRelativeErrorNoDifference(self):
        """Test Case: Valid command-line arguments using the relative error flag where no differences are expected because the same file is used"""
        file01 = os.path.join('bin', 'jsondiff.py')
        A = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..', 'diff', 'tests', 'samples', 'json',
                         'sample05', 'sample05A.json'))
        relative_error = '1e-8'
        sys.argv = [file01, A, A, '--rel_tol']
        return A, A, relative_error

    def setUpValidAbsoluteErrorNoDifference(self):
        """Test Case: Valid command-line arguments using the absolute error flag where no differences are expected because the same file is used"""
        file01 = os.path.join('bin', 'jsondiff.py')
        A = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..', 'diff', 'tests', 'samples', 'json',
                         'sample05', 'sample05A.json'))
        absolute_error = '1e-10'
        sys.argv = [file01, A, A, '--abs_tol']
        return A, A, absolute_error

    def setUpInvalidPathRelativeError(self):
        """Test Case: Invalid command-line arguments using relative error where the paths for both files are invalid"""
        file01 = os.path.join('bin', 'jsondiff.py')
        A = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..', 'diff', 'tests', 'samples', 'json',
                         'sample01A.json'))
        B = os.path.abspath(os.path.join('json', 'sample01', 'sample01A.json'))
        relative_error = '1e-8'
        sys.argv = [file01, A, B, '--rel_tol']
        return A, B, relative_error

    def setUpInvalidExtensionRelativeError(self):
        """Test Case: Invalid command-line arguments using relative error where the extension of a file is invalid"""
        file01 = os.path.join('bin', 'jsondiff.py')
        A = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..', 'diff', 'tests', 'samples', 'json',
                         'sample01A.json'))
        B = os.path.abspath(os.path.join('diff', 'diff.py'))
        relative_error = '1e-8'
        sys.argv = [file01, A, B, '--rel_tol']
        return A, B, relative_error

    def setUpNoFlags(self):
        """Test Case: Invalid command-line arguments where neither the --rel_tol or --abs_tol flag are used"""
        file01 = os.path.join('bin', 'jsondiff.py')
        A = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..', 'diff', 'tests', 'samples', 'json',
                         'sample01A.json'))
        B = os.path.abspath(os.path.join('json', 'sample01', 'sample01A.json'))
        sys.argv = [file01, A, B]
        return A, B

    def setUpTwoFlags(self):
        """Test Case: Invalid command-line arguments where both the --rel_tol and --abs_tol flags are used"""
        file01 = os.path.join('bin', 'jsondiff.py')
        A = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..', 'diff', 'tests', 'samples', 'json',
                         'sample01', 'sample01A.json'))
        B = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..', 'diff', 'tests', 'samples', 'json',
                         'sample01', 'sample01B.json'))
        sys.argv = [file01, A, B, '--rel_tol', '--abs_tol']
        return A, B

    def setUpSample01(self):
        """Test Case: Valid command-line arguments using the relative error flag and sample01 files"""
        file01 = os.path.join('bin', 'jsondiff.py')
        A = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..', 'diff', 'tests', 'samples', 'json',
                         'sample01', 'sample01A.json'))
        B = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..', 'diff', 'tests', 'samples', 'json',
                         'sample01', 'sample01B.json'))
        relative_error = '1e-8'
        sys.argv = [file01, A, B, '--rel_tol']
        return A, B, relative_error

    def setUpSample02(self):
        """Test Case: Valid command-line arguments using the relative error flag and sample02 files"""
        file01 = os.path.join('bin', 'jsondiff.py')
        A = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..', 'diff', 'tests', 'samples', 'json',
                         'sample02', 'sample02A.json'))
        B = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..', 'diff', 'tests', 'samples', 'json',
                         'sample02', 'sample02B.json'))
        relative_error = '1e-8'
        sys.argv = [file01, A, B, '--rel_tol']
        return A, B, relative_error

    def setUpSample03(self):
        """Test Case: Valid command-line arguments using the relative error flag and sample03 files"""
        file01 = os.path.join('bin', 'jsondiff.py')
        A = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..', 'diff', 'tests', 'samples', 'json',
                         'sample03', 'sample03A.json'))
        B = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..', 'diff', 'tests', 'samples', 'json',
                         'sample03', 'sample03B.json'))
        relative_error = '1e-8'
        sys.argv = [file01, A, B, '--rel_tol']
        return A, B, relative_error

    def setUpSample04(self):
        """Test Case: Valid command-line arguments using the relative error flag and sample04 files"""
        file01 = os.path.join('bin', 'jsondiff.py')
        A = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..', 'diff', 'tests', 'samples', 'json',
                         'sample04', 'sample04A.json'))
        B = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..', 'diff', 'tests', 'samples', 'json',
                         'sample04', 'sample04B.json'))
        relative_error = '1e-8'
        sys.argv = [file01, A, B, '--rel_tol']
        return A, B, relative_error

    def setUpSample05(self):
        """Test Case: Valid command-line arguments using the relative error flag and sample05 files
            Note: Mock files to test various tolerances"""
        file01 = os.path.join('bin', 'jsondiff.py')
        A = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..', 'diff', 'tests', 'samples', 'json',
                         'sample05', 'sample05A.json'))
        B = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..', 'diff', 'tests', 'samples', 'json',
                         'sample05', 'sample05B.json'))
        relative_error = '1e-8'
        sys.argv = [file01, A, B, '--rel_tol']
        return A, B, relative_error

    def testAddArgumentsValidRelativeError(self):
        """Test Case: Valid command-line arguments using the relative error flag where the user specifies the relative error"""
        A, B, relative_error = self.setUpValidRelativeError()
        args = jsondiff.add_arguments()
        self.assertEqual(args.json_files[0], A)
        self.assertEqual(args.json_files[1], B)
        self.assertEqual(args.relative_error, float(relative_error))

    def testAddArgumentsValidRelativeErrorDefault(self):
        """Test Case: Valid command-line arguments using the relative error flag where the default value is used for the relative error"""
        A, B, relative_error = self.setUpValidRelativeErrorDefault()
        args = jsondiff.add_arguments()
        self.assertEqual(args.json_files[0], A)
        self.assertEqual(args.json_files[1], B)
        self.assertEqual(args.relative_error, float(relative_error))

    def testAddArgumentsValidAbsoluteError(self):
        """Test Case: Valid command-line arguments using the absolute error flag where the user specifies the absolute error"""
        A, B, absolute_error = self.setUpValidAbsoluteError()
        args = jsondiff.add_arguments()
        self.assertEqual(args.json_files[0], A)
        self.assertEqual(args.json_files[1], B)
        self.assertEqual(args.absolute_error, float(absolute_error))

    def testAddArgumentsValidAbsoluteErrorDefault(self):
        """Test Case: Valid command-line arguments using the absolute error flag where the default value is used for the absolute error"""
        A, B, absolute_error = self.setUpValidAbsoluteErrorDefault()
        args = jsondiff.add_arguments()
        self.assertEqual(args.json_files[0], A)
        self.assertEqual(args.json_files[1], B)
        self.assertEqual(args.absolute_error, float(absolute_error))

    def testValidateFlagsNoFlags(self):
        """Test Case: Invalid command-line arguments where neither the --rel_tol or --abs_tol flag are used"""
        A, B = self.setUpNoFlags()
        args = jsondiff.add_arguments()
        return_code = jsondiff.validate_flags(args)
        self.assertEqual(return_code, 1)

    def testValidateFlagsNoFlagsRaiseOnError(self):
        """Test Case: Invalid command-line arguments where neither the --rel_tol or --abs_tol flag are used and raises ValueError"""
        A, B = self.setUpNoFlags()
        args = jsondiff.add_arguments()
        with self.assertRaises(ValueError):
            jsondiff.validate_flags(args, raise_on_error=True)

    def testValidateFlagsTwoFlags(self):
        """Test Case: Invalid command-line arguments where both the --rel_tol and --abs_tol flags are used"""
        A, B = self.setUpTwoFlags()
        args = jsondiff.add_arguments()
        return_code = jsondiff.validate_flags(args)
        self.assertEqual(return_code, 1)

    def testValidateFlagsTwoFlagsRaiseOnError(self):
        """Test Case: Invalid command-line arguments where both the --rel_tol and --abs_tol flags are used and raises ValueError"""
        A, B = self.setUpTwoFlags()
        args = jsondiff.add_arguments()
        with self.assertRaises(ValueError):
            jsondiff.validate_flags(args, raise_on_error=True)

    def testValidateFlagsOneFlag(self):
        """Test Case: Valid command-line arguments where either the --rel_tol or --abs_tol flag is used"""
        A, B, relative_error = self.setUpValidRelativeError()
        args = jsondiff.add_arguments()
        return_code = jsondiff.validate_flags(args, raise_on_error=True)
        self.assertEqual(return_code, 0)

    def testMainValidRelativeErrorDifference(self):
        """Test Case: Valid command-line arguments using relative error and different json files"""
        A, B, relative_error = self.setUpValidRelativeError()
        returned = jsondiff.main()
        self.assertEqual(returned, None)

    def testMainValidAbsoluteErrorDifference(self):
        """Test Case: Valid command-line arguments using absolute error and different json files"""
        A, B, absolute_error = self.setUpValidAbsoluteError()
        returned = jsondiff.main()
        self.assertEqual(returned, None)

    def testMainValidRelativeErrorNoDifference(self):
        """Test Case: Valid command-line arguments using relative error and the same json file"""
        A, B, relative_error = self.setUpValidRelativeErrorNoDifference()
        returned = jsondiff.main()
        self.assertEqual(returned, None)

    def testMainValidAbsoluteErrorNoDifference(self):
        """Test Case: Valid command-line arguments using absolute error and the same json file"""
        A, B, absolute_error = self.setUpValidAbsoluteErrorNoDifference()
        returned = jsondiff.main()
        self.assertEqual(returned, None)

    def testMainInvalidPaths(self):
        """Test Case: Invalid command-line arguments where the paths for both files are invalid"""
        A, B, relative_error = self.setUpInvalidPathRelativeError()
        with self.assertRaises(FileNotFoundError):
            jsondiff.main()

    def testMainInvalidExtension(self):
        """Test Case: An invalid extension is provided. Raises TypeError because expect .json extension, .py provided"""
        A, B, relative_error = self.setUpInvalidExtensionRelativeError()
        with self.assertRaises(TypeError):
            jsondiff.main()

    def testMainInvalidFlags(self):
        """Test Case: Invalid command-line arguments where both the --rel_tol and --abs_tol flags are used and raises ValueError"""
        A, B = self.setUpTwoFlags()
        with self.assertRaises(ValueError):
            jsondiff.main()

    def testMainSample01(self):
        """Test Case: Valid command-line arguments using the relative error flag and sample01 files"""
        A, B, relative_error = self.setUpSample01()
        returned = jsondiff.main()
        self.assertEqual(returned, None)

    def testMainSample02(self):
        """Test Case: Valid command-line arguments using the relative error flag and sample02 files"""
        A, B, relative_error = self.setUpSample02()
        returned = jsondiff.main()
        self.assertEqual(returned, None)

    def testMainSample03(self):
        """Test Case: Valid command-line arguments using the relative error flag and sample03 files"""
        A, B, relative_error = self.setUpSample03()
        returned = jsondiff.main()
        self.assertEqual(returned, None)

    def testMainSample04(self):
        """Test Case: Valid command-line arguments using the relative error flag and sample04 files"""
        A, B, relative_error = self.setUpSample04()
        returned = jsondiff.main()
        self.assertEqual(returned, None)

    def testMainSample05(self):
        """Test Case: Valid command-line arguments using the relative error flag and sample05 files"""
        A, B, relative_error = self.setUpSample05()
        returned = jsondiff.main()
        self.assertEqual(returned, None)


if __name__ == '__main__':
    unittest.main(module=__name__)
