#* This file is part of MOOSETOOLS repository
#* https://www.github.com/idaholab/moosetools
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moosetools/blob/main/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html

from . import base
from . import controllers
from . import runners
from . import differs
from .discover import discover
from .run import run, fuzzer
from .main import main

import logging

logging.basicConfig()

# Fix python 3.8/3.9 on MacOS due to this https://github.com/python/cpython/pull/13603
# There is some more information here:
#   https://github.com/ansible/ansible/issues/63973#issuecomment-546995228
#
# If we use the default "spawn" I get some strange behavior and the system locks up, with "fork" it
# all works great :shrug:
import multiprocessing

multiprocessing.set_start_method('fork', force=True)
