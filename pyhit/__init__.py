#* This file is part of MOOSETOOLS repository
#* https://www.github.com/idaholab/moosetools
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moose/blob/master/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html

import sys
import os
import subprocess

hit_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'contrib', 'hit'))
try:
    sys.path.append(hit_dir)
    import hit
except:
    subprocess.run(['make', 'bindings'], cwd=hit_dir)
    import hit

from hit import TokenType, Token
from .pyhit import Node, load, write, parse, tokenize
