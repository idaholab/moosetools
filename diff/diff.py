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
import json
import logging
from deepdiff import DeepDiff

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from diff.moosedeepdiff import MOOSEDeepDiff
import mooseutils


def compare_jsons(json_file01, json_file02, relative_error=None, absolute_error=None):
    """Determine the differences between two json files
        relative_error: the maximum relative tolerance that will be detected as a changed value
        absolute_error: the maximum absolute tolerance that will be detected as a changed value
        Return deep diff object
            e.g. differences: {'values_changed': {'root[0]': {'new_value': 1.0000001, 'old_value': 1.0}}}
            e.g. no differences: {}
        Formatted string of the differences: deep_diff_obj.pretty()
        Note: Must pip install and import deepdiff"""
    log = logging.getLogger(__name__)

    # Validate files
    validate_tolerance(relative_error, absolute_error, raise_on_error=True)
    mooseutils.validate_extension(json_file01, json_file02, extension='.json', raise_on_error=True)
    mooseutils.validate_paths_exist(json_file01, json_file02, raise_on_error=True)

    # Parse jsons
    with open(json_file01) as f:
        json01 = json.load(f)

    with open(json_file02) as f:
        json02 = json.load(f)

    # Determine json differences
    if relative_error is not None:
        log.info('Using relative error = {0}'.format(relative_error))
        json_diff = MOOSEDeepDiff(json01, json02, verbose_level=2, relative_error=relative_error)
    elif absolute_error is not None:
        log.info('Using absolute error = {0}'.format(absolute_error))
        json_diff = MOOSEDeepDiff(json01, json02, verbose_level=2, absolute_error=absolute_error)
    return json_diff


def validate_tolerance(relative_error, absolute_error, raise_on_error=False, log_on_error=True):
    """Validates the that only one tolerance was provided and the datatype of the tolerance is a float
        relative_error: the maximum relative tolerance to validate
        absolute_error: the maximum absolute tolerance to validate
        raise_on_error: raises TypeError if incorrect datatype or ValueError if invalid quantity for tolerance
        log_on_error: reports the error in a log file"""
    return_code = 0
    log = logging.getLogger(__name__)

    # When no tolerance is provided
    if relative_error is None and absolute_error is None:
        return_code += 1
        error = 'No tolerance provided.'
        message = '{0}: {1}'.format('ValueError', error)
        if log_on_error:
            log.error(message)
        if raise_on_error:
            raise ValueError(error)
    # When two tolerances are provided
    elif relative_error is not None and absolute_error is not None:
        return_code += 1
        error = 'One tolerance expected but both relative error and an absolute error were provided.'
        message = '{0}: {1}'.format('ValueError', error)
        if log_on_error:
            log.error(message)
        if raise_on_error:
            raise ValueError(error)
    elif relative_error is not None:
        # Check the datatype of relative error
        if not isinstance(relative_error, float) and not isinstance(relative_error, int):
            return_code += 1

            error = 'Invalid datatype: Require \'{0}\' or \'{1}\' for relative error (e.g. 1e-8), provided \'{2}\''.format(
                type(float()).__name__,
                type(int()).__name__,
                type(relative_error).__name__)
            message = '{0}: {1}'.format('TypeError', error)
            if log_on_error:
                log.error(message)
            if raise_on_error:
                raise TypeError(error)
    elif absolute_error is not None:
        # Check the datatype of absolute error
        if not isinstance(absolute_error, float) and not isinstance(relative_error, int):
            return_code += 1
            error = error = 'Invalid datatype: Require \'{0}\' or \'{1}\' for absolute error (e.g. 1e-10), provided \'{2}\''.format(
                type(float()).__name__,
                type(int()).__name__,
                type(absolute_error).__name__)
            message = '{0}: {1}'.format('TypeError', error)
            if log_on_error:
                log.error(message)
            if raise_on_error:
                raise TypeError(error)
    return return_code
