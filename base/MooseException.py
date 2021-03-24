#* This file is part of MOOSETOOLS repository
#* https://www.github.com/idaholab/moosetools
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moosetools/blob/main/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html


class MooseException(Exception):
    """
    General exception.
    """
    def __init__(self, message, *args, **kwargs):
        self.__message = message.format(*args, **kwargs)
        Exception.__init__(self, self.__message)

    @property
    def message(self):
        """Return the message supplied to the constructor."""
        return self.__message
