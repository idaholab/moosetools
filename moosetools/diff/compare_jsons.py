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

from moosetools import mooseutils
from .validate_tolerance import validate_tolerance
from .MooseDeepDiff import MooseDeepDiff


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
    #validate_tolerance(relative_error, absolute_error, raise_on_error=True)
    #mooseutils.validate_extension(json_file01, json_file02, extension='.json', raise_on_error=True)
    mooseutils.validate_paths_exist(json_file01, json_file02, raise_on_error=True)

    # Parse jsons
    with open(json_file01) as f:
        json01 = json.load(f)

    with open(json_file02) as f:
        json02 = json.load(f)

    # Determine json differences
    if relative_error is not None:
        log.info('Using relative error = {0}'.format(relative_error))
        json_diff = MooseDeepDiff(json01, json02, verbose_level=2, relative_error=relative_error)
    elif absolute_error is not None:
        log.info('Using absolute error = {0}'.format(absolute_error))
        json_diff = MooseDeepDiff(json01, json02, verbose_level=2, absolute_error=absolute_error)
    return json_diff
