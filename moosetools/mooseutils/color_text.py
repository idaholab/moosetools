#* This file is part of MOOSETOOLS repository
#* https://www.github.com/idaholab/moosetools
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moosetools/blob/main/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html

import colored


def color_text(text, fg=None, bg=None):
    output = ''
    if fg is not None:
        output += colored.fg(fg)
    if bg is not None:
        output += colored.bg(bg)
    output += text
    if (fg is not None) or (bg is not None):
        output += colored.attr('reset')
    return output
