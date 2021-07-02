#* This file is part of MOOSETOOLS repository
#* https://www.github.com/idaholab/moosetools
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moosetools/blob/main/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html

import re
from moosetools.moosetest.base import Controller


class NameController(Controller):
    """
    A controller to dictate if an object should run based on the name.
    """
    AUTO_BUILD = True

    @staticmethod
    def validParams():
        params = Controller.validParams()
        params.add('remove_if_text_in_name',
                   vtype=str,
                   doc="Remove test if the supplied text is in the object name.")
        params.add('remove_if_text_not_in_name',
                   vtype=str,
                   doc="Remove test if the supplied text is not in the object name.")
        params.add('remove_if_re_match_name',
                   vtype=str,
                   doc="Remove test if the supplied regular expression matches the object name.")
        params.add(
            'remove_if_re_not_match_name',
            vtype=str,
            doc="Remove test if the supplied regular expression does not match the object name.")
        params.add('re_flags',
                   vtype=str,
                   array=True,
                   default=('MULTILINE', 'DOTALL', 'UNICODE'),
                   allow=('MULTILINE', 'DOTALL', 'UNICODE', 'IGNORECASE', 'VERBOSE', 'LOCALE',
                          'DEBUG', 'ASCII'),
                   doc="The names of the flags to pass to regular expression `match` function.")
        return params

    @staticmethod
    def validObjectParams():
        """
        The "prefix" parameter for this object is not set, so this method is not used.

        See the `make_runner` and `make_differ` in the Runner.py and Differ.py modules.
        """
        return None

    def execute(self, obj, params):

        # TEXT
        text_in = self.getParam('remove_if_text_in_name')
        if (text_in is not None) and (text_in in obj.name()):
            self.debug(
                "The text in 'remove_if_text_in_name', '{}', was located in the object name '{}'",
                text_in, obj.name())
            self.remove('remove_if_text_in_name')

        text_not_in = self.getParam('remove_if_text_not_in_name')
        if (text_not_in is not None) and (text_not_in not in obj.name()):
            self.debug(
                "The text in 'remove_if_text_not_in_name', '{}', was not located in the object name '{}'",
                text_in, obj.name())
            self.remove('remove_if_text_not_in_name')

        # RE
        flags = 0
        for flag in self.getParam('re_flags'):
            flags |= eval(f're.{flag}')

        re_match = self.getParam('remove_if_re_match_name')
        if re_match is not None:
            match = re.search(re_match, obj.name(), flags=flags)
            if match:
                self.debug(
                    "The regular expression of 'remove_if_re_match_name', '{}', matches the object name '{}'",
                    text_in, obj.name())
                self.remove('remove_if_re_match_name')

        re_not_match = self.getParam('remove_if_re_not_match_name')
        if re_not_match is not None:
            match = re.search(re_not_match, obj.name(), flags=flags)
            if not match:
                self.debug(
                    "The regular expression of 'remove_if_re_not_match_name', '{}', does not match the object name '{}'",
                    text_in, obj.name())
                self.remove('remove_if_re_not_match_name')
