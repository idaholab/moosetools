#* This file is part of MOOSETOOLS repository
#* https://www.github.com/idaholab/moosetools
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moose/blob/master/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html
"""
A package for building tree structures. This package is designed as a faster alternative to the
anytree package, although it is not a direct replacement.
"""
from .Node import Node
from .search import findall, find, iterate, IterMethod
