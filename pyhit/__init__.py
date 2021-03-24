#* This file is part of MOOSETOOLS repository
#* https://www.github.com/idaholab/moosetools
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moosetools/blob/main/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html

import sys
import os
import logging
import subprocess

hit_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'contrib', 'hit'))
sys.path.append(hit_dir)
try:
    import hit
except ImportError:
    log = logging.getLogger(__name__)
    log.exception("Failed to import python bindings for HIT library, attempting to build with `make bindings`")
    subprocess.run(['make', 'bindings'], cwd=hit_dir)

try:
    from hit import TokenType, Token
    from .pyhit import Node, load, write, parse, tokenize
except ImportError:
    log = logging.getLogger(__name__)
    log.exception("Failed to import python bindings for HIT library.")
