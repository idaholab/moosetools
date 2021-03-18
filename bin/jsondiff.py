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
import argparse
import deepdiff
import logging

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import diff
import mooseutils

# Configure logging to overwrite the log file for each run, add option: filemode='w'
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s',
                    datefmt='%Y/%m/%d %H:%M:%S')


def add_arguments():
    """Returns the arguments provided by the user and parsed by the Argument Parser"""
    parser = argparse.ArgumentParser(
        description='Provide two json files (.json) to check for differences', add_help=False)
    options = parser.add_argument_group(title='Options')
    options.add_argument('json_files',
                         metavar='<json_file, json_file>',
                         help='Specify two json files',
                         nargs=2)
    # Note: nargs='?' and const=value is for 0 or 1 arguments supplied. If 0 arguments provided, the const value will be used
    options.add_argument('--rel_tol',
                         metavar='<relative_error>',
                         dest='relative_error',
                         help='Specify the maximum relative error (default 1e-8)',
                         type=float,
                         nargs='?',
                         const=1e-8,
                         default=None)
    options.add_argument('--abs_tol',
                         metavar='<absolute_error>',
                         dest='absolute_error',
                         help='Specify the maximum absolute error (default 1e-10)',
                         type=float,
                         nargs='?',
                         const=1e-10,
                         default=None)
    options.add_argument('-h', '--help', action='help', help='Displays CLI usage statement')
    args, unknown = parser.parse_known_args()
    return args


def validate_flags(args, raise_on_error=False, log_on_error=True):
    """Validate that only one flag was passed via the command-line interface
        args: arguments provided by the user
        raise_on_error: raises a ValueError if invalid quantity of tolerance flags
        log_on_error: reports the error in a log file"""
    return_code = 0
    log = logging.getLogger(__name__)

    # When no flags are provided
    if args.relative_error is None and args.absolute_error is None:
        return_code += 1
        help = 'Use "-h" or "--help" for more information.'
        error = 'No flag provided.'
        message = '{0}: {1}'.format('ValueError', error)
        value_error = '{0} {1}'.format(error, help)
        if log_on_error:
            log.error(message)
        if raise_on_error:
            raise ValueError(value_error)
    # When two flags are provided
    elif args.relative_error is not None and args.absolute_error is not None:
        return_code += 1
        help = 'Use "-h" or "--help" for more information.'
        error = 'One flag expected but two flags were provided.'
        message = '{0}: {1}'.format('ValueError', error)
        value_error = '{0} {1}'.format(error, help)
        if log_on_error:
            log.error(message)
        if raise_on_error:
            raise ValueError(value_error)
    return return_code


def main():
    # Create command-line arguments
    args = add_arguments()

    # Validation of command-line arguments
    mooseutils.validate_extension(args.json_files[0],
                                  args.json_files[1],
                                  extension='.json',
                                  raise_on_error=True)
    mooseutils.validate_paths_exist(args.json_files[0], args.json_files[1], raise_on_error=True)
    validate_flags(args, raise_on_error=True)

    # Compare jsons
    json_diff = diff.compare_jsons(args.json_files[0],
                                   args.json_files[1],
                                   relative_error=args.relative_error,
                                   absolute_error=args.absolute_error)

    differences = ''

    # When no difference are found
    if len(json_diff) == 0:
        differences += 'Differences: {0}\r\n'.format(len(json_diff))
        if args.relative_error is not None:
            differences += 'Relative error: {0}'.format(args.relative_error)
        elif args.absolute_error is not None:
            differences += 'Absolute error: {0}'.format(args.absolute_error)

    # When differences are found
    else:
        count = (len(json_diff.pretty().splitlines()))
        differences += 'Differences: {0}\r\n'.format(count)
        if args.relative_error is not None:
            differences += 'Relative error: {0}\r\n'.format(args.relative_error)
        elif args.absolute_error is not None:
            differences += 'Absolute error: {0}\r\n'.format(args.absolute_error)
        differences += json_diff.pretty()
    print(differences)


if __name__ == '__main__':
    sys.exit(main())
