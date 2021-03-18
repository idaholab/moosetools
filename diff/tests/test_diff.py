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
import diff


class TestDiff(unittest.TestCase):
    def setUpSample05(self):
        """Test Case: Provide the absolute path for Sample05 json files, which are mock files to test various tolerances"""
        A = os.path.abspath(os.path.join(os.path.dirname(__file__), 'samples', 'json', 'sample05', 'sample05A.json'))
        B = os.path.abspath(os.path.join(os.path.dirname(__file__), 'samples', 'json', 'sample05', 'sample05B.json'))
        return A, B

    def testValidateToleranceInvalidRelativeError(self):
        """Test Case: An invalid datatype(invalid:str, valid:float,int) for relative error was provided"""
        relative_error = 'string'
        absolute_error = None
        return_code = diff.validate_tolerance(relative_error=relative_error,
                                              absolute_error=absolute_error)
        self.assertEqual(return_code, 1)

    def testValidateToleranceInvalidRelativeErrorRaiseOnError(self):
        """Test Case: An invalid datatype(invalid:str, valid:float,int) for relative error was provided and raises TypeError"""
        relative_error = 'string'
        absolute_error = None
        with self.assertRaises(TypeError):
            diff.validate_tolerance(relative_error=relative_error,
                                    absolute_error=absolute_error,
                                    raise_on_error=True)

    def testValidateToleranceInvalidAbsoluteError(self):
        """Test Case: An invalid datatype(invalid:str, valid:float,int) for absolute error was provided"""
        relative_error = None
        absolute_error = 'string'
        return_code = diff.validate_tolerance(relative_error=relative_error,
                                              absolute_error=absolute_error)
        self.assertEqual(return_code, 1)

    def testValidateToleranceInvalidAbsoluteErrorRaiseOnError(self):
        """Test Case: An invalid datatype(invalid:str, valid:float,int) for absolute error was provided and raises TypeError"""
        relative_error = None
        absolute_error = 'string'
        with self.assertRaises(TypeError):
            diff.validate_tolerance(relative_error=relative_error,
                                    absolute_error=absolute_error,
                                    raise_on_error=True)

    def testValidateToleranceNoToleranceProvided(self):
        """Test Case: An invalid tolerance since neither relative error or absolute error was provided"""
        relative_error = None
        absolute_error = None
        return_code = diff.validate_tolerance(relative_error=relative_error,
                                              absolute_error=absolute_error)
        self.assertEqual(return_code, 1)

    def testValidateToleranceNoToleranceProvidedRaiseOnError(self):
        """Test Case: An invalid tolerance since neither relative error or absolute error was provided and raises ValueError"""
        relative_error = None
        absolute_error = None
        with self.assertRaises(ValueError):
            diff.validate_tolerance(relative_error=relative_error,
                                    absolute_error=absolute_error,
                                    raise_on_error=True)

    def testValidateToleranceTwoTolerancesProvided(self):
        """Test Case: An invalid tolerance since both relative error or absolute error were provided"""
        relative_error = 1e-8
        absolute_error = 1e-10
        return_code = diff.validate_tolerance(relative_error=relative_error,
                                              absolute_error=absolute_error)
        self.assertEqual(return_code, 1)

    def testValidateToleranceTwoTolerancesProvidedRaiseOnError(self):
        """Test Case: An invalid tolerance since both relative error or absolute error were provided and raises ValueError"""
        relative_error = 1e-8
        absolute_error = 1e-10
        with self.assertRaises(ValueError):
            diff.validate_tolerance(relative_error=relative_error,
                                    absolute_error=absolute_error,
                                    raise_on_error=True)

    def testValidateToleranceValidTolerance01(self):
        """Test Case: A valid tolerance using relative error with a 'float' datatype was provided"""
        relative_error = 1e-8
        absolute_error = None
        return_code = diff.validate_tolerance(relative_error=relative_error,
                                              absolute_error=absolute_error,
                                              raise_on_error=True)
        self.assertEqual(return_code, 0)

    def testValidateToleranceValidTolerance02(self):
        """Test Case: A valid tolerance using relative error with a 'int' datatype was provided"""
        relative_error = 10
        absolute_error = None
        return_code = diff.validate_tolerance(relative_error=relative_error,
                                              absolute_error=absolute_error,
                                              raise_on_error=True)
        self.assertEqual(return_code, 0)

    def testCompareJsonsRelativeErrorDifference(self):
        """Test Case: the two json files are different when using relative error"""
        A = os.path.abspath(os.path.join(os.path.dirname(__file__), 'samples', 'json', 'sample05', 'sample05A.json'))
        B = os.path.abspath(os.path.join(os.path.dirname(__file__), 'samples', 'json', 'sample05', 'sample05B.json'))
        relative_error = 1e-8
        json_diff = diff.compare_jsons(A, B, relative_error=relative_error)
        has_differences = False
        if len(json_diff) != 0:
            has_differences = True
        self.assertEqual(has_differences, True)

    def testCompareJsonsAbsoluteErrorDifference(self):
        """Test Case: the two json files are different when using absolute error"""
        A = os.path.abspath(os.path.join(os.path.dirname(__file__), 'samples', 'json', 'sample05', 'sample05A.json'))
        B = os.path.abspath(os.path.join(os.path.dirname(__file__), 'samples', 'json', 'sample05', 'sample05B.json'))
        absolute_error = 1e-10
        json_diff = diff.compare_jsons(A, B, absolute_error=absolute_error)
        has_differences = False
        if len(json_diff) != 0:
            has_differences = True
        self.assertEqual(has_differences, True)

    def testCompareJsonsRelativeErrorNoDifference(self):
        """Test Case: the two json files are equal when using relative error"""
        A = os.path.abspath(os.path.join(os.path.dirname(__file__), 'samples', 'json', 'sample05', 'sample05A.json'))
        relative_error = 1e-8
        json_diff = diff.compare_jsons(A, A, relative_error=relative_error)
        is_equal = False
        if len(json_diff) == 0:
            is_equal = True
        self.assertEqual(is_equal, True)

    def testCompareJsonsAbsoluteErrorNoDifference(self):
        """Test Case: the two json files are equal when using absolute error"""
        A = os.path.abspath(os.path.join(os.path.dirname(__file__), 'samples', 'json', 'sample05', 'sample05A.json'))
        absolute_error = 1e-10
        json_diff = diff.compare_jsons(A, A, absolute_error=absolute_error)
        is_equal = False
        if len(json_diff) == 0:
            is_equal = True
        self.assertEqual(is_equal, True)

    def testCompareJsonsInvalidPath(self):
        """Test Case: An invalid path to the file and raises FileNotFoundError"""
        A = os.path.abspath(os.path.join(os.path.dirname(__file__), 'samples', 'json', 'sample05A.json'))
        B = os.path.abspath(os.path.join(os.path.dirname(__file__), 'samples', 'json', 'sample05', 'sample05B.json'))
        relative_error = 1e-8
        with self.assertRaises(FileNotFoundError):
            json_diff = diff.compare_jsons(A, B, relative_error=relative_error)

    def testCompareJsonsInvalidExtension(self):
        """Test Case: An invalid extension is provided. Raises TypeError because expect .json extension, .py provided"""
        A = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'bin', 'jsondiff.py'))
        relative_error = 1e-8
        with self.assertRaises(TypeError):
            json_diff = diff.compare_jsons(A, A, relative_error=relative_error)

    def testCompareJsonsInvalidTolerance(self):
        """Test Case: An invalid tolerance since both relative error or absolute error were provided and raises ValueError"""
        A = os.path.abspath(os.path.join(os.path.dirname(__file__), 'samples', 'json', 'sample05', 'sample05A.json'))
        B = os.path.abspath(os.path.join(os.path.dirname(__file__), 'samples', 'json', 'sample05', 'sample05B.json'))
        relative_error = 1e-8
        absolute_error = 1e-10
        with self.assertRaises(ValueError):
            json_diff = diff.compare_jsons(A,
                                           A,
                                           relative_error=relative_error,
                                           absolute_error=absolute_error)

    def testSample05RelativeErrorCheck01(self):
        """Test Case: Sample05 json files with a relative tolerance of 1e-2. Expect 1 difference identified"""
        A, B = self.setUpSample05()
        relative_error = 1e-2
        json_diff = diff.compare_jsons(A, B, relative_error=relative_error)
        count = len(json_diff.pretty().splitlines())
        self.assertEqual(count, 1)

    def testSample05RelativeErrorCheck02(self):
        """Test Case: Sample05 json files with a relative tolerance of 1e-3. Expect 2 difference identified"""
        A, B = self.setUpSample05()
        relative_error = 1e-3
        json_diff = diff.compare_jsons(A, B, relative_error=relative_error)
        count = len(json_diff.pretty().splitlines())
        self.assertEqual(count, 2)

    def testSample05RelativeErrorCheck03(self):
        """Test Case: Sample05 json files with a relative tolerance of 1e-4. Expect 3 difference identified"""
        A, B = self.setUpSample05()
        relative_error = 1e-4
        json_diff = diff.compare_jsons(A, B, relative_error=relative_error)
        count = len(json_diff.pretty().splitlines())
        self.assertEqual(count, 3)

    def testSample05RelativeErrorCheck04(self):
        """Test Case: Sample05 json files with a relative tolerance of 1e-5. Expect 4 difference identified"""
        A, B = self.setUpSample05()
        relative_error = 1e-5
        json_diff = diff.compare_jsons(A, B, relative_error=relative_error)
        count = len(json_diff.pretty().splitlines())
        self.assertEqual(count, 4)

    def testSample05RelativeErrorCheck05(self):
        """Test Case: Sample05 json files with a relative tolerance of 1e-6. Expect 5 difference identified"""
        A, B = self.setUpSample05()
        relative_error = 1e-6
        json_diff = diff.compare_jsons(A, B, relative_error=relative_error)
        count = len(json_diff.pretty().splitlines())
        self.assertEqual(count, 5)

    def testSample05RelativeErrorCheck06(self):
        """Test Case: Sample05 json files with a relative tolerance of 1e-7. Expect 6 difference identified"""
        A, B = self.setUpSample05()
        relative_error = 1e-7
        json_diff = diff.compare_jsons(A, B, relative_error=relative_error)
        count = len(json_diff.pretty().splitlines())
        self.assertEqual(count, 6)

    def testSample05RelativeErrorCheck07(self):
        """Test Case: Sample05 json files with a relative tolerance of 1e-8. Expect 7 difference identified"""
        A, B = self.setUpSample05()
        relative_error = 1e-8
        json_diff = diff.compare_jsons(A, B, relative_error=relative_error)
        count = len(json_diff.pretty().splitlines())
        self.assertEqual(count, 7)

    def testSample05RelativeErrorCheck08(self):
        """Test Case: Sample05 json files with a relative tolerance of 1e-9. Expect 8 difference identified"""
        A, B = self.setUpSample05()
        relative_error = 1e-9
        json_diff = diff.compare_jsons(A, B, relative_error=relative_error)
        count = len(json_diff.pretty().splitlines())
        self.assertEqual(count, 8)

    def testSample05RelativeErrorCheck09(self):
        """Test Case: Sample05 json files with a relative tolerance of 1e-10. Expect 9 difference identified"""
        A, B = self.setUpSample05()
        relative_error = 1e-10
        json_diff = diff.compare_jsons(A, B, relative_error=relative_error)
        count = len(json_diff.pretty().splitlines())
        self.assertEqual(count, 9)

    def testSample05AbsoluteErrorCheck01(self):
        """Test Case: Sample05 json files with an absolute tolerance of 1e-2. Expect a difference of 0 or greater because of floating point subtraction"""
        A, B = self.setUpSample05()
        absolute_error = 1e-2
        json_diff = diff.compare_jsons(A, B, absolute_error=absolute_error)
        count = len(json_diff.pretty().splitlines())
        self.assertTrue(count >= 0)

    def testSample05AbsoluteErrorCheck02(self):
        """Test Case: Sample05 json files with an absolute tolerance of 1e-3. Expect a difference of 1 or greater because of floating point subtraction"""
        A, B = self.setUpSample05()
        absolute_error = 1e-3
        json_diff = diff.compare_jsons(A, B, absolute_error=absolute_error)
        count = len(json_diff.pretty().splitlines())
        self.assertTrue(count >= 1)

    def testSample05AbsoluteErrorCheck03(self):
        """Test Case: Sample05 json files with an absolute tolerance of 1e-4. Expect a difference of 2 or greater because of floating point subtraction"""
        A, B = self.setUpSample05()
        absolute_error = 1e-4
        json_diff = diff.compare_jsons(A, B, absolute_error=absolute_error)
        count = len(json_diff.pretty().splitlines())
        self.assertTrue(count >= 2)

    def testSample05AbsoluteErrorCheck04(self):
        """Test Case: Sample05 json files with an absolute tolerance of 1e-5. Expect a difference of 3 or greater because of floating point subtraction"""
        A, B = self.setUpSample05()
        absolute_error = 1e-5
        json_diff = diff.compare_jsons(A, B, absolute_error=absolute_error)
        count = len(json_diff.pretty().splitlines())
        self.assertTrue(count >= 3)

    def testSample05AbsoluteErrorCheck05(self):
        """Test Case: Sample05 json files with an absolute tolerance of 1e-6. Expect a difference of 4 or greater because of floating point subtraction"""
        A, B = self.setUpSample05()
        absolute_error = 1e-6
        json_diff = diff.compare_jsons(A, B, absolute_error=absolute_error)
        count = len(json_diff.pretty().splitlines())
        self.assertTrue(count >= 4)

    def testSample05AbsoluteErrorCheck06(self):
        """Test Case: Sample05 json files with an absolute tolerance of 1e-7. Expect a difference of 5 or greater because of floating point subtraction"""
        A, B = self.setUpSample05()
        absolute_error = 1e-7
        json_diff = diff.compare_jsons(A, B, absolute_error=absolute_error)
        count = len(json_diff.pretty().splitlines())
        self.assertTrue(count >= 5)

    def testSample05AbsoluteErrorCheck07(self):
        """Test Case: Sample05 json files with an absolute tolerance of 1e-8. Expect a difference of 6 or greater because of floating point subtraction"""
        A, B = self.setUpSample05()
        absolute_error = 1e-8
        json_diff = diff.compare_jsons(A, B, absolute_error=absolute_error)
        count = len(json_diff.pretty().splitlines())
        self.assertTrue(count >= 6)

    def testSample05AbsoluteErrorCheck08(self):
        """Test Case: Sample05 json files with an absolute tolerance of 1e-9. Expect a difference of 7 or greater because of floating point subtraction"""
        A, B = self.setUpSample05()
        absolute_error = 1e-9
        json_diff = diff.compare_jsons(A, B, absolute_error=absolute_error)
        count = len(json_diff.pretty().splitlines())
        self.assertTrue(count >= 7)

    def testSample05AbsoluteErrorCheck09(self):
        """Test Case: Sample05 json files with an absolute tolerance of 1e-10. Expect a difference of 8 or greater because of floating point subtraction"""
        A, B = self.setUpSample05()
        absolute_error = 1e-10
        json_diff = diff.compare_jsons(A, B, absolute_error=absolute_error)
        count = len(json_diff.pretty().splitlines())
        self.assertTrue(count >= 8)

    def testSample05AbsoluteErrorCheck10(self):
        """Test Case: Sample05 json files with an absolute tolerance of 1e-11. Expect a difference of 9 or greater because of floating point subtraction"""
        A, B = self.setUpSample05()
        absolute_error = 1e-11
        json_diff = diff.compare_jsons(A, B, absolute_error=absolute_error)
        count = len(json_diff.pretty().splitlines())
        self.assertTrue(count >= 9)


if __name__ == '__main__':
    unittest.main(module=__name__)
