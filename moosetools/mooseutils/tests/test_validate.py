#!/usr/bin/env python3
#* This file is part of MOOSETOOLS repository
#* https://www.github.com/idaholab/moosetools
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moosetools/blob/main/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html

import os
import sys
import unittest

from moosetools.mooseutils.validate import validate_extension, validate_paths_exist


class TestValidate(unittest.TestCase):
    def testValidateExtensionInvalidExtension01RaiseOnError(self):
        """Test Case: An invalid extension is provided. Raise TypeError because expect .txt extension, .py provided"""
        A = os.path.abspath(os.path.join('bin', 'jsondiff.py'))
        with self.assertRaises(TypeError):
            validate_extension(A, extension='.txt', raise_on_error=True)

    def testValidateExtensionValidExtension01(self):
        """Test Case: A valid .py extension is provided"""
        A = os.path.abspath(os.path.join('bin', 'jsondiff.py'))
        return_code = validate_extension(A, extension='.py', raise_on_error=True)
        self.assertEqual(return_code, 0)

    def testValidateExtensionInvalidExtension02RaiseOnError(self):
        """Test Case: An invalid extension is provided. Raise TypeError because expect .json, .py provided"""
        A = os.path.abspath(os.path.join('bin', 'jsondiff.py'))
        with self.assertRaises(TypeError):
            validate_extension(A, extension='.json', raise_on_error=True)

    def testValidateExtensionValidExtension02(self):
        """Test Case: A valid .json extension is provided"""
        A = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..', 'diff', 'tests', 'samples', 'json',
                         'sample05', 'sample05A.json'))
        return_code = validate_extension(A, extension='.json', raise_on_error=True)
        self.assertEqual(return_code, 0)

    def testValidateExtensionInvalidCapitalizeExtension01RaiseOnError(self):
        """Test Case: An invalid extension is provided. Raise TypeError because expect capitalize or lowercase .json, .py provided"""
        A = os.path.abspath(os.path.join('bin', 'jsondiff.py'))
        with self.assertRaises(TypeError):
            validate_extension(A, extension='.JSON', raise_on_error=True)

    def testValidateExtensionInvalidCapitalizeExtension02RaiseOnError(self):
        """Test Case: An invalid extension is provided. Raise TypeError because expect .json, capitalize .py provided"""
        A = os.path.abspath(os.path.join('bin', 'jsondiff.PY'))
        with self.assertRaises(TypeError):
            validate_extension(A, extension='.json', raise_on_error=True)

    def testValidateExtensionValidCapitalizeExtension01(self):
        """Test Case: A valid .json extension is provided whether the extension is capitalize or not"""
        A = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..', 'diff', 'tests', 'samples', 'json',
                         'sample05', 'sample05A.json'))
        return_code = validate_extension(A, extension='.JSON', raise_on_error=True)
        self.assertEqual(return_code, 0)

    def testValidateExtensionValidCapitalizeExtension02(self):
        """Test Case: A valid .json extension is provided whether the file path containing the extension is capitalize or not"""
        A = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..', 'diff', 'tests', 'samples', 'json',
                         'sample05', 'sample05A.JSON'))
        return_code = validate_extension(A, extension='.json', raise_on_error=True)
        self.assertEqual(return_code, 0)

    def testValidateExtensionInvalidMultipleExtensionsRaiseOnError(self):
        """Test Case: Invalid extensions are provided when using multiple files. Raise TypeError because expect .json, .py provided"""
        A = os.path.abspath(os.path.join('bin', 'jsondiff.py'))
        B = os.path.abspath(os.path.join('diff', 'diff.py'))
        with self.assertRaises(TypeError):
            validate_extension(A, B, extension='.json', raise_on_error=True)

    def testValidateExtensionValidMultipleExtensionsRaiseOnError(self):
        """Test Case: Valid .json extensions are provided when using multiple files."""
        A = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..', 'diff', 'tests', 'samples', 'json',
                         'sample05', 'sample05A.json'))
        B = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..', 'diff', 'tests', 'samples', 'json',
                         'sample05', 'sample05B.json'))
        return_code = validate_extension(A, B, extension='.json', raise_on_error=True)
        self.assertEqual(return_code, 0)

    def testValidateExtensionInvalidExtensionNoRaiseOnError(self):
        """Test Case: An invalid extension is provided. Returns a non-zero return code (raise_on_error=False) because expect .py, .json provided."""
        A = os.path.abspath(os.path.join('bin', 'jsondiff.py'))
        return_code = validate_extension(A, extension='.json')
        self.assertEqual(return_code, 1)

    def testValidateExtensionInvalidMultipleExtensionsNoRaiseOnError(self):
        """Test Case: Invalid extensions are provided when using multiple files. Returns a non-zero return code (raise_on_error=False) because expect .txt, .json provided."""
        A = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..', 'diff', 'tests', 'samples', 'json',
                         'sample05', 'sample05A.json'))
        B = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..', 'diff', 'tests', 'samples', 'json',
                         'sample05', 'sample05B.json'))
        return_code = validate_extension(A, B, extension='.txt')
        self.assertEqual(return_code, 2)

    def testValidatePathsExistInvalidFilePathRaiseOnError(self):
        """Test Case: An invalid file path is provided and raises FileNotFoundError."""
        A = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..', 'diff', 'tests', 'samples', 'json',
                         'sample05A.json'))
        with self.assertRaises(FileNotFoundError):
            validate_paths_exist(A, raise_on_error=True)

    def testValidatePathsExistInvalidDirectoryPathRaiseOnError(self):
        """Test Case: An invalid directory path is provided and raises FileNotFoundError."""
        A = os.path.abspath(os.path.join('test_diff', 'sample_json'))
        with self.assertRaises(FileNotFoundError):
            validate_paths_exist(A, raise_on_error=True)

    def testValidatePathsExistValidFilePath(self):
        """Test Case: A valid file path is provided."""
        A = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..', 'diff', 'tests', 'samples', 'json',
                         'sample05', 'sample05A.json'))
        return_code = validate_paths_exist(A, raise_on_error=True)
        self.assertEqual(return_code, 0)

    def testValidatePathsExistValidDirectoryPath(self):
        """Test Case: A valid directory path is provided."""
        A = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..', 'diff', 'tests', 'samples', 'json',
                         'sample05'))
        return_code = validate_paths_exist(A, raise_on_error=True)
        self.assertEqual(return_code, 0)

    def testValidatePathsExistInvalidMultipleFilePathsRaiseOnError(self):
        """Test Case: Invalid file paths are provided using multiple files and raises FileNotFoundError."""
        A = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..', 'diff', 'tests', 'samples', 'json',
                         'sample05A.json'))
        B = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..', 'diff', 'tests', 'samples', 'json',
                         'sample05B.json'))
        with self.assertRaises(FileNotFoundError):
            validate_paths_exist(A, B, raise_on_error=True)

    def testValidatePathsExistInvalidMultipleDirectoryPathsRaiseOnError(self):
        """Test Case: Invalid directory paths are provided using multiple directories and raises FileNotFoundError."""
        A = os.path.abspath(os.path.join('test_diff', 'sample_json'))
        B = os.path.abspath(os.path.join('test_diff'))
        with self.assertRaises(FileNotFoundError):
            validate_paths_exist(A, B, raise_on_error=True)

    def testValidatePathsExistValidMultipleFilePaths(self):
        """Test Case: Valid file paths are provided using multiple files."""
        A = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..', 'diff', 'tests', 'samples', 'json',
                         'sample05', 'sample05A.json'))
        B = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..', 'diff', 'tests', 'samples', 'json',
                         'sample05', 'sample05B.json'))
        return_code = validate_paths_exist(A, B, raise_on_error=True)
        self.assertEqual(return_code, 0)

    def testValidatePathsExistValidMultipleDirectoryPaths(self):
        """Test Case: Valid directory paths are provided using multiple files."""
        A = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..', 'diff', 'tests', 'samples', 'json',
                         'sample05'))
        B = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..', 'diff', 'tests', 'samples', 'json'))
        return_code = validate_paths_exist(A, B, raise_on_error=True)
        self.assertEqual(return_code, 0)

    def testValidatePathsExistInvalidFilePathNoRaiseOnError(self):
        """Test Case: An invalid file path is provided. Returns a non-zero return code (raise_on_error=False)."""
        A = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..', 'diff', 'tests', 'samples', 'json',
                         'sample05A.json'))
        return_code = validate_paths_exist(A)
        self.assertEqual(return_code, 1)

    def testValidatePathsExistInvalidDirectoryPathNoRaiseOnError(self):
        """Test Case: An invalid directory path is provided. Returns a non-zero return code (raise_on_error=False)."""
        A = os.path.abspath(os.path.join('test_diff', 'sample_json'))
        return_code = validate_paths_exist(A)
        self.assertEqual(return_code, 1)

    def testValidatePathsExistInvalidMultipleFilePathsNoRaiseOnError(self):
        """Test Case: Invalid file paths are provided using multiple files. Returns a non-zero return code (raise_on_error=False)."""
        A = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..', 'diff', 'tests', 'samples', 'json',
                         'sample05A.json'))
        B = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..', 'diff', 'tests', 'samples', 'json',
                         'sample05B.json'))
        return_code = validate_paths_exist(A, B)
        self.assertEqual(return_code, 2)

    def testValidatePathsExistInvalidMultipleDirectoryPathsNoRaiseOnError(self):
        """Test Case: Invalid directory paths are provided using multiple files. Returns a non-zero return code (raise_on_error=False)."""
        A = os.path.abspath(os.path.join('test_diff', 'sample_json'))
        B = os.path.abspath(os.path.join('test_diff'))
        return_code = validate_paths_exist(A, B)
        self.assertEqual(return_code, 2)


if __name__ == '__main__':
    unittest.main(module=__name__)
