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
import json
import logging
import mooseutils

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
