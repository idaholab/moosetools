#* This file is part of MOOSETOOLS repository
#* https://www.github.com/idaholab/moosetools
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moosetools/blob/main/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html

import sys
if sys.version_info < (3, 6):
    print('"TestHarness" requires python version 3.6 or greater, version {}.{} is being used.' \
          .format(sys.version_info[0], sys.version_info[1]))
    sys.exit(1)

from .TestHarness import TestHarness
from .TestHarness import findDepApps

__all__ = ['TestHarness', 'findDepApps']
