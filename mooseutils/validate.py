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
import errno
import logging


def validate_extension(*args, extension, raise_on_error=False, log_on_error=True):
    """Validates that the file has the provided extension
        *args: the file(s) to validate
        extension: the expected extension
        raise_on_error: raises a TypeError if incorrect extension
        log_on_error: reports the error in a log file"""
    return_code = 0
    log = logging.getLogger(__name__)

    for file in args:
        base, ext = os.path.splitext(file)
        if ext.lower() != extension.lower():
            return_code += 1
            error = 'Invalid extension: \'{0}\'. Provide a file with {1} extension'.format(
                file, extension)
            message = '{0}: {1}'.format('TypeError', error)
            if log_on_error:
                log.error(message)
            if raise_on_error:
                raise TypeError(error)
    return return_code


def validate_paths_exist(*args, raise_on_error=False, log_on_error=True):
    """Check if the files or directories exist in the system path
        *args: the files/directories to validate
        raise_on_error: raises a FileNotFoundError if the path does not exist
        log_on_error: reports the error in a log file"""
    return_code = 0
    log = logging.getLogger(__name__)

    for path in args:
        # Check if the provided path exists in the system path
        if not os.path.exists(path):
            return_code += 1
            error = FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), path)
            message = '{0}: {1}'.format('FileNotFoundError', error)
            if log_on_error:
                log.error(message)
            if raise_on_error:
                raise error
    return return_code
