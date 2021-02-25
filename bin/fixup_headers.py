#!/usr/bin/env python3
#* This file is part of MOOSETOOLS repository
#* https://www.github.com/idaholab/moosetools
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moose/blob/master/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html

import os
import sys
import string
import re
import shutil
import subprocess
import argparse


def get_options():
    parser = argparse.ArgumentParser(description='Check/update headers')
    parser.add_argument("-u", "--update", action="store_true")
    parser.add_argument("-f", "--force", action="store_true")
    parser.add_argument('--cpp-header-file',
                        default=os.path.join(os.path.dirname(__file__), '.cpp-header.txt'))
    parser.add_argument('--python-header-file',
                        default=os.path.join(os.path.dirname(__file__), '.python-header.txt'))
    parser.add_argument('--exclude',
                        default=['contrib'],
                        nargs='*',
                        help="List of files or directories to exclude")
    return parser.parse_args()


def _git_ls_files(exclude=None):
    """Helper for mocking in tests"""
    files = subprocess.check_output(['git', 'ls-files'], encoding='utf-8').split('\n')
    if exclude is not None:
        files = [f for f in files if not any([f.startswith(e) for e in exclude])]
    return files


def main():
    retcode = 0
    opt = get_options()
    for filename in _git_ls_files(opt.exclude):
        if filename.endswith('.py'):
            retcode += check_and_update_python(filename, opt.python_header_file, opt.update,
                                               opt.force)
        elif filename.endswith('.C') or filename.endswith('.h'):
            retcode += check_and_update_cpp(filename, opt.cpp_header_file, opt.update, opt.force)
    return retcode > 0


def check_and_update_cpp(filename, header_file, update=False, force=False):
    retcode = 0

    # Don't update soft links
    if os.path.islink(filename):
        return

    f = open(filename)
    text = f.read()
    f.close()

    with open(header_file, 'r') as fid:
        header = fid.read()

    # Check (exact match only)
    if (text.find(header) == -1 or force):
        retcode = 1
        # print the first 10 lines or so of the file
        if update == False:  # Report only
            print(filename + ' does not contain an up-to-date header')
        else:
            # Make sure any previous C-style header version is removed
            text = re.sub(r'^/\*+/$.*^/\*+/$', '', text, flags=re.S | re.M)

            # Make sure that any previous C++-style header (with extra character)
            # is also removed.
            text = re.sub(r'(?:^//\*.*\n)*', '', text, flags=re.M)

            # Now cleanup extra blank lines
            text = re.sub(r'\A(^\s*\n)', '', text)

            suffix = os.path.splitext(filename)
            if suffix[-1] == '.h':
                text = re.sub(r'^#ifndef\s*\S+_H_?\s*\n#define.*\n', '', text, flags=re.M)
                text = re.sub(r'^#endif.*\n[\s]*\Z', '', text, flags=re.M)

            # Update
            f = open(filename + '~tmp', 'w')
            f.write(header + '\n')

            if suffix[-1] == '.h':
                if not re.search(r'#pragma once', text):
                    f.write("#pragma once\n")

            f.write(text)
            f.close()
            os.rename(filename + '~tmp', filename)

    return retcode


def check_and_update_python(filename, header_file, update=False, force=False):
    retcode = 0

    f = open(filename)
    text = f.read()
    f.close()

    with open(header_file, 'r') as fid:
        header = fid.read()

    # Check (exact match only)
    if (text.find(header) == -1 or force):
        retcode = 1
        # print the first 10 lines or so of the file
        if update == False:  # Report only
            print(filename + ' does not contain an up-to-date header')
        else:
            # Save off the shebang line if it exists
            m = re.match(r'#!.*\n', text)
            shebang = ''
            if m:
                shebang = m.group(0)
                text = re.sub(r'^.*\n', '', text)

            # Save off any pytlint disable directives
            m = re.match(r'\A#pylint:\s+disable.*\n', text)
            pylint_disable = ''
            if m:
                pylint_disable = m.group(0)
                text = re.sub(r'^.*\n', '', text)

            pylint_enable = False
            if re.search(r'#pylint: enable=missing-docstring', text) != None:
                pylint_enable = True

            # Make sure any previous box-style header version is removed
            text = re.sub(r'\A(?:#.*#\n)*', '', text)

            # Make sure any previous version of the new header is removed
            text = re.sub(r'^#\*.*\n', '', text, flags=re.M)

            # Discard any pylint missing-docstring commands
            text = re.sub(r'\A#pylint:.*missing-docstring.*\n', '', text)

            # Now cleanup extra blank lines at the beginning of the file
            text = re.sub(r'\A(^\s*\n)', '', text)

            # Update
            f = open(filename + '~tmp', 'w')

            f.write(shebang)
            f.write(pylint_disable)
            f.write(header)

            if len(text) != 0:
                f.write('\n' + text)

            f.close()

            shutil.copystat(filename, filename + '~tmp')
            os.rename(filename + '~tmp', filename)

    return retcode


if __name__ == '__main__':
    sys.exit(main())
