#!/usr/bin/env python3
#* This file is part of MOOSETOOLS repository
#* https://www.github.com/idaholab/moosetools
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moosetools/blob/main/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html

import mms

fs, ss = mms.evaluate('-div(grad(u))', 'sin(2*pi*x)*sin(2*pi*y)')
mms.print_fparser(fs)

mms.print_hit(fs, 'force')
mms.print_hit(ss, 'exact')

ft, st = mms.evaluate('diff(u,t) - div(grad(u))', 't**3*x*y')
mms.print_fparser(ft)

mms.print_hit(ft, 'force')
mms.print_hit(st, 'exact')
